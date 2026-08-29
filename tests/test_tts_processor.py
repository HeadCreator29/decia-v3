# tests/test_tts_processor.py - Unit tests for TTS processor

import asyncio
import numpy as np
import pytest
from app.services.voice_pipeline.tts_processor import (
    PiperTTS,
    Pyttsx3TTS,
    TTSProcessor,
    text_chunker,
    TTSChunk,
)


class TestPyttsx3TTS:
    """Tests for pyttsx3 TTS fallback."""
    
    @pytest.mark.asyncio
    async def test_initialization(self):
        """Test pyttsx3 TTS initializes correctly."""
        tts = Pyttsx3TTS()
        await tts.start()
        assert tts._engine is not None
        await tts.stop()
    
    @pytest.mark.asyncio
    async def test_synthesize_stream(self):
        """Test streaming synthesis with pyttsx3."""
        tts = Pyttsx3TTS()
        await tts.start()
        
        chunks = []
        
        async def on_chunk(chunk):
            chunks.append(chunk)
        
        async def text_gen():
            yield "Hola mundo"
        
        await tts.synthesize_stream(text_gen(), on_chunk)
        
        assert len(chunks) > 0
        await tts.stop()


class TestPiperTTS:
    """Tests for Piper TTS."""
    
    def test_initialization_with_missing_model(self):
        """Test Piper fails gracefully when model missing."""
        with pytest.raises(FileNotFoundError):
            PiperTTS(voice_id="nonexistent", model_dir="/nonexistent")


class TestTTSProcessor:
    """Tests for TTSProcessor with Piper + pyttsx3 fallback."""
    
    @pytest.mark.asyncio
    async def test_initialization_with_fallback(self):
        """Test TTSProcessor initializes with pyttsx3 fallback when Piper missing."""
        processor = TTSProcessor(
            voice_id="nonexistent",
            model_dir="/nonexistent",
            fallback_enabled=True,
        )
        await processor.start()
        
        # Should fall back to pyttsx3
        assert processor._active is not None
        assert processor._use_fallback == True
        await processor.stop()
    
    @pytest.mark.asyncio
    async def test_synthesize_stream_with_fallback(self):
        """Test streaming synthesis with pyttsx3 fallback."""
        processor = TTSProcessor(
            voice_id="nonexistent",
            model_dir="/nonexistent",
            fallback_enabled=True,
        )
        await processor.start()
        
        chunks = []
        
        async def on_chunk(chunk):
            chunks.append(chunk)
        
        async def text_gen():
            yield "Hola mundo"
        
        await processor.synthesize_stream(text_gen(), on_chunk)
        
        assert len(chunks) > 0
        await processor.stop()
    
    @pytest.mark.asyncio
    async def test_stop_current(self):
        """Test stop_current interrupts synthesis."""
        processor = TTSProcessor(
            voice_id="nonexistent",
            model_dir="/nonexistent",
            fallback_enabled=True,
        )
        await processor.start()
        
        processor.stop_current()
        assert processor._active._stop_requested == True
        await processor.stop()


class TestTextChunker:
    """Tests for text_chunker utility."""
    
    @pytest.mark.asyncio
    async def test_basic_chunking(self):
        """Test basic sentence chunking."""
        async def text_gen():
            yield "Hola. "
            yield "¿Cómo estás? "
            yield "Bien, gracias."
        
        chunks = []
        async for chunk in text_chunker(text_gen()):
            chunks.append(chunk)
        
        assert len(chunks) == 3
        assert chunks[0] == "Hola."
        assert chunks[1] == "¿Cómo estás?"
        assert chunks[2] == "Bien, gracias."
    
    @pytest.mark.asyncio
    async def test_chunking_with_partial_sentences(self):
        """Test chunking with partial sentences."""
        async def text_gen():
            yield "Hola, ¿cómo "
            yield "estás? Bien."
        
        chunks = []
        async for chunk in text_chunker(text_gen()):
            chunks.append(chunk)
        
        assert len(chunks) == 2
        assert "estás?" in chunks[0] or "estás?" in chunks[1]
    
    @pytest.mark.asyncio
    async def test_empty_input(self):
        """Test empty input produces no chunks."""
        async def text_gen():
            yield ""
            yield "   "
        
        chunks = []
        async for chunk in text_chunker(text_gen()):
            chunks.append(chunk)
        
        assert len(chunks) == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])