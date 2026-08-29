# ring_buffer.py - Thread-safe circular buffer for pre-roll audio

import threading
from typing import Optional
import numpy as np


class RingBuffer:
    """
    Thread-safe circular buffer for pre-roll audio storage.
    
    Uses numpy array as backend with thread-safe read/write operations.
    Designed for audio callback thread (writer) and asyncio event loop (reader).
    """
    
    def __init__(
        self,
        capacity_samples: int,
        channels: int = 1,
        dtype: np.dtype = np.float32,
    ):
        """
        Initialize ring buffer.
        
        Args:
            capacity_samples: Maximum number of samples to store
            channels: Number of audio channels (default: 1 for mono)
            dtype: NumPy dtype for samples (default: float32)
        """
        if capacity_samples <= 0:
            raise ValueError("capacity_samples must be positive")
        if channels <= 0:
            raise ValueError("channels must be positive")
            
        self._capacity = capacity_samples
        self._channels = channels
        self._dtype = dtype
        
        # Pre-allocate buffer
        self._buffer = np.zeros(
            (capacity_samples, channels),
            dtype=dtype
        )
        
        # Thread synchronization
        self._lock = threading.RLock()
        self._write_pos = 0
        self._available = 0
        
    @property
    def capacity(self) -> int:
        """Total capacity in samples."""
        return self._capacity
    
    @property
    def channels(self) -> int:
        """Number of audio channels."""
        return self._channels
    
    @property
    def dtype(self) -> np.dtype:
        """Sample dtype."""
        return self._dtype
    
    @property
    def available_samples(self) -> int:
        """Number of samples currently available for reading."""
        with self._lock:
            return self._available
    
    @property
    def free_samples(self) -> int:
        """Number of free samples available for writing."""
        with self._lock:
            return self._capacity - self._available
    
    def write(self, data: np.ndarray) -> int:
        """
        Write samples to buffer.
        
        Args:
            data: Array of shape (n_samples, channels) or (n_samples,) for mono
            
        Returns:
            Number of samples actually written
        """
        if data.size == 0:
            return 0
            
        # Ensure correct shape
        if data.ndim == 1:
            data = data.reshape(-1, 1)
        elif data.ndim != 2:
            raise ValueError("data must be 1D or 2D array")
            
        if data.shape[1] != self._channels:
            raise ValueError(
                f"Expected {self._channels} channels, got {data.shape[1]}"
            )
            
        # Convert dtype if needed
        if data.dtype != self._dtype:
            data = data.astype(self._dtype, copy=False)
            
        n_samples = data.shape[0]
        
        with self._lock:
            # If data exceeds capacity, keep only the last capacity samples
            if n_samples >= self._capacity:
                data = data[-self._capacity:]
                n_samples = self._capacity
            
            # Handle wrap-around
            end_pos = self._write_pos + n_samples
            if end_pos <= self._capacity:
                # Single contiguous write
                self._buffer[self._write_pos:end_pos] = data
            else:
                # Wrap around: write in two parts
                first_part = self._capacity - self._write_pos
                self._buffer[self._write_pos:] = data[:first_part]
                self._buffer[:n_samples - first_part] = data[first_part:]
                
            self._write_pos = (self._write_pos + n_samples) % self._capacity
            self._available = min(self._available + n_samples, self._capacity)
            
            return n_samples
    
    def read(self, num_samples: int) -> np.ndarray:
        """
        Read oldest samples from buffer (FIFO).
        
        Args:
            num_samples: Number of samples to read
            
        Returns:
            Array of shape (n_read, channels) - may be fewer than requested
        """
        if num_samples <= 0:
            return np.zeros((0, self._channels), dtype=self._dtype)
            
        with self._lock:
            readable = min(num_samples, self._available)
            if readable == 0:
                return np.zeros((0, self._channels), dtype=self._dtype)
                
            # Calculate read positions
            read_pos = (self._write_pos - self._available) % self._capacity
            end_pos = read_pos + readable
            
            if end_pos <= self._capacity:
                # Single contiguous read
                result = self._buffer[read_pos:end_pos].copy()
            else:
                # Wrap around
                first_part = self._capacity - read_pos
                result = np.vstack([
                    self._buffer[read_pos:],
                    self._buffer[:readable - first_part]
                ])
                
            self._available -= readable
            return result
    
    def get_latest(self, num_samples: int) -> np.ndarray:
        """
        Get most recent samples (for pre-roll).
        
        Args:
            num_samples: Number of samples to get
            
        Returns:
            Array of shape (min(num_samples, available), channels)
        """
        if num_samples <= 0:
            return np.zeros((0, self._channels), dtype=self._dtype)
            
        with self._lock:
            readable = min(num_samples, self._available)
            if readable == 0:
                return np.zeros((0, self._channels), dtype=self._dtype)
                
            # Start from most recent and go backwards
            end_pos = self._write_pos
            start_pos = (end_pos - readable) % self._capacity
            
            if start_pos < end_pos:
                # Contiguous
                result = self._buffer[start_pos:end_pos].copy()
            else:
                # Wrap around
                result = np.vstack([
                    self._buffer[start_pos:],
                    self._buffer[:end_pos]
                ])
                
            return result
    
    def clear(self) -> None:
        """Clear buffer, reset to empty state."""
        with self._lock:
            self._write_pos = 0
            self._available = 0
    
    def __len__(self) -> int:
        """Return number of available samples."""
        return self.available_samples
    
    def __repr__(self) -> str:
        return (
            f"RingBuffer(capacity={self._capacity}, "
            f"available={self._available}, "
            f"channels={self._channels})"
        )