# tts_processor.py - Streaming Text-to-Speech with Piper + pyttsx3 fallback

import asyncio
import json
import os
import re
from dataclasses import dataclass
from typing import Optional, Callable, Awaitable, AsyncIterator
import numpy as np

try:
    from piper import PiperVoice
    PIPER_AVAILABLE = True
except ImportError:
    PIPER_AVAILABLE = False

try:
    import pyttsx3
    PYTTSX3_AVAILABLE = True
except ImportError:
    PYTTSX3_AVAILABLE = False


@dataclass
class TTSChunk:
    """Audio chunk from TTS synthesis."""
    audio: np.ndarray          # PCM float32 mono
    is_final: bool
    text_source: str           # Source text for this chunk


class BaseTTS:
    """Base class for TTS processors."""
    
    def __init__(
        self,
        sample_rate: int = 22050,
        speed: float = 1.0,
    ):
        self.sample_rate = sample_rate
        self.speed = speed
    
    async def start(self) -> None:
        pass
    
    async def stop(self) -> None:
        pass
    
    async def synthesize_stream(
        self,
        text_stream: AsyncIterator[str],
        on_chunk: Callable[[np.ndarray], Awaitable[None]],
    ) -> None:
        raise NotImplementedError
    
    def stop_current(self) -> None:
        pass


class Pyttsx3TTS(BaseTTS):
    """pyttsx3 TTS fallback (non-streaming but chunked)."""
    
    def __init__(
        self,
        sample_rate: int = 22050,
        speed: float = 1.0,
    ):
        super().__init__(sample_rate, speed)
        self._engine = None
        self._stop_requested = False
    
    async def start(self) -> None:
        if not PYTTSX3_AVAILABLE:
            raise RuntimeError("pyttsx3 not available")
        self._engine = pyttsx3.init()
        self._engine.setProperty("rate", int(175 * self.speed))
        self._engine.setProperty("volume", 1.0)
    
    async def stop(self) -> None:
        if self._engine:
            self._engine.stop()
            self._engine = None
    
    async def synthesize_stream(
        self,
        text_stream: AsyncIterator[str],
        on_chunk: Callable[[np.ndarray], Awaitable[None]],
    ) -> None:
        """Synthesize text stream using pyttsx3 (non-streaming but chunked)."""
        if self._engine is None:
            await self.start()
        
        # Collect all text first (pyttsx3 is not truly streaming)
        text_parts = []
        async for text in text_stream:
            if text:
                text_parts.append(text)
        
        if not text_parts:
            return
        
        full_text = " ".join(text_parts)
        
        # Synthesize to temporary file or use callback
        # pyttsx3 doesn't support streaming callbacks, so we synthesize to file
        # and then read it in chunks
        import tempfile
        import soundfile as sf
        
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
            tmp_path = tmp.name
        
        try:
            self._engine.save_to_file(full_text, tmp_path)
            self._engine.runAndWait()
            
            # Read and stream chunks
            import soundfile as sf
            data, sr = sf.read(tmp_path, dtype="float32")
            
            # Resample if needed
            if sr != self.sample_rate:
                import scipy.signal
                data = scipy.signal.resample(data, int(len(data) * self.sample_rate / sr))
            
            # Stream in chunks
            chunk_size = 1024
            for i in range(0, len(data), chunk_size):
                chunk = data[i:i+chunk_size]
                if len(chunk) == 0:
                    break
                await on_chunk(chunk.astype(np.float32))
                if self._stop_requested:
                    break
        finally:
            try:
                os.unlink(tmp_path)
            except Exception:
                pass
    
    def stop_current(self) -> None:
        self._stop_requested = True
        if self._engine:
            self._engine.stop()


class PiperTTS(BaseTTS):
    """Piper TTS with streaming support."""
    
    def __init__(
        self,
        voice_id: str = "es_ES-carlfm-x_low",
        speed: float = 1.0,
        sample_rate: int = 22050,
        model_dir: str = "models",
        fallback_tts: Optional[BaseTTS] = None,
    ):
        super().__init__(sample_rate, speed)
        self.voice_id = voice_id
        self.model_dir = model_dir
        self._voice: Optional["PiperVoice"] = None
        self._stop_requested = False
        self._fallback_tts = fallback_tts or (Pyttsx3TTS() if PYTTSX3_AVAILABLE else None)
        self._use_fallback = False
    
    async def start(self) -> None:
        """Load Piper voice model."""
        if not PIPER_AVAILABLE:
            raise RuntimeError("Piper TTS not available (piper-tts not installed)")
        
        model_path = os.path.join(self.model_dir, f"{self.voice_id}.onnx")
        config_path = os.path.join(self.model_dir, f"{self.voice_id}.onnx.json")
        
        if not os.path.exists(model_path):
            raise FileNotFoundError(f"Piper model not found: {model_path}")
        if not os.path.exists(config_path):
            raise FileNotFoundError(f"Piper config not found: {config_path}")
        
        # Load voice
        with open(config_path, "r") as f:
            config = json.load(f)
        
        self._voice = PiperVoice.load(model_path, config)
        
        # Warmup
        self._voice.synthesize_stream_raw("Hola")
        for _ in self._voice.synthesize_stream_raw("Hola"):
            pass
    
    async def stop(self) -> None:
        self._voice = None
    
    async def synthesize_stream(
        self,
        text_stream: AsyncIterator[str],
        on_chunk: Callable[[np.ndarray], Awaitable[None]],
    ) -> None:
        """Stream synthesis using Piper."""
        if self._voice is None:
            raise RuntimeError("Piper TTS not started")
        
        self._stop_requested = False
        self._use_fallback = False
        
        # Collect text into sentences
        sentence_buffer = ""
        
        async for text in text_stream:
            if self._stop_requested:
                break
            
            if not text:
                continue
            
            sentence_buffer += text
            
            # Split into sentences
            sentences = self._split_sentences(sentence_buffer)
            
            # Keep last incomplete sentence in buffer
            if sentence_buffer and not sentence_buffer[-1] in ".!?":
                sentence_buffer = sentences.pop() if sentences else sentence_buffer
            else:
                sentence_buffer = ""
            
            # Synthesize complete sentences
            for sentence in sentences:
                if self._stop_requested:
                    break
                
                await self._synthesize_sentence(sentence.strip(), on_chunk)
        
        # Synthesize remaining buffer
        if sentence_buffer.strip() and not self._stop_requested:
            await self._synthesize_sentence(sentence_buffer.strip(), on_chunk)
    
    def _split_sentences(self, text: str) -> list[str]:
        """Split text into sentences."""
        import re
        # Split on sentence boundaries, keeping the delimiter
        sentences = re.split(r'(?<=[.!?])\s+', text)
        return [s.strip() for s in sentences if s.strip()]
    
    async def _synthesize_sentence(self, sentence: str, on_chunk: Callable[[np.ndarray], Awaitable[None]]) -> None:
        """Synthesize a single sentence with Piper, fallback on failure."""
        if self._stop_requested:
            return
        
        if self._use_fallback and self._fallback_tts:
            # Use fallback for remaining synthesis
            await self._fallback_tts.synthesize_stream(
                iter([sentence]), on_chunk
            )
            return
        
        try:
            # Piper synthesizes to raw audio chunks
            for audio_chunk in self._voice.synthesize_stream_raw(sentence):
                if self._stop_requested:
                    break
                
                # Convert int16 to float32
                audio_float = np.frombuffer(audio_chunk, dtype=np.int16).astype(np.float32) / 32767.0
                
                # Resample if needed (Piper outputs at voice sample rate)
                if self._voice.config.sample_rate != self.sample_rate:
                    import scipy.signal
                    target_len = int(len(audio_float) * self.sample_rate / self._voice.config.sample_rate)
                    audio_float = np.interp(
                        np.linspace(0, len(audio_float), target_len),
                        np.arange(len(audio_float)),
                        audio_float
                    ).astype(np.float32)
                
                await on_chunk(audio_float)
                
        except Exception as e:
            # On Piper failure, switch to fallback
            if self._fallback_tts and not self._use_fallback:
                print(f"[TTS] Piper failed, switching to pyttsx3 fallback: {e}")
                self._use_fallback = True
                if self._fallback_tts:
                    await self._fallback_tts.synthesize_stream(
                        iter([sentence]), on_chunk
                    )
            else:
                raise
    
    def stop_current(self) -> None:
        self._stop_requested = True
    
    async def __aenter__(self) -> "PiperTTS":
        await self.start()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        await self.stop()


class TTSProcessor(BaseTTS):
    """
    TTS Processor with Piper primary + pyttsx3 fallback.
    
    Handles sentence-level chunking, streaming synthesis, and fallback chain.
    """
    
    def __init__(
        self,
        voice_id: str = "es_ES-carlfm-x_low",
        speed: float = 1.0,
        sample_rate: int = 22050,
        model_dir: str = "models",
        fallback_enabled: bool = True,
    ):
        super().__init__(sample_rate, speed)
        self._piper: Optional[PiperTTS] = None
        self._fallback: Optional[Pyttsx3TTS] = None
        self._active: Optional[BaseTTS] = None
        self._use_fallback = False
        self._fallback_enabled = fallback_enabled
        self._voice_id = voice_id
        self._speed = speed
        self._sample_rate = sample_rate
        self._model_dir = model_dir
    
    async def start(self) -> None:
        """Initialize TTS engines."""
        # Try Piper first
        try:
            self._piper = PiperTTS(
                voice_id=self.voice_id,
                speed=self._speed,
                sample_rate=self._sample_rate,
            )
            await self._piper.start()
            self._active = self._piper
        except Exception as e:
            print(f"[TTS] Piper failed to initialize: {e}")
            self._piper = None
        
        # Initialize fallback if enabled
        if self._fallback_enabled and PYTTSX3_AVAILABLE:
            self._fallback = Pyttsx3TTS(speed=self._speed)
            await self._fallback.start()
        
        # Set active TTS (prefer Piper)
        if self._active is None and self._fallback:
            self._active = self._fallback
            self._use_fallback = True
    
    async def stop(self) -> None:
        if self._piper:
            await self._piper.stop()
        if self._fallback:
            await self._fallback.stop()
        self._active = None
    
    async def synthesize_stream(
        self,
        text_stream: AsyncIterator[str],
        on_chunk: Callable[[np.ndarray], Awaitable[None]],
    ) -> None:
        """Stream synthesis with active TTS."""
        if self._active is None:
            raise RuntimeError("TTSProcessor not started")
        
        await self._active.synthesize_stream(text_stream, on_chunk)
    
    def stop_current(self) -> None:
        if self._active:
            self._active.stop_current()
    
    def switch_to_fallback(self) -> bool:
        """Manually switch to fallback TTS."""
        if self._fallback and self._active != self._fallback:
            self._active = self._fallback
            self._use_fallback = True
            return True
        return False
    
    @property
    def is_using_fallback(self) -> bool:
        return self._use_fallback
    
    async def __aenter__(self) -> "TTSProcessor":
        await self.start()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        await self.stop()


async def text_chunker(text_stream: AsyncIterator[str], min_chars: int = 10) -> AsyncIterator[str]:
    """
    Chunk text stream into sentence-level chunks.
    
    Yields text chunks of at least min_chars, splitting on sentence boundaries.
    """
    import re
    buffer = ""
    
    async for text in text_stream:
        if not text:
            continue
        buffer += text
        
        # Split on sentence boundaries
        sentences = re.split(r'(?<=[.!?])\s+', buffer)
        
        # Keep last incomplete sentence in buffer
        if buffer and not buffer[-1] in ".!?":
            if sentences:
                buffer = sentences.pop()
            else:
                buffer = ""
        else:
            buffer = ""
        
        for sentence in sentences:
            if sentence.strip():
                yield sentence.strip()
    
    # Yield remaining buffer
    if buffer.strip():
        yield buffer.strip()