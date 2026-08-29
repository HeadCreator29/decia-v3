# audio_output.py - Audio output with sounddevice callback and barge-in support

import asyncio
import janus
import sounddevice as sd
import numpy as np
from typing import Optional


class AudioOutput:
    """
    Audio output handler using sounddevice callback mode.
    
    Plays audio chunks from asyncio queue via callback thread,
    supports immediate stop for barge-in interruption.
    """
    
    def __init__(
        self,
        device_id: int,
        sample_rate: int = 22050,
        blocksize: int = 1024,
        channels: int = 1,
        dtype: np.dtype = np.float32,
        queue_maxsize: int = 50,
    ):
        """
        Initialize audio output.
        
        Args:
            device_id: sounddevice output device index
            sample_rate: Sample rate in Hz (default: 22050 for Piper)
            blocksize: Samples per callback (default: 1024)
            channels: Number of channels (default: 1)
            dtype: Sample dtype (default: float32)
            queue_maxsize: Max chunks in queue (backpressure)
        """
        self._device_id = device_id
        self._sample_rate = sample_rate
        self._blocksize = blocksize
        self._channels = channels
        self._dtype = dtype
        
        # Async queue for audio chunks (asyncio -> callback thread)
        self._chunk_queue: janus.Queue[np.ndarray] = janus.Queue(maxsize=queue_maxsize)
        
        # Stream state
        self._stream: Optional[sd.OutputStream] = None
        self._running = False
        self._stopped_event = asyncio.Event()
        
        # Metrics
        self._buffer_underruns = 0
        self._chunks_played = 0
        self._stopped_for_barge_in = False
        
        # Pre-allocate silence buffer for underruns
        self._silence_buffer = np.zeros(
            (blocksize, 1), dtype=np.float32
        )
    
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
    def buffer_underruns(self) -> int:
        return self._buffer_underruns
    
    @property
    def chunks_played(self) -> int:
        return self._chunks_played
    
    @property
    def stopped_for_barge_in(self) -> bool:
        return self._stopped_for_barge_in
    
    async def write(self, chunk: np.ndarray) -> None:
        """
        Write audio chunk to playback queue.
        
        Args:
            chunk: Audio array (n_samples, channels) or (n_samples,) for mono
            
        Blocks if queue is full (backpressure).
        """
        if not self._running:
            raise RuntimeError("AudioOutput not running")
        
        # Ensure correct shape
        if chunk.ndim == 1:
            chunk = chunk.reshape(-1, 1)
        elif chunk.ndim != 2:
            raise ValueError("chunk must be 1D or 2D array")
        
        if chunk.shape[1] != self._channels:
            raise ValueError(
                f"Expected {self._channels} channels, got {chunk.shape[1]}"
            )
        
        # Convert dtype if needed
        if chunk.dtype != np.float32:
            chunk = chunk.astype(np.float32, copy=False)
        
        # Wait for queue space (backpressure)
        await self._chunk_queue.async_q.put(chunk)
    
    def stop_immediate(self) -> None:
        """
        Stop playback immediately for barge-in.
        
        Clears queue, signals callback to stop, safe to call from any thread.
        """
        self._stopped_for_barge_in = True
        
        # Clear queue (thread-safe)
        while True:
            try:
                self._chunk_queue.sync_q.get_nowait()
            except Exception:
                break
        
        # Signal callback to stop
        self._stopped_event.set()
    
    async def start(self) -> None:
        """Start audio output stream."""
        if self._running:
            return
            
        self._running = True
        self._stopped_for_barge_in = False
        self._stopped_event.clear()
        self._buffer_underruns = 0
        self._chunks_played = 0
        
        def callback(outdata: np.ndarray, frames: int, time_info, status: sd.CallbackFlags) -> None:
            """Sounddevice callback (runs in audio callback thread)."""
            if status:
                # Log but don't block
                pass
            
            # Check for immediate stop (barge-in)
            if self._stopped_event.is_set():
                outdata.fill(0)
                return
            
            # Try to get chunk from queue (non-blocking)
            try:
                chunk = self._chunk_queue.sync_q.get_nowait()
            except Exception:
                # Queue empty - underrun
                self._buffer_underruns += 1
                outdata[:] = self._silence_buffer[:frames]
                return
            
            # Handle chunk size mismatch
            chunk_frames = chunk.shape[0]
            if chunk_frames >= frames:
                # Chunk larger or equal - use first frames, put remainder back
                outdata[:] = chunk[:frames]
                if chunk_frames > frames:
                    remainder = chunk[frames:]
                    try:
                        self._chunk_queue.sync_q.put_nowait(remainder)
                    except Exception:
                        pass  # Queue full, drop remainder
            else:
                # Chunk smaller - pad with silence
                outdata[:chunk_frames] = chunk
                outdata[chunk_frames:] = 0
            
            self._chunks_played += 1
        
        # Create and start stream
        self._stream = sd.OutputStream(
            device=self._device_id,
            channels=self._channels,
            samplerate=self._sample_rate,
            blocksize=self._blocksize,
            dtype=np.float32,
            callback=callback,
        )
        
        self._stream.start()
        await asyncio.sleep(0.05)  # Let stream stabilize
    
    async def stop(self) -> None:
        """Stop audio output stream gracefully."""
        if not self._running:
            return
            
        self._running = False
        self._stopped_event.set()
        
        # Wait for callback to finish current buffer
        await asyncio.sleep(0.1)
        
        if self._stream is not None:
            self._stream.stop()
            self._stream.close()
            self._stream = None
        
        # Clear queue
        while True:
            try:
                self._chunk_queue.sync_q.get_nowait()
            except Exception:
                break
        
        self._stopped_for_barge_in = False
        self._stopped_event.clear()
    
    async def drain(self) -> None:
        """Wait for all queued chunks to play."""
        while not self._chunk_queue.async_q.empty():
            await asyncio.sleep(0.01)
    
    async def __aenter__(self) -> "AudioOutput":
        await self.start()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        await self.stop()