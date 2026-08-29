# audio_input.py - Audio input with sounddevice callback and pre-roll buffer

import asyncio
import janus
import sounddevice as sd
import numpy as np
from typing import Optional
from .ring_buffer import RingBuffer


class AudioInput:
    """
    Audio input handler using sounddevice callback mode.
    
    Captures audio from microphone in a separate callback thread,
    pushes frames to asyncio queue via janus.Queue, and maintains
    a ring buffer for pre-roll capture.
    """
    
    def __init__(
        self,
        device_id: int,
        sample_rate: int = 16000,
        blocksize: int = 512,           # 32ms @ 16kHz
        pre_roll_ms: int = 1000,
        channels: int = 1,
        dtype: np.dtype = np.float32,
    ):
        """
        Initialize audio input.
        
        Args:
            device_id: sounddevice input device index
            sample_rate: Sample rate in Hz (default: 16000)
            blocksize: Samples per callback (default: 512 = 32ms @ 16kHz)
            pre_roll_ms: Pre-roll buffer duration in ms (default: 1000)
            channels: Number of channels (default: 1)
            dtype: Sample dtype (default: float32)
        """
        self._device_id = device_id
        self._sample_rate = sample_rate
        self._blocksize = blocksize
        self._channels = channels
        self._dtype = dtype
        
        # Pre-roll buffer capacity in samples
        pre_roll_samples = int(sample_rate * pre_roll_ms / 1000)
        self._pre_roll_buffer = RingBuffer(
            capacity_samples=pre_roll_samples,
            channels=channels,
            dtype=dtype,
        )
        
        # Thread-safe queue for frames (callback thread -> asyncio)
        self._frame_queue: janus.Queue[np.ndarray] = janus.Queue(maxsize=100)
        
        # Stream state
        self._stream: Optional[sd.InputStream] = None
        self._running = False
        self._started_event = asyncio.Event()
        
    @property
    def sample_rate(self) -> int:
        return self._sample_rate
    
    @property
    def blocksize(self) -> int:
        return self._blocksize
    
    @property
    def channels(self) -> int:
        return self._channels
    
    @property
    def frames(self) -> "janus.Queue[np.ndarray]":
        """Async queue for audio frames (async side)."""
        return self._frame_queue.async_q
    
    @property
    def pre_roll_buffer(self) -> RingBuffer:
        """Ring buffer for pre-roll audio."""
        return self._pre_roll_buffer
    
    @property
    def running(self) -> bool:
        return self._running
    
    def get_pre_roll(self, duration_ms: int) -> np.ndarray:
        """
        Get pre-roll audio for barge-in preservation.
        
        Args:
            duration_ms: Duration in milliseconds
            
        Returns:
            Audio array of shape (n_samples, channels)
        """
        samples = int(self._sample_rate * duration_ms / 1000)
        return self._pre_roll_buffer.get_latest(samples)
    
    async def start(self) -> None:
        """Start audio input stream."""
        if self._running:
            return
            
        self._running = True
        self._started_event.clear()
        
        def callback(indata: np.ndarray, frames: int, time_info, status: sd.CallbackFlags) -> None:
            """Sounddevice callback (runs in audio callback thread)."""
            if status:
                # Log but don't block - callback must be fast
                pass
            
            # Copy data (callback buffer may be reused)
            frame = indata.copy()
            
            # Write to pre-roll buffer (thread-safe)
            self._pre_roll_buffer.write(frame)
            
            # Push to async queue (non-blocking)
            try:
                self._frame_queue.sync_q.put_nowait(frame)
            except janus.QueueFull:
                # Drop frame if queue full - don't block callback
                pass
        
        # Create and start stream
        self._stream = sd.InputStream(
            device=self._device_id,
            channels=self._channels,
            samplerate=self._sample_rate,
            blocksize=self._blocksize,
            dtype=self._dtype,
            callback=callback,
        )
        
        self._stream.start()
        
        # Wait a moment for stream to stabilize
        await asyncio.sleep(0.05)
        self._started_event.set()
    
    async def stop(self) -> None:
        """Stop audio input stream."""
        if not self._running:
            return
            
        self._running = False
        
        if self._stream is not None:
            self._stream.stop()
            self._stream.close()
            self._stream = None
        
        # Clear queue
        while not self._frame_queue.async_q.empty():
            try:
                self._frame_queue.async_q.get_nowait()
            except asyncio.QueueEmpty:
                break
        
        self._pre_roll_buffer.clear()
        self._started_event.clear()
    
    async def wait_started(self) -> None:
        """Wait for stream to be ready."""
        await self._started_event.wait()
    
    async def __aenter__(self) -> "AudioInput":
        await self.start()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        await self.stop()