# tests/test_pipeline.py - Unit tests for VoicePipeline

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "app"))

import asyncio
import numpy as np
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from app.services.voice_pipeline.pipeline import (
    VoicePipeline,
    PipelineConfig,
    PipelineState,
    PipelineMetrics,
    run_voice_conversation,
)
from app.services.voice_pipeline.vad_processor import VADResult
from app.services.voice_pipeline.stt_processor import STTResult


class TestPipelineConfig:
    """Tests for PipelineConfig."""
    
    def test_default_config(self):
        """Test default configuration."""
        config = PipelineConfig()
        assert config.vad.threshold == 0.5
        assert config.stt.model_size == "small"
        assert config.tts.voice_id == "es_ES-carlfm-x_low"
    
    def test_config_from_env(self):
        """Test loading config from environment."""
        import os
        os.environ["DECIA_VOICE_STT_MODEL_SIZE"] = "tiny"
        os.environ["DECIA_VOICE_TTS_VOICE_ID"] = "test_voice"
        
        config = PipelineConfig.from_env()
        assert config.stt.model_size == "tiny"
        assert config.tts.voice_id == "test_voice"
        
        # Cleanup
        del os.environ["DECIA_VOICE_STT_MODEL_SIZE"]
        del os.environ["DECIA_VOICE_TTS_VOICE_ID"]


class TestPipelineMetrics:
    """Tests for PipelineMetrics."""
    
    def test_default_metrics(self):
        """Test default metrics values."""
        metrics = PipelineMetrics()
        assert metrics.total_turns == 0
        assert metrics.total_latency_ms == 0.0
        assert metrics.barge_in_count == 0
        assert metrics.fallback_count == 0


class TestVoicePipeline:
    """Tests for VoicePipeline."""
    
    @pytest.fixture
    def mock_config(self):
        """Create a test configuration."""
        config = PipelineConfig()
        config.vad.threshold = 0.5
        config.vad.min_speech_ms = 100
        config.vad.min_silence_ms = 50
        config.stt.model_size = "tiny"
        config.tts.voice_id = "test"
        config.tts.fallback_enabled = True
        config.audio.in_device = 0
        config.audio.out_device = 0
        return config
    
    @pytest.fixture
    def mock_intent_layer(self):
        """Create a mock intent layer."""
        mock = MagicMock()
        mock.classify = MagicMock(return_value=MagicMock(
            intent="GREETING",
            confidence=0.9,
            entities={},
            matched_pattern="hola",
            candidates=[]
        ))
        return mock
    
    @pytest.mark.asyncio
    async def test_pipeline_start_stop(self, mock_config):
        """Test pipeline start and stop."""
        pipeline = VoicePipeline(config=mock_config)
        
        # Mock component start/stop
        with patch.object(pipeline, '_vad') as mock_vad, \
             patch.object(pipeline, '_stt') as mock_stt, \
             patch.object(pipeline, '_tts') as mock_tts, \
             patch.object(pipeline, '_audio_in') as mock_audio_in, \
             patch.object(pipeline, '_audio_out') as mock_audio_out:
            
            mock_vad.start = AsyncMock()
            mock_vad.stop = AsyncMock()
            mock_stt.start = AsyncMock()
            mock_stt.stop = AsyncMock()
            mock_tts.start = AsyncMock()
            mock_tts.stop = AsyncMock()
            mock_audio_in.start = AsyncMock()
            mock_audio_in.stop = AsyncMock()
            mock_audio_out.start = AsyncMock()
            mock_audio_out.stop = AsyncMock()
            
            await pipeline.start()
            assert pipeline.running == True
            assert pipeline.state == PipelineState.LISTENING
            
            await pipeline.stop()
            assert pipeline.running == False
            assert pipeline.state == PipelineState.IDLE
    
    @pytest.mark.asyncio
    async def test_pipeline_state_transitions(self, mock_config):
        """Test pipeline state transitions."""
        pipeline = VoicePipeline(config=mock_config)
        
        state_changes = []
        
        async def on_state_change(old, new):
            state_changes.append((old, new))
        
        pipeline.on_state_change = on_state_change
        
        with patch.object(pipeline, '_vad') as mock_vad, \
             patch.object(pipeline, '_stt') as mock_stt, \
             patch.object(pipeline, '_tts') as mock_tts, \
             patch.object(pipeline, '_audio_in') as mock_audio_in, \
             patch.object(pipeline, '_audio_out') as mock_audio_out:
            
            mock_vad.start = AsyncMock()
            mock_vad.stop = AsyncMock()
            mock_stt.start = AsyncMock()
            mock_stt.stop = AsyncMock()
            mock_tts.start = AsyncMock()
            mock_tts.stop = AsyncMock()
            mock_audio_in.start = AsyncMock()
            mock_audio_in.stop = AsyncMock()
            mock_audio_out.start = AsyncMock()
            mock_audio_out.stop = AsyncMock()
            
            await pipeline.start()
            await pipeline._transition_state(PipelineState.CAPTURING)
            await pipeline._transition_state(PipelineState.PROCESSING)
            await pipeline._transition_state(PipelineState.THINKING)
            await pipeline._transition_state(PipelineState.SPEAKING)
            await pipeline.stop()
            
            # Check state transitions were recorded (includes IDLE at stop)
            assert len(state_changes) == 6
            assert state_changes[0] == (PipelineState.IDLE, PipelineState.LISTENING)
            assert state_changes[1] == (PipelineState.LISTENING, PipelineState.CAPTURING)
            assert state_changes[2] == (PipelineState.CAPTURING, PipelineState.PROCESSING)
            assert state_changes[3] == (PipelineState.PROCESSING, PipelineState.THINKING)
            assert state_changes[4] == (PipelineState.THINKING, PipelineState.SPEAKING)
            assert state_changes[5] == (PipelineState.SPEAKING, PipelineState.IDLE)
    
    @pytest.mark.asyncio
    async def test_metrics_collection(self, mock_config):
        """Test metrics collection."""
        pipeline = VoicePipeline(config=mock_config)
        
        assert pipeline.metrics.total_turns == 0
        assert pipeline.metrics.barge_in_count == 0
        assert pipeline.metrics.fallback_count == 0
    
    @pytest.mark.asyncio
    async def test_context_manager(self, mock_config):
        """Test async context manager."""
        with patch.object(VoicePipeline, 'start', new_callable=AsyncMock) as mock_start, \
             patch.object(VoicePipeline, 'stop', new_callable=AsyncMock) as mock_stop:
            
            mock_start.side_effect = lambda: setattr(VoicePipeline, 'running', True)
            
            async with VoicePipeline(config=mock_config) as pipeline:
                assert pipeline.running == True
                mock_start.assert_called_once()
            
            mock_stop.assert_called_once()


class TestRunVoiceConversation:
    """Tests for run_voice_conversation convenience function."""
    
    @pytest.mark.asyncio
    async def test_run_voice_conversation(self):
        """Test run_voice_conversation function."""
        with patch('app.services.voice_pipeline.pipeline.VoicePipeline') as mock_pipeline_class:
            mock_pipeline = AsyncMock()
            mock_pipeline.__aenter__ = AsyncMock(return_value=mock_pipeline)
            mock_pipeline.__aexit__ = AsyncMock(return_value=None)
            mock_pipeline.running = True
            mock_pipeline_class.return_value = mock_pipeline
            
            callbacks = {
                'on_transcription': AsyncMock(),
                'on_response': AsyncMock(),
                'on_barge_in': AsyncMock(),
            }
            
            # Mock the while loop to exit quickly
            async def mock_sleep(duration):
                mock_pipeline.running = False
            
            with patch('asyncio.sleep', side_effect=mock_sleep):
                await run_voice_conversation(
                    on_transcription=callbacks['on_transcription'],
                    on_response=callbacks['on_response'],
                    on_barge_in=callbacks['on_barge_in'],
                )
            
            mock_pipeline_class.assert_called_once()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])