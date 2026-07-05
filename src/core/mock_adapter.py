import time
import queue
import numpy as np
from typing import Dict, Any
from .interfaces import IRadioClient, AudioChunk

class MockRadioClient(IRadioClient):
    """
    Mock adapter that generates fake audio and simulates a radio connection.
    Useful for testing the inference and control loops without a real internet SDR.
    """
    def __init__(self, frequency: float = 10000.0):
        self.frequency = frequency
        self.mode = 'am'
        self._running = False
        self.start_time = 0.0

    def connect(self) -> None:
        print("[MockRadio] Connecting to simulated radio...")
        time.sleep(1)
        self._running = True
        self.start_time = time.time()
        print("[MockRadio] Connected!")

    def disconnect(self) -> None:
        print("[MockRadio] Disconnecting...")
        self._running = False

    def set_parameters(self, params: Dict[str, Any]) -> None:
        if 'frequency' in params:
            self.frequency = float(params['frequency'])
            print(f"[MockRadio] Changed frequency to {self.frequency}")
        if 'mode' in params:
            self.mode = params['mode']
            print(f"[MockRadio] Changed mode to {self.mode}")

    def read_audio(self, chunk_size: int = 60000) -> AudioChunk:
        """Simulate reading audio. 12000 samples = 1 sec."""
        if not self._running:
            raise Exception("Stream is closed")
            
        duration = chunk_size / 12000.0
        time.sleep(duration) # simulate blocking read
        
        t = np.linspace(0, duration, chunk_size, endpoint=False)
        
        # Let's say there is a strong signal at 10000.5 kHz
        target_freq = 10000.5
        distance = abs(self.frequency - target_freq)
        
        if distance < 0.1:
            # Tuned! Generate a clean tone (400 Hz)
            signal = np.sin(2 * np.pi * 400 * t) * 0.8
            signal += np.random.normal(0, 0.1, chunk_size)
            rssi = -60
        else:
            # Static noise
            signal = np.random.normal(0, 0.5, chunk_size)
            rssi = -100
            
        # Clip
        signal = np.clip(signal, -1.0, 1.0)
        
        # Convert to 16-bit PCM bytes
        audio_data = (signal * 32767).astype(np.int16).tobytes()
        
        return AudioChunk(
            data=audio_data,
            sample_rate=12000,
            timestamp=time.time(),
            rssi=rssi
        )
