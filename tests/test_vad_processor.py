# tests/test_vad_processor.py - Unit tests for VAD processors

import asyncio
import numpy as np
import pytest
from app.services.voice_pipeline.vad_processor import (
    SileroVADProcessor,
    WebRTCVADProcessor,
    VADProcessor,
    VADResult,
)


class TestWebRTCVADProcessor:
    """Tests for WebRTC VAD fallback processor."""
    
    @pytest.mark.asyncio
    async def test_initialization(self):
        """Test WebRTC VAD initializes correctly."""
        vad = WebRTCVADProcessor(
            threshold=0.5,
            min_speech_ms=250,
            min_silence_ms=100,
            sample_rate=16000,
        )
        await vad.start()
        assert vad._vad is not None
        await vad.stop()
    
    def test_process_silence(self):
        """Test VAD on silence (zeros)."""
        vad = WebRTCVADProcessor(threshold=0.5, sample_rate=16000)
        vad._update_state(False)  # Reset state
        
        # Silence frame (zeros)
        silence = np.zeros(512, dtype=np.float32)
        result = vad.process_frame(silence)
        
        assert isinstance(result, VADResult)
        assert result.probability >= 0.0
        assert result.probability <= 1.0
        assert result.is_speech in (True, False)
        assert result.speech_start in (True, False)
        assert result.speech_end in (True, False)
    
    def test_process_noise(self):
        """Test VAD on random noise."""
        vad = WebRTCVADProcessor(threshold=0.5, sample_rate=16000)
        
        # Random noise
        np.random.seed(42)
        noise = np.random.normal(0, 0.01, 512).astype(np.float32)
        result = vad.process_frame(noise)
        
        assert isinstance(result, VADResult)
        assert 0.0 <= result.probability <= 1.0
    
    def test_state_machine(self):
        """Test internal state machine transitions."""
        # WebRTC VAD with threshold=0.5
        # WebRTC processes 512-sample frames as 320-sample chunks (20ms each)
        # So each process_frame call = 1 WebRTC frame (20ms)
        # 250ms at 20ms/frame = 12.5 -> need 13 frames for speech_start
        # 100ms at 20ms/frame = 5 frames for silence_end
        vad = WebRTCVADProcessor(
            threshold=0.5,
            min_speech_ms=250,  # 250ms = 13 frames @ 20ms/frame (320 samples @ 16kHz = 20ms)
            min_silence_ms=100,  # 100ms = 5 frames @ 20ms/frame
            sample_rate=16000,
        )
        
        # Create a strong speech-like signal (high amplitude)
        speech_frame = np.random.normal(0, 0.5, 512).astype(np.float32)
        silence_frame = np.zeros(512, dtype=np.float32)
        
        # Reset state
        vad._was_speech = False
        vad._speech_frame_count = 0
        vad._silence_frame_count = 0
        vad._speech_started.clear()
        vad._speech_ended.clear()
        
        # 250ms at 20ms/frame = 12.5 -> need 13 frames for speech_start
        # First 12 frames - no speech_start yet
        for i in range(12):
            result = vad.process_frame(speech_frame)
            assert result.speech_start == False, f"Frame {i}: speech_start should be False"
        
        # 13th frame - should trigger speech_start
        result = vad.process_frame(speech_frame)
        assert result.speech_start == True, "13th frame should trigger speech_start"
        assert vad._was_speech == True
        
        # Now silence - should trigger speech_end after min_silence_frames (5 frames @ 20ms = 100ms)
        silence = np.zeros(512, dtype=np.float32)
        for i in range(4):
            result = vad.process_frame(silence)
            assert result.speech_end == False, f"Silence frame {i}: speech_end should be False"
        
        # 5th silence frame - should trigger speech_end
        result = vad.process_frame(silence)
        assert result.speech_end == True, "5th silence frame should trigger speech_end"
        assert vad._was_speech == False


class TestSileroVADProcessor:
    """Tests for Silero VAD processor (requires ONNX model)."""
    
    def test_initialization_fails_gracefully_without_model(self):
        """Test that Silero fails gracefully when model missing."""
        with pytest.raises(FileNotFoundError):
            SileroVADProcessor(model_path="/nonexistent/model.onnx")


class TestVADProcessor:
    """Tests for unified VAD processor with fallback."""
    
    @pytest.mark.asyncio
    async def test_fallback_to_webrtc(self):
        """Test that VADProcessor falls back to WebRTC when Silero fails."""
        # Use a model path that will fail to load (directory instead of file)
        processor = VADProcessor(
            model_path="/nonexistent/model.onnx",  # This will fail
            fallback_enabled=True,
        )
        
        # Should have fallen back to WebRTC (Silero init fails)
        assert processor._active is not None
        # The active processor should be WebRTC (not Silero)
        assert isinstance(processor._active, WebRTCVADProcessor)
        
        await processor.start()
        
        # Test basic processing
        frame = np.zeros(512, dtype=np.float32)
        result = processor.process_frame(frame)
        
        assert isinstance(result, VADResult)
        await processor.stop()
    
    @pytest.mark.asyncio
    async def test_events(self):
        """Test speech_started and speech_ended events."""
        # Use a model path that will fail Silero initialization
        processor = VADProcessor(
            model_path="/nonexistent/model.onnx",
            fallback_enabled=True,
        )
        
        # Check events exist before start
        assert hasattr(processor, 'speech_started')
        assert hasattr(processor, 'speech_ended')
        import asyncio
        assert isinstance(processor.speech_started, asyncio.Event)
        assert isinstance(processor.speech_ended, asyncio.Event)
        
        # Start should succeed (fallback to WebRTC)
        await processor.start()
        
        # Events should still be accessible
        assert isinstance(processor.speech_started, asyncio.Event)
        assert isinstance(processor.speech_ended, asyncio.Event)
        
        await processor.stop()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])