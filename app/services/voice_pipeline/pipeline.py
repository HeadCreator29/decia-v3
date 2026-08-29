# pipeline.py - Voice Pipeline Orchestrator
# Integrates VAD -> STT -> Intent -> LLM -> TTS with barge-in support

import asyncio
import time
import re
from typing import Optional, Callable, Awaitable, AsyncIterator
from dataclasses import dataclass, field
from enum import Enum

from .vad_processor import VADProcessor, VADResult
from .stt_processor import STTProcessor, STTResult
from .tts_processor import TTSProcessor, TTSChunk
from .audio_input import AudioInput
from .audio_output import AudioOutput
from .config import PipelineConfig, load_config

from brain.intent_layer import IntentLayer
from brain.intent_types import ClassifyResult
from brain.core import think


class PipelineState(Enum):
    """Pipeline states."""
    IDLE = "idle"
    LISTENING = "listening"
    CAPTURING = "capturing"
    PROCESSING = "processing"
    THINKING = "thinking"
    SPEAKING = "speaking"
    INTERRUPTED = "interrupted"


@dataclass
class PipelineMetrics:
    """Pipeline performance metrics."""
    total_turns: int = 0
    total_latency_ms: float = 0.0
    vad_latency_ms: float = 0.0
    stt_latency_ms: float = 0.0
    intent_latency_ms: float = 0.0
    llm_latency_ms: float = 0.0
    tts_latency_ms: float = 0.0
    barge_in_count: int = 0
    fallback_count: int = 0
    buffer_underruns: int = 0
    errors: int = 0


class VoicePipeline:
    """
    Complete voice conversation pipeline.
    
    Orchestrates: VAD -> STT -> Intent Classification -> LLM -> TTS
    With barge-in support for natural conversation.
    """
    
    def __init__(
        self,
        config: Optional[PipelineConfig] = None,
        intent_layer: Optional[IntentLayer] = None,
        llm_client: Optional[Callable[[str], Awaitable[str]]] = None,
    ):
        """
        Initialize voice pipeline.
        
        Args:
            config: Pipeline configuration (loads from env if not provided)
            intent_layer: IntentLayer instance (creates default if not provided)
            llm_client: Async function for LLM calls (uses brain.core.think if not provided)
        """
        self.config = config or load_config()
        self._intent_layer = intent_layer or IntentLayer()
        self._llm_client = llm_client or self._default_llm
        
        # Components
        self._vad = VADProcessor(
            threshold=self.config.vad.threshold,
            min_speech_ms=self.config.vad.min_speech_ms,
            min_silence_ms=self.config.vad.min_silence_ms,
            model_path=self.config.vad.model_path,
            sample_rate=self.config.audio.in_sample_rate,
            fallback_enabled=self.config.vad.fallback_enabled,
        )
        
        self._stt = STTProcessor(
            model_size=self.config.stt.model_size,
            language=self.config.stt.language,
            beam_size=self.config.stt.beam_size,
            compute_type=self.config.stt.compute_type,
        )
        
        self._tts = TTSProcessor(
            voice_id=self.config.tts.voice_id,
            speed=self.config.tts.speed,
            sample_rate=self.config.audio.out_sample_rate,
            model_dir=self.config.tts.voice_id.rsplit("-", 2)[0] if "-" in self.config.tts.voice_id else "models",
            fallback_enabled=self.config.tts.fallback_enabled,
        )
        
        self._audio_in = AudioInput(
            device_id=self.config.audio.in_device,
            sample_rate=self.config.audio.in_sample_rate,
            blocksize=self.config.audio.in_blocksize,
            pre_roll_ms=self.config.vad.pre_roll_ms,
        )
        
        self._audio_out = AudioOutput(
            device_id=self.config.audio.out_device,
            sample_rate=self.config.audio.out_sample_rate,
            blocksize=self.config.audio.out_blocksize,
        )
        
        # State
        self._state = PipelineState.IDLE
        self._state_lock = asyncio.Lock()
        self._running = False
        self._stop_requested = False
        
        # Metrics
        self.metrics = PipelineMetrics()
        
        # Event callbacks
        self.on_state_change: Optional[Callable[[PipelineState, PipelineState], Awaitable[None]]] = None
        self.on_transcription_partial: Optional[Callable[[str], Awaitable[None]]] = None
        self.on_transcription_final: Optional[Callable[[str], Awaitable[None]]] = None
        self.on_intent_classified: Optional[Callable[[ClassifyResult], Awaitable[None]]] = None
        self.on_response_start: Optional[Callable[[str], Awaitable[None]]] = None
        self.on_response_complete: Optional[Callable[[str], Awaitable[None]]] = None
        self.on_barge_in: Optional[Callable[[], Awaitable[None]]] = None
        self.on_error: Optional[Callable[[Exception], Awaitable[None]]] = None
        self.on_metrics: Optional[Callable[[PipelineMetrics], Awaitable[None]]] = None
        
        # Internal queues
        self._stt_partial_queue: asyncio.Queue[str] = asyncio.Queue()
        self._stt_final_queue: asyncio.Queue[str] = asyncio.Queue()
        self._tts_chunk_queue: asyncio.Queue[np.ndarray] = asyncio.Queue()
        self._vad_result_queue: asyncio.Queue[VADResult] = asyncio.Queue()
        
        # Component tasks
        self._tasks: list[asyncio.Task] = []
    
    @property
    def state(self) -> PipelineState:
        return self._state
    
    @property
    def running(self) -> bool:
        return self._running
    
    async def _transition_state(self, new_state: PipelineState) -> None:
        """Transition to new state with callback."""
        async with self._state_lock:
            old_state = self._state
            if old_state != new_state:
                self._state = new_state
                if self.on_state_change:
                    try:
                        await self.on_state_change(old_state, new_state)
                    except Exception:
                        pass  # Don't let callback errors break pipeline
    
    async def _default_llm(self, text: str, context=None) -> str:
        """Default LLM client using brain.core.think."""
        from brain import think
        from brain import ConversationContext
        
        if context is None:
            context = ConversationContext(max_turns=10)
        
        return think(text, context=context)
    
    async def start(self) -> None:
        """Start all pipeline components."""
        if self._running:
            return
        
        self._running = True
        self._stop_requested = False
        
        # Start components
        await self._vad.start()
        await self._stt.start()
        await self._tts.start()
        await self._audio_in.start()
        await self._audio_out.start()
        
        await self._transition_state(PipelineState.LISTENING)
        
        # Start component tasks
        self._tasks = [
            asyncio.create_task(self._vad_loop()),
            asyncio.create_task(self._stt_loop()),
            asyncio.create_task(self._tts_loop()),
            asyncio.create_task(self._audio_output_loop()),
            asyncio.create_task(self._pipeline_loop()),
        ]
    
    async def stop(self) -> None:
        """Stop all pipeline components gracefully."""
        if not self._running:
            return
        
        self._running = False
        self._stop_requested = True
        
        # Cancel tasks
        for task in self._tasks:
            task.cancel()
        
        # Wait for tasks to finish
        if self._tasks:
            await asyncio.gather(*self._tasks, return_exceptions=True)
        
        # Stop components
        await self._tts.stop()
        await self._stt.stop()
        await self._vad.stop()
        await self._audio_out.stop()
        await self._audio_in.stop()
        
        await self._transition_state(PipelineState.IDLE)
    
    async def _vad_loop(self) -> None:
        """Process audio frames through VAD."""
        try:
            async for frame in self._audio_in.frames:
                if not self._running:
                    break
                
                result = self._vad.process_frame(frame)
                await self._vad_result_queue.put(result)
                
        except asyncio.CancelledError:
            pass
        except Exception as e:
            if self.on_error:
                await self.on_error(e)
    
    async def _stt_loop(self) -> None:
        """Process VAD results through STT."""
        buffer = np.array([], dtype=np.float32)
        capturing = False
        
        try:
            while self._running:
                # Wait for VAD result
                try:
                    vad_result = await asyncio.wait_for(
                        self._vad_result_queue.get(), timeout=0.1
                    )
                except asyncio.TimeoutError:
                    continue
                
                # Get audio frame from input (already processed by VAD)
                # We need to get the corresponding audio frame
                # For now, we'll use the audio input's frames directly
                # This is a simplification - in practice, we'd need proper sync
                
                if vad_result.speech_start:
                    capturing = True
                    buffer = np.array([], dtype=np.float32)
                
                if capturing:
                    # Get audio from input queue (this is approximate)
                    try:
                        frame = self._audio_in.frames.get_nowait()
                        buffer = np.concatenate([buffer, frame.flatten()])
                    except asyncio.QueueEmpty:
                        pass
                
                if vad_result.speech_end and capturing:
                    # Speech segment complete - send to STT
                    if len(buffer) > 0:
                        await self._stt.transcribe_stream(
                            buffer,
                            on_partial=self._on_stt_partial,
                            on_final=self._on_stt_final,
                        )
                    capturing = False
                    buffer = np.array([], dtype=np.float32)
                    
        except asyncio.CancelledError:
            pass
        except Exception as e:
            if self.on_error:
                await self.on_error(e)
    
    async def _on_stt_partial(self, text: str) -> None:
        """Handle partial STT result."""
        if self.on_transcription_partial:
            await self.on_transcription_partial(text)
    
    async def _on_stt_final(self, text: str) -> None:
        """Handle final STT result - process through intent and LLM."""
        if not text:
            return
        
        if self.on_transcription_final:
            await self.on_transcription_final(text)
        
        # Classify intent
        start_time = time.perf_counter()
        intent_result = self._intent_layer.classify(text)
        self.metrics.intent_latency_ms += (time.perf_counter() - start_time) * 1000
        
        if self.on_intent_classified:
            await self.on_intent_classified(intent_result)
        
        # Get LLM response
        start_time = time.perf_counter()
        try:
            response = await self._llm_client(text)
        except Exception as e:
            if self.on_error:
                await self.on_error(e)
            return
        self.metrics.llm_latency_ms += (time.perf_counter() - start_time) * 1000
        
        if self.on_response_start:
            await self.on_response_start(response)
        
        # Send to TTS
        async def text_gen():
            yield response
        
        await self._tts.synthesize_stream(
            self._text_chunker(response),
            on_chunk=self._on_tts_chunk,
        )
        
        if self.on_response_complete:
            await self.on_response_complete(response)
    
    async def _text_chunker(self, text: str):
        """Split text into sentence chunks for TTS."""
        import re
        sentences = re.split(r'(?<=[.!?])\s+', text)
        for sentence in sentences:
            if sentence.strip():
                yield sentence.strip()
    
    async def _on_tts_chunk(self, chunk: np.ndarray) -> None:
        """Handle TTS audio chunk."""
        await self._tts_chunk_queue.put(chunk)
    
    async def _tts_loop(self) -> None:
        """Process TTS chunks for playback."""
        try:
            while self._running:
                try:
                    chunk = await asyncio.wait_for(
                        self._tts_chunk_queue.get(), timeout=0.1
                    )
                except asyncio.TimeoutError:
                    continue
                
                await self._audio_out.write(chunk)
                
        except asyncio.CancelledError:
            pass
        except Exception as e:
            if self.on_error:
                await self.on_error(e)
    
    async def _audio_output_loop(self) -> None:
        """Monitor audio output for barge-in detection."""
        try:
            while self._running:
                await asyncio.sleep(0.05)
                
                # Check for barge-in during TTS playback
                if self._state == PipelineState.SPEAKING:
                    # Check VAD during playback
                    try:
                        vad_result = self._vad_result_queue.get_nowait()
                        if vad_result.speech_start:
                            await self._handle_barge_in()
                    except asyncio.QueueEmpty:
                        pass
                        
        except asyncio.CancelledError:
            pass
        except Exception as e:
            if self.on_error:
                await self.on_error(e)
    
    async def _handle_barge_in(self) -> None:
        """Handle user interruption during TTS."""
        self.metrics.barge_in_count += 1
        
        # Stop TTS immediately
        self._tts.stop_current()
        
        # Flush TTS queue
        while not self._tts_chunk_queue.empty():
            try:
                self._tts_chunk_queue.get_nowait()
            except asyncio.QueueEmpty:
                break
        
        # Transition state
        await self._transition_state(PipelineState.INTERRUPTED)
        
        if self.on_barge_in:
            await self.on_barge_in()
        
        # Go back to listening
        await self._transition_state(PipelineState.LISTENING)
    
    async def _pipeline_loop(self) -> None:
        """Main pipeline coordination loop."""
        try:
            while self._running:
                await asyncio.sleep(0.1)
                
                # Update metrics periodically
                if self.on_metrics and self.metrics.total_turns > 0:
                    await self.on_metrics(self.metrics)
                    
        except asyncio.CancelledError:
            pass
        except Exception as e:
            if self.on_error:
                await self.on_error(e)
    
    async def __aenter__(self) -> "VoicePipeline":
        await self.start()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        await self.stop()


# Convenience function for simple usage
async def run_voice_conversation(
    config: Optional[PipelineConfig] = None,
    on_transcription: Optional[Callable[[str], Awaitable[None]]] = None,
    on_response: Optional[Callable[[str], Awaitable[None]]] = None,
    on_barge_in: Optional[Callable[[], Awaitable[None]]] = None,
) -> None:
    """
    Run a complete voice conversation session.
    
    Args:
        config: Pipeline configuration
        on_transcription: Callback for final transcriptions
        on_response: Callback for DECIA responses
        on_barge_in: Callback for barge-in events
    """
    pipeline = VoicePipeline(config=config)
    
    if on_transcription:
        pipeline.on_transcription_final = on_transcription
    if on_response:
        pipeline.on_response_complete = on_response
    if on_barge_in:
        pipeline.on_barge_in = on_barge_in
    
    async with pipeline:
        # Keep running until stopped
        while pipeline.running:
            await asyncio.sleep(1)