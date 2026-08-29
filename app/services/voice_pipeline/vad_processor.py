# vad_processor.py - Voice Activity Detection with Silero VAD (ONNX) and WebRTC fallback

import asyncio
import os
from dataclasses import dataclass
from typing import Optional
import numpy as np

try:
    import onnxruntime as ort
    ONNX_AVAILABLE = True
except ImportError:
    ONNX_AVAILABLE = False

try:
    import webrtcvad
    WEBRTC_AVAILABLE = True
except ImportError:
    WEBRTC_AVAILABLE = False


@dataclass
class VADResult:
    """Result of VAD processing for a single frame."""
    probability: float          # 0.0-1.0 speech probability
    is_speech: bool             # Thresholded decision
    speech_start: bool          # Rising edge detected
    speech_end: bool            # Falling edge detected


class BaseVADProcessor:
    """Base class for VAD processors."""
    
    def __init__(
        self,
        threshold: float = 0.5,
        min_speech_ms: int = 250,
        min_silence_ms: int = 100,
        sample_rate: int = 16000,
    ):
        self.threshold = threshold
        self.min_speech_frames = max(1, int(min_speech_ms * sample_rate / 1000 / 512))
        self.min_silence_frames = max(1, int(min_silence_ms * sample_rate / 1000 / 512))
        self.sample_rate = sample_rate
        
        self._speech_started = asyncio.Event()
        self._speech_ended = asyncio.Event()
        self._was_speech = False
        self._speech_frame_count = 0
        self._silence_frame_count = 0
    
    @property
    def speech_started(self) -> asyncio.Event:
        return self._speech_started
    
    @property
    def speech_ended(self) -> asyncio.Event:
        return self._speech_ended
    
    def _update_state(self, is_speech: bool) -> tuple[bool, bool]:
        """Update internal state machine, return (speech_start, speech_end)."""
        speech_start = False
        speech_end = False
        
        if is_speech:
            self._silence_frame_count = 0
            self._speech_frame_count += 1
            
            if not self._was_speech and self._speech_frame_count >= self.min_speech_frames:
                speech_start = True
                self._was_speech = True
                self._speech_started.set()
        else:
            self._speech_frame_count = 0
            self._silence_frame_count += 1
            
            if self._was_speech and self._silence_frame_count >= self.min_silence_frames:
                speech_end = True
                self._was_speech = False
                self._speech_ended.set()
        
        return speech_start, speech_end
    
    def reset(self) -> None:
        """Reset internal state."""
        self._was_speech = False
        self._speech_frame_count = 0
        self._silence_frame_count = 0
        self._speech_started.clear()
        self._speech_ended.clear()


class SileroVADProcessor(BaseVADProcessor):
    """Silero VAD using ONNX runtime."""
    
    def __init__(
        self,
        threshold: float = 0.5,
        min_speech_ms: int = 250,
        min_silence_ms: int = 100,
        model_path: str = "models/silero_vad.onnx",
        sample_rate: int = 16000,
    ):
        super().__init__(threshold, min_speech_ms, min_silence_ms, sample_rate)
        self.model_path = model_path
        self._session: Optional[ort.InferenceSession] = None
        self._input_name: Optional[str] = None
        self._output_name: Optional[str] = None
        self._state: np.ndarray = np.zeros((2, 1, 128), dtype=np.float32)  # Silero state
        self._sr: np.ndarray = np.array([sample_rate], dtype=np.int64)
        
        # Validate model path exists at init time
        if not os.path.exists(model_path):
            raise FileNotFoundError(f"Silero VAD model not found: {model_path}")
    
    async def start(self) -> None:
        """Load and warmup ONNX model."""
        if not ONNX_AVAILABLE:
            raise RuntimeError("onnxruntime not available")
        
        self._session = ort.InferenceSession(
            self.model_path,
            providers=['CPUExecutionProvider']
        )
        self._input_name = self._session.get_inputs()[0].name
        self._output_name = self._session.get_outputs()[0].name
        
        # Warmup
        dummy = np.zeros((1, 512), dtype=np.float32)
        _ = self._run_inference(dummy)
    
    def _run_inference(self, frame: np.ndarray) -> float:
        """Run Silero VAD inference on single frame."""
        # Silero expects: input (1, 512), state (2, 1, 128), sr (1,)
        inputs = {
            self._session.get_inputs()[0].name: frame.astype(np.float32),
            self._session.get_inputs()[1].name: self._state.astype(np.float32),
            self._session.get_inputs()[2].name: self._sr,
        }
        outputs = self._session.run(None, inputs)
        prob = float(outputs[0][0][0])
        self._state = outputs[1]  # Update state
        return prob
    
    def process_frame(self, frame: np.ndarray) -> VADResult:
        """
        Process 512-sample frame @ 16kHz.
        Returns VADResult with probability and state flags.
        """
        # Ensure correct shape (512 samples, mono)
        if frame.ndim == 2:
            frame = frame.flatten()
        if frame.shape[0] != 512:
            raise ValueError(f"Expected 512 samples, got {frame.shape[0]}")
        
        # Run inference
        prob = self._run_inference(frame.astype(np.float32).reshape(1, 512))
        is_speech = prob >= self.threshold
        speech_start, speech_end = self._update_state(is_speech)
        
        return VADResult(
            probability=prob,
            is_speech=is_speech,
            speech_start=speech_start,
            speech_end=speech_end,
        )
    
    async def stop(self) -> None:
        """Cleanup."""
        pass
    
    def reset(self) -> None:
        super().reset()
        self._state = np.zeros((2, 1, 128), dtype=np.float32)


class WebRTCVADProcessor(BaseVADProcessor):
    """WebRTC VAD fallback processor."""
    
    def __init__(
        self,
        threshold: float = 0.5,
        min_speech_ms: int = 250,
        min_silence_ms: int = 100,
        model_path: str = "models/silero_vad.onnx",
        sample_rate: int = 16000,
    ):
        # WebRTC processes 320-sample chunks (20ms @ 16kHz)
        # Override frame duration for correct frame counting
        super().__init__(threshold, min_speech_ms, min_silence_ms, sample_rate)
        
        # Override frame counts for WebRTC's 20ms frames (320 samples @ 16kHz)
        # Each process_frame call processes one 320-sample chunk (20ms)
        self.min_speech_frames = max(1, int(min_speech_ms * sample_rate / 1000 / 320))
        self.min_silence_frames = max(1, int(min_silence_ms * sample_rate / 1000 / 320))
        
        if not WEBRTC_AVAILABLE:
            raise RuntimeError("webrtcvad not available")
        self._vad = webrtcvad.Vad(2)
        self._frame_size = int(sample_rate * 0.016)  # 16ms frames for WebRTC (256 samples @ 16kHz)
        # Ensure frame_size is valid for WebRTC (10/20/30ms at 16kHz)
        # WebRTC supports 10ms (160), 20ms (320), 30ms (480) at 16kHz
        self._frame_size = 320  # 20ms @ 16kHz
    
    def process_frame(self, frame: np.ndarray) -> VADResult:
        """Process frame using WebRTC VAD."""
        if frame.ndim == 2:
            frame = frame.flatten()
        
        # Check frame energy - if too low, treat as silence
        frame_energy = np.mean(frame ** 2)
        if frame_energy < 1e-10:  # Very low energy = silence
            prob = 0.0
            is_speech = False
        else:
            # Process 20ms chunks (320 samples @ 16kHz)
            chunk_size = self._frame_size
            speech_votes = 0
            total_chunks = 0
            
            for i in range(0, len(frame), chunk_size):
                chunk = frame[i:i+chunk_size]
                if len(chunk) == chunk_size:
                    # Convert to int16 bytes for WebRTC
                    chunk_int16 = (chunk * 32767).astype(np.int16).tobytes()
                    try:
                        if self._vad.is_speech(chunk_int16, self.sample_rate):
                            speech_votes += 1
                    except Exception:
                        pass
                    total_chunks += 1
            
            prob = speech_votes / total_chunks if total_chunks > 0 else 0.0
            is_speech = prob >= self.threshold
        
        speech_start, speech_end = self._update_state(is_speech)
        
        return VADResult(
            probability=prob,
            is_speech=is_speech,
            speech_start=speech_start,
            speech_end=speech_end,
        )
    
    async def start(self) -> None:
        pass
    
    async def stop(self) -> None:
        pass


class VADProcessor:
    """
    Unified VAD processor with Silero primary and WebRTC fallback.
    """
    
    def __init__(
        self,
        threshold: float = 0.5,
        min_speech_ms: int = 250,
        min_silence_ms: int = 100,
        model_path: str = "models/silero_vad.onnx",
        sample_rate: int = 16000,
        fallback_enabled: bool = True,
    ):
        self.fallback_enabled = fallback_enabled
        
        # Try Silero first
        self._silero: Optional[SileroVADProcessor] = None
        self._webrtc: Optional[WebRTCVADProcessor] = None
        self._active: Optional[BaseVADProcessor] = None
        
        # Try to initialize Silero
        try:
            self._silero = SileroVADProcessor(
                threshold=threshold,
                min_speech_ms=min_speech_ms,
                min_silence_ms=min_silence_ms,
                model_path=model_path,
                sample_rate=sample_rate,
            )
        except Exception as e:
            print(f"[VAD] Silero failed to initialize: {e}")
            self._silero = None
        
        # Initialize WebRTC fallback if enabled
        if fallback_enabled:
            try:
                self._webrtc = WebRTCVADProcessor(
                    threshold=threshold,
                    min_speech_ms=min_speech_ms,
                    min_silence_ms=min_silence_ms,
                    sample_rate=sample_rate,
                )
            except Exception as e:
                print(f"[VAD] WebRTC VAD failed to initialize: {e}")
                self._webrtc = None
        
        # Set active processor (prefer Silero, fallback to WebRTC)
        self._active = self._silero if self._silero else self._webrtc
        
        if self._active is None:
            raise RuntimeError("No VAD processor available (Silero and WebRTC both failed)")
    
    @property
    def speech_started(self) -> asyncio.Event:
        return self._active.speech_started if self._active else asyncio.Event()
    
    @property
    def speech_ended(self) -> asyncio.Event:
        return self._active.speech_ended if self._active else asyncio.Event()
    
    async def start(self) -> None:
        if self._active:
            await self._active.start()
    
    async def stop(self) -> None:
        if self._active:
            await self._active.stop()
    
    def process_frame(self, frame: np.ndarray) -> VADResult:
        """Process frame with active VAD processor."""
        if self._active is None:
            raise RuntimeError("VAD processor not initialized")
        return self._active.process_frame(frame)
    
    def reset(self) -> None:
        if self._active:
            self._active.reset()
    
    def switch_to_fallback(self) -> bool:
        """Switch to WebRTC fallback if available."""
        if self._webrtc and self._active != self._webrtc:
            self._active = self._webrtc
            print("[VAD] Switched to WebRTC fallback")
            return True
        return False