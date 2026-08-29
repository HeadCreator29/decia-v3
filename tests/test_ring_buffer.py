# tests/test_ring_buffer.py - Unit tests for RingBuffer

import threading
import time
import numpy as np
import pytest
from app.services.voice_pipeline.ring_buffer import RingBuffer


class TestRingBuffer:
    """Tests for RingBuffer thread-safe circular buffer."""
    
    def test_basic_write_read(self):
        """Test basic write and read operations."""
        buf = RingBuffer(capacity_samples=100, channels=1)
        
        data = np.arange(10, dtype=np.float32).reshape(-1, 1)
        written = buf.write(data)
        assert written == 10
        assert buf.available_samples == 10
        
        read_data = buf.read(10)
        assert read_data.shape == (10, 1)
        np.testing.assert_array_equal(read_data.flatten(), data.flatten())
        assert buf.available_samples == 0
    
    def test_write_exceeds_capacity(self):
        """Test writing more than capacity keeps last samples."""
        buf = RingBuffer(capacity_samples=10, channels=1)
        
        data = np.arange(20, dtype=np.float32).reshape(-1, 1)
        written = buf.write(data)
        assert written == 10  # Only capacity worth
        assert buf.available_samples == 10
        
        read_data = buf.read(10)
        # Should get the LAST 10 samples (10-19)
        np.testing.assert_array_equal(read_data.flatten(), np.arange(10, 20, dtype=np.float32))
    
    def test_wrap_around(self):
        """Test buffer wrap-around behavior."""
        buf = RingBuffer(capacity_samples=10, channels=1)
        
        # Fill buffer
        buf.write(np.arange(10, dtype=np.float32).reshape(-1, 1))
        assert buf.available_samples == 10
        
        # Read 5
        read1 = buf.read(5)
        assert buf.available_samples == 5
        np.testing.assert_array_equal(read1.flatten(), np.arange(5, dtype=np.float32))
        
        # Write 5 more (should wrap)
        buf.write(np.arange(10, 15, dtype=np.float32).reshape(-1, 1))
        assert buf.available_samples == 10
        
        # Read all - should get 5-9 then 10-14
        read2 = buf.read(10)
        expected = np.concatenate([np.arange(5, 10), np.arange(10, 15)]).astype(np.float32)
        np.testing.assert_array_equal(read2.flatten(), expected)
    
    def test_concurrent_write_read(self):
        """Test thread-safe concurrent write/read."""
        buf = RingBuffer(capacity_samples=1000, channels=1)
        errors = []
        
        def writer():
            try:
                for i in range(100):
                    data = np.full((10, 1), float(i), dtype=np.float32)
                    buf.write(data)
                    time.sleep(0.001)
            except Exception as e:
                errors.append(e)
        
        def reader():
            try:
                total_read = 0
                while total_read < 1000:
                    read_data = buf.read(50)
                    total_read += len(read_data)
                    time.sleep(0.002)
            except Exception as e:
                errors.append(e)
        
        t1 = threading.Thread(target=writer)
        t2 = threading.Thread(target=reader)
        t1.start()
        t2.start()
        t1.join()
        t2.join()
        
        assert len(errors) == 0, f"Thread errors: {errors}"
    
    def test_get_latest(self):
        """Test get_latest for pre-roll."""
        buf = RingBuffer(capacity_samples=100, channels=1)
        
        buf.write(np.arange(20, dtype=np.float32).reshape(-1, 1))
        
        # Get latest 5
        latest = buf.get_latest(5)
        assert latest.shape == (5, 1)
        np.testing.assert_array_equal(latest.flatten(), np.arange(15, 20, dtype=np.float32))
        
        # Request more than available
        latest = buf.get_latest(200)
        assert latest.shape == (20, 1)
    
    def test_clear(self):
        """Test buffer clear."""
        buf = RingBuffer(capacity_samples=10, channels=1)
        buf.write(np.arange(5, dtype=np.float32).reshape(-1, 1))
        assert buf.available_samples == 5
        
        buf.clear()
        assert buf.available_samples == 0
        assert buf.read(10).shape == (0, 1)
    
    def test_multi_channel(self):
        """Test multi-channel support."""
        buf = RingBuffer(capacity_samples=10, channels=2)
        
        # Stereo data
        data = np.column_stack([
            np.arange(5, dtype=np.float32),
            np.arange(5, 10, dtype=np.float32)
        ])
        buf.write(data)
        
        read_data = buf.read(5)
        assert read_data.shape == (5, 2)
        np.testing.assert_array_equal(read_data[:, 0], np.arange(5, dtype=np.float32))
        np.testing.assert_array_equal(read_data[:, 1], np.arange(5, 10, dtype=np.float32))
    
    def test_dtype_conversion(self):
        """Test automatic dtype conversion."""
        buf = RingBuffer(capacity_samples=10, channels=1, dtype=np.float32)
        
        # Write int16 data
        data = np.arange(5, dtype=np.int16).reshape(-1, 1)
        buf.write(data)
        
        read_data = buf.read(5)
        assert read_data.dtype == np.float32
        np.testing.assert_array_equal(read_data.flatten(), np.arange(5, dtype=np.float32))


if __name__ == "__main__":
    pytest.main([__file__, "-v"])