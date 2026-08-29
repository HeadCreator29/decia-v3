# tests/test_stt_processor.py - Unit tests for STT processor

import asyncio
import numpy as np
import pytest
from app.services.voice_pipeline.stt_processor import (
    STTProcessor,
    STTProcessorStreaming,
    STTResult,
)


class TestSTTProcessor:
    """Tests for STTProcessor with faster-whisper."""
    
    @pytest.mark.asyncio
    async def test_initialization(self):
        """Test STTProcessor initializes correctly."""
        processor = STTProcessor(
            model_size="tiny",  # Use tiny for fast tests
            language="es",
            beam_size=1,
            compute_type="int8",
        )
        await processor.start()
        assert processor._model is not None
        assert processor._running == True
        await processor.stop()
    
    @pytest.mark.asyncio
    async def test_transcribe_silence(self):
        """Test transcription of silence returns empty."""
        processor = STTProcessor(
            model_size="tiny",
            language="es",
            beam_size=1,
            compute_type="int8",
        )
        await processor.start()
        
        # Silence
        silence = np.zeros(16000, dtype=np.float32)  # 1 second
        
        results = []
        
        async def on_final(text):
            results.append(text)
        
        await processor.transcribe_stream(
            silence,
            on_final=on_final,
        )
        
        # Silence should produce empty result
        assert len(results) == 1
        await processor.stop()
    
    @pytest.mark.asyncio
    async def test_transcribe_noise(self):
        """Test transcription of noise."""
        processor = STTProcessor(
            model_size="tiny",
            language="es",
            beam_size=1,
            compute_type="int8",
        )
        await processor.start()
        
        # Random noise
        np.random.seed(42)
        noise = np.random.normal(0, 0.1, 16000).astype(np.float32)
        
        results = []
        
        async def on_final(text):
            results.append(text)
        
        await processor.transcribe_stream(
            noise,
            on_final=on_final,
        )
        
        assert len(results) == 1
        await processor.stop()


class TestSTTProcessorStreaming:
    """Tests for STTProcessorStreaming (chunk-based)."""
    
    @pytest.mark.asyncio
    async def test_initialization(self):
        """Test STTProcessorStreaming initializes correctly."""
        processor = STTProcessorStreaming(
            model_size="tiny",
            language="es",
            beam_size=1,
            compute_type="int8",
        )
        await processor.start()
        assert processor._model is not None
        assert processor._running == True
        await processor.stop()
    
    @pytest.mark.asyncio
    async def test_add_chunk_and_transcribe(self):
        """Test adding chunks and transcribing."""
        processor = STTProcessorStreaming(
            model_size="tiny",
            language="es",
            beam_size=1,
            compute_type="int8",
        )
        await processor.start()
        
        # Add silence chunks
        for _ in range(5):
            silence = np.zeros(3200, dtype=np.float32)  # 200ms @ 16kHz
            processor.add_audio_chunk(silence)
        
        result = await processor.get_transcription()
        
        # Silence should produce empty string (not None)
        assert result is not None
        await processor.stop()
    
    @pytest.mark.asyncio
    async def test_empty_buffer(self):
        """Test empty buffer returns None."""
        processor = STTProcessorStreaming(
            model_size="tiny",
            language="es",
            beam_size=1,
            compute_type="int8",
        )
        await processor.start()
        
        result = await processor.get_transcription()
        assert result is None
        await processor.stop()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])