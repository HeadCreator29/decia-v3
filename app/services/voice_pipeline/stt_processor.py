# stt_processor.py - Streaming Speech-to-Text with faster-whisper

import asyncio
import os
from dataclasses import dataclass
from typing import Optional, Callable, Awaitable
import numpy as np
from faster_whisper import WhisperModel


@dataclass
class STTResult:
    """Result of STT transcription."""
    text: str
    is_partial: bool
    confidence: float
    language: str


class STTProcessor:
    """
    Streaming Speech-to-Text processor using faster-whisper.
    
    Provides streaming transcription with partial results for real-time feedback
    and final transcription on segment end.
    """
    
    def __init__(
        self,
        model_size: str = "small",
        language: str = "es",
        beam_size: int = 5,
        compute_type: str = "int8",
        device: str = "cpu",
    ):
        """
        Initialize STT processor.
        
        Args:
            model_size: Whisper model size (tiny, base, small, medium, large)
            language: Language code (e.g., "es", "en")
            beam_size: Beam size for decoding
            compute_type: Compute type (int8, int16, float16, float32)
            device: Device to run on (cpu, cuda)
        """
        self.model_size = model_size
        self.language = language
        self.beam_size = beam_size
        self.compute_type = compute_type
        self.device = device
        
        self._model: Optional[WhisperModel] = None
        self._running = False
    
    async def start(self) -> None:
        """Load and warmup Whisper model."""
        if self._running:
            return
            
        self._model = WhisperModel(
            self.model_size,
            device=self.device,
            compute_type=self.compute_type,
        )
        
        # Warmup with silence
        dummy_audio = np.zeros(16000, dtype=np.float32)  # 1 second of silence
        segments, _ = self._model.transcribe(
            dummy_audio,
            language=self.language,
            beam_size=self.beam_size,
            vad_filter=False,
        )
        for _ in segments:
            pass  # Consume generator
        
        self._running = True
    
    async def stop(self) -> None:
        """Cleanup."""
        self._running = False
        self._model = None
    
    async def transcribe_stream(
        self,
        audio_buffer: np.ndarray,
        on_partial: Optional[Callable[[str], Awaitable[None]]] = None,
        on_final: Optional[Callable[[str], Awaitable[None]]] = None,
    ) -> None:
        """
        Stream transcription of audio buffer.
        
        Args:
            audio_buffer: Audio data (float32, 16kHz, mono)
            on_partial: Callback for partial transcription results
            on_final: Callback for final transcription result
        """
        if not self._running or self._model is None:
            raise RuntimeError("STTProcessor not started")
        
        if audio_buffer.size == 0:
            if on_final:
                await on_final("")
            return
        
        # Ensure correct format
        if audio_buffer.dtype != np.float32:
            audio_buffer = audio_buffer.astype(np.float32)
        
        if audio_buffer.ndim == 2:
            audio_buffer = audio_buffer.flatten()
        
        # Transcribe with streaming
        try:
            segments, info = self._model.transcribe(
                audio_buffer,
                language=self.language,
                beam_size=self.beam_size,
                vad_filter=False,  # We handle VAD externally
                condition_on_previous_text=False,
                word_timestamps=False,
            )
            
            full_text_parts = []
            has_segments = False
            
            for segment in segments:
                segment_text = segment.text.strip()
                if segment_text:
                    full_text_parts.append(segment_text)
                    has_segments = True
                    
                    # Emit partial result
                    if on_partial:
                        partial_text = " ".join(full_text_parts)
                        await on_partial(partial_text)
            
            # Emit final result (even if empty)
            if on_final:
                final_text = " ".join(full_text_parts) if has_segments else ""
                await on_final(final_text)
                
        except Exception as e:
            # On error, emit empty final to avoid hanging
            if on_final:
                await on_final("")
            raise


class STTProcessorStreaming:
    """
    Alternative streaming interface for real-time chunk processing.
    
    Accepts audio chunks incrementally and provides partial results.
    """
    
    def __init__(
        self,
        model_size: str = "small",
        language: str = "es",
        beam_size: int = 5,
        compute_type: str = "int8",
        device: str = "cpu",
    ):
        self.model_size = model_size
        self.language = language
        self.beam_size = beam_size
        self.compute_type = compute_type
        self.device = device
        
        self._model: Optional[WhisperModel] = None
        self._buffer = bytearray()
        self._running = False
    
    async def start(self) -> None:
        """Load and warmup Whisper model."""
        if self._running:
            return
            
        self._model = WhisperModel(
            self.model_size,
            device=self.device,
            compute_type=self.compute_type,
        )
        self._running = True
    
    async def stop(self) -> None:
        """Cleanup."""
        self._running = False
        self._model = None
        self._buffer.clear()
    
    def add_audio_chunk(self, chunk: np.ndarray) -> None:
        """Add audio chunk to internal buffer."""
        if chunk.dtype != np.float32:
            chunk = chunk.astype(np.float32)
        if chunk.ndim == 2:
            chunk = chunk.flatten()
        # Convert to int16 bytes for internal buffering
        int16_data = (chunk * 32767).astype(np.int16)
        self._buffer.extend(int16_data.tobytes())
    
    async def get_transcription(
        self,
        on_partial: Optional[Callable[[str], Awaitable[None]]] = None,
        on_final: Optional[Callable[[str], Awaitable[None]]] = None,
    ) -> Optional[str]:
        """
        Process buffered audio and return transcription.
        
        Returns final transcription text or None if buffer empty.
        """
        if not self._running or self._model is None:
            raise RuntimeError("STTProcessor not started")
        
        if len(self._buffer) == 0:
            if on_final:
                await on_final("")
            return None
        
        # Convert buffer to float32 array
        audio_data = np.frombuffer(self._buffer, dtype=np.int16).astype(np.float32) / 32767.0
        self._buffer.clear()
        
        # Transcribe
        try:
            segments, info = self._model.transcribe(
                audio_data,
                language=self.language,
                beam_size=self.beam_size,
                vad_filter=False,
                condition_on_previous_text=False,
            )
            
            full_text_parts = []
            has_segments = False
            
            for segment in segments:
                segment_text = segment.text.strip()
                if segment_text:
                    full_text_parts.append(segment_text)
                    has_segments = True
                    
                    # In a real streaming implementation, we'd emit partial here
                    # For now, we just collect all
            
            # Emit final result (even if empty)
            if on_final:
                final_text = " ".join(full_text_parts) if has_segments else ""
                await on_final(final_text)
            
            if has_segments:
                return " ".join(full_text_parts)
            
        except Exception as e:
            if on_final:
                await on_final("")
            raise
        
        return ""
    
    async def __aenter__(self) -> "STTProcessorStreaming":
        await self.start()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        await self.stop()