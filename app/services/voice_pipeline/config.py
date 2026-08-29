# config.py - Configuration for Voice Pipeline

import os
from dataclasses import dataclass, field
from typing import Optional
from pathlib import Path


@dataclass
class VADConfig:
    """Voice Activity Detection configuration."""
    threshold: float = 0.5
    min_speech_ms: int = 250
    min_silence_ms: int = 100
    pre_roll_ms: int = 1000
    model_path: str = "models/silero_vad.onnx"
    fallback_enabled: bool = True


@dataclass
class STTConfig:
    """Speech-to-Text configuration."""
    model_size: str = "small"
    language: str = "es"
    beam_size: int = 5
    compute_type: str = "int8"


@dataclass
class TTSConfig:
    """Text-to-Speech configuration."""
    voice_id: str = "es_ES-carlfm-x_low"
    speed: float = 1.0
    chunk_strategy: str = "sentence"  # "sentence" | "word" | "semantic"
    fallback_enabled: bool = True


@dataclass
class AudioConfig:
    """Audio I/O configuration."""
    in_device: int = 1
    out_device: int = 0
    in_sample_rate: int = 16000
    out_sample_rate: int = 22050
    in_blocksize: int = 512
    out_blocksize: int = 1024


@dataclass
class PipelineConfig:
    """Main pipeline configuration."""
    # Sub-configs
    vad: VADConfig = field(default_factory=VADConfig)
    stt: STTConfig = field(default_factory=STTConfig)
    tts: TTSConfig = field(default_factory=TTSConfig)
    audio: AudioConfig = field(default_factory=AudioConfig)
    
    # Pipeline settings
    queue_maxsize: int = 10
    latency_budget_ms: int = 800
    
    # Feature flag
    enabled: bool = False
    
    @classmethod
    def from_env(cls, env_prefix: str = "DECIA_VOICE_") -> "PipelineConfig":
        """Load configuration from environment variables."""
        cfg = cls()
        
        # Feature flag
        cfg.enabled = os.getenv(f"{env_prefix}ENABLED", "0") == "1"
        
        # VAD
        cfg.vad.threshold = float(os.getenv(f"{env_prefix}VAD_THRESHOLD", "0.5"))
        cfg.vad.min_speech_ms = int(os.getenv(f"{env_prefix}VAD_MIN_SPEECH_MS", "250"))
        cfg.vad.min_silence_ms = int(os.getenv(f"{env_prefix}VAD_MIN_SILENCE_MS", "100"))
        cfg.vad.pre_roll_ms = int(os.getenv(f"{env_prefix}VAD_PRE_ROLL_MS", "1000"))
        cfg.vad.model_path = os.getenv(f"{env_prefix}VAD_MODEL_PATH", "models/silero_vad.onnx")
        cfg.vad.fallback_enabled = os.getenv(f"{env_prefix}VAD_FALLBACK", "1") == "1"
        
        # STT
        cfg.stt.model_size = os.getenv(f"{env_prefix}STT_MODEL_SIZE", "small")
        cfg.stt.language = os.getenv(f"{env_prefix}STT_LANGUAGE", "es")
        cfg.stt.beam_size = int(os.getenv(f"{env_prefix}STT_BEAM_SIZE", "5"))
        cfg.stt.compute_type = os.getenv(f"{env_prefix}STT_COMPUTE_TYPE", "int8")
        
        # TTS
        cfg.tts.voice_id = os.getenv(f"{env_prefix}TTS_VOICE_ID", "es_ES-carlfm-x_low")
        cfg.tts.speed = float(os.getenv(f"{env_prefix}TTS_SPEED", "1.0"))
        cfg.tts.chunk_strategy = os.getenv(f"{env_prefix}TTS_CHUNK_STRATEGY", "sentence")
        cfg.tts.fallback_enabled = os.getenv(f"{env_prefix}TTS_FALLBACK", "1") == "1"
        
        # Audio
        cfg.audio.in_device = int(os.getenv(f"{env_prefix}AUDIO_IN_DEVICE", "1"))
        cfg.audio.out_device = int(os.getenv(f"{env_prefix}AUDIO_OUT_DEVICE", "0"))
        cfg.audio.in_sample_rate = int(os.getenv(f"{env_prefix}AUDIO_IN_SR", "16000"))
        cfg.audio.out_sample_rate = int(os.getenv(f"{env_prefix}AUDIO_OUT_SR", "22050"))
        cfg.audio.in_blocksize = int(os.getenv(f"{env_prefix}AUDIO_IN_BLOCKSIZE", "512"))
        cfg.audio.out_blocksize = int(os.getenv(f"{env_prefix}AUDIO_OUT_BLOCKSIZE", "1024"))
        
        # Pipeline
        cfg.queue_maxsize = int(os.getenv(f"{env_prefix}QUEUE_MAXSIZE", "10"))
        cfg.latency_budget_ms = int(os.getenv(f"{env_prefix}LATENCY_BUDGET_MS", "800"))
        
        return cfg
    
    @classmethod
    def from_yaml(cls, path: str) -> "PipelineConfig":
        """Load configuration from YAML file (override env)."""
        import yaml
        with open(path, 'r') as f:
            data = yaml.safe_load(f)
        
        cfg = cls.from_env()
        
        # Override with YAML values
        if "vad" in data:
            for k, v in data["vad"].items():
                if hasattr(cfg.vad, k):
                    setattr(cfg.vad, k, v)
        if "stt" in data:
            for k, v in data["stt"].items():
                if hasattr(cfg.stt, k):
                    setattr(cfg.stt, k, v)
        if "tts" in data:
            for k, v in data["tts"].items():
                if hasattr(cfg.tts, k):
                    setattr(cfg.tts, k, v)
        if "audio" in data:
            for k, v in data["audio"].items():
                if hasattr(cfg.audio, k):
                    setattr(cfg.audio, k, v)
        if "pipeline" in data:
            for k, v in data["pipeline"].items():
                if hasattr(cfg, k):
                    setattr(cfg, k, v)
        
        return cfg
    
    def to_yaml(self, path: str) -> None:
        """Save configuration to YAML file."""
        import yaml
        data = {
            "vad": self.vad.__dict__,
            "stt": self.stt.__dict__,
            "tts": self.tts.__dict__,
            "audio": self.audio.__dict__,
            "pipeline": {
                "queue_maxsize": self.queue_maxsize,
                "latency_budget_ms": self.latency_budget_ms,
                "enabled": self.enabled,
            }
        }
        with open(path, 'w') as f:
            yaml.safe_dump(data, f, default_flow_style=False)


def load_config(config_path: Optional[str] = None) -> PipelineConfig:
    """
    Load configuration from environment and optional YAML file.
    
    Priority: YAML > env vars > defaults
    """
    cfg = PipelineConfig.from_env()
    
    if config_path and Path(config_path).exists():
        cfg = PipelineConfig.from_yaml(config_path)
    
    return cfg


# Default .env.example content
ENV_EXAMPLE = """# Voice Pipeline Configuration
# Copy to .env and modify as needed

# Feature flag
DECIA_VOICE_ENABLED=0

# VAD Settings
DECIA_VOICE_VAD_THRESHOLD=0.5
DECIA_VOICE_VAD_MIN_SPEECH_MS=250
DECIA_VOICE_VAD_MIN_SILENCE_MS=100
DECIA_VOICE_VAD_PRE_ROLL_MS=1000
DECIA_VOICE_VAD_MODEL_PATH=models/silero_vad.onnx
DECIA_VOICE_VAD_FALLBACK=1

# STT Settings
DECIA_VOICE_STT_MODEL_SIZE=small
DECIA_VOICE_STT_LANGUAGE=es
DECIA_VOICE_STT_BEAM_SIZE=5
DECIA_VOICE_STT_COMPUTE_TYPE=int8

# TTS Settings
DECIA_VOICE_TTS_VOICE_ID=es_ES-carlfm-x_low
DECIA_VOICE_TTS_SPEED=1.0
DECIA_VOICE_TTS_CHUNK_STRATEGY=sentence
DECIA_VOICE_TTS_FALLBACK=1

# Audio Settings
DECIA_VOICE_AUDIO_IN_DEVICE=1
DECIA_VOICE_AUDIO_OUT_DEVICE=0
DECIA_VOICE_AUDIO_IN_SR=16000
DECIA_VOICE_AUDIO_OUT_SR=22050
DECIA_VOICE_AUDIO_IN_BLOCKSIZE=512
DECIA_VOICE_AUDIO_OUT_BLOCKSIZE=1024

# Pipeline Settings
DECIA_VOICE_QUEUE_MAXSIZE=10
DECIA_VOICE_LATENCY_BUDGET_MS=800
"""