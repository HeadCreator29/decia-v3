# voice_pipeline - Modern Voice Pipeline for DECIA v3
# Streaming VAD -> STT -> Intent -> LLM -> TTS with barge-in support

__version__ = "0.1.0"

from .config import PipelineConfig, load_config
from .ring_buffer import RingBuffer
from .audio_input import AudioInput
from .audio_output import AudioOutput
from .vad_processor import VADProcessor, VADResult
from .stt_processor import STTProcessor, STTProcessorStreaming, STTResult
from .tts_processor import TTSProcessor, PiperTTS, Pyttsx3TTS, text_chunker, TTSChunk
from .pipeline import VoicePipeline, PipelineConfig, PipelineState, PipelineMetrics, run_voice_conversation

__all__ = [
    "PipelineConfig",
    "load_config",
    "RingBuffer",
    "AudioInput",
    "AudioOutput",
    "VADProcessor",
    "VADResult",
    "STTProcessor",
    "STTProcessorStreaming",
    "STTResult",
    "TTSProcessor",
    "PiperTTS",
    "Pyttsx3TTS",
    "text_chunker",
    "TTSChunk",
    "VoicePipeline",
    "PipelineConfig",
    "PipelineState",
    "PipelineMetrics",
    "run_voice_conversation",
]