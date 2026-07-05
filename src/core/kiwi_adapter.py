import os
import sys
import time
import threading
import queue
from typing import Dict, Any

# Add vendor path
vendor_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'vendor', 'kiwiclient'))
if vendor_path not in sys.path:
    sys.path.append(vendor_path)

from kiwi.client import KiwiSDRStream
from .interfaces import IRadioClient, AudioChunk

class AIKiwiStream(KiwiSDRStream):
    def __init__(self, *args, **kwargs):
        self.audio_queue = kwargs.pop('audio_queue', None)
        super().__init__(*args, **kwargs)

    def _setup_rx_params(self):
        self.set_name(self._options.user)
        self.set_mod(self._mode, self._options.lowcut, self._options.highcut)
        self.set_agc(True)
        # self.set_freq(self._freq) # Usually set by run() automatically or set_mod does it? Actually KiwiSDRStream's run() calls self.set_freq(self._freq) before this if self._freq is set.

    def _process_audio_samples(self, seq, samples, rssi, fmt):
        if self.audio_queue is not None:
            # samples is typically an array of shorts (16-bit PCM)
            # Ensure it is bytes
            data = samples.tobytes() if hasattr(samples, 'tobytes') else samples.tostring()
            self.audio_queue.put({
                'data': data,
                'timestamp': time.time(),
                'rssi': rssi
            })

class KiwiSDRAdapter(IRadioClient):
    def __init__(self, host: str, port: int, frequency: float, mode: str = 'am'):
        self.host = host
        self.port = int(port)
        self.frequency = float(frequency)
        self.mode = mode
        
        self.audio_queue = queue.Queue(maxsize=500)
        self.stream = AIKiwiStream(audio_queue=self.audio_queue)
        self.thread = None
        self._running = False

    def connect(self) -> None:
        class Options:
            def __init__(self, **kwargs):
                for k, v in kwargs.items():
                    setattr(self, k, v)
            def __getattr__(self, name):
                return False

        opt = Options(
            server_host=self.host,
            server_port=self.port,
            password="",
            user="AIListener",
            frequency=self.frequency,
            modulation=self.mode,
            lowcut=-5000 if self.mode == 'am' else 0,
            highcut=5000 if self.mode == 'am' else 3000,
            socket_timeout=10,
            tlimit_password=False,
            nolocal=False,
            admin=False
        )
        
        self.stream._options = opt
        self.stream._freq = self.frequency
        self.stream._mode = self.mode
        self.stream._start_ts = None
        self.stream._type = 'SND'
        # Do not call set_name here, it happens in _setup_rx_params inside run()
        self.stream._camp_chan = -1

        self._running = True
        self.thread = threading.Thread(target=self._run_stream, daemon=True)
        self.thread.start()
        # Give it a short moment to establish
        time.sleep(1)

    def disconnect(self) -> None:
        self._running = False
        if hasattr(self, 'stream') and self.stream:
            try:
                # Force socket close to break out of blocking recv
                if hasattr(self.stream, '_socket'):
                    self.stream._socket.close()
            except Exception as e:
                pass
                
    def _run_stream(self):
        try:
            self.stream.connect(self.host, self.port)
            self.stream.open()
            while self._running:
                self.stream.run()
        except Exception as e:
            print(f"Kiwi stream error: {e}")
        finally:
            self._running = False

    def set_parameters(self, params: Dict[str, Any]) -> None:
        if 'frequency' in params:
            self.frequency = float(params['frequency'])
            self.stream.set_freq(self.frequency)
            print(f"[Kiwi] Changed frequency to {self.frequency}")
        if 'mode' in params:
            self.mode = params['mode']
            lowcut = -5000 if self.mode == 'am' else 0
            highcut = 5000 if self.mode == 'am' else 3000
            self.stream.set_mod(self.mode, lowcut, highcut)
            print(f"[Kiwi] Changed mode to {self.mode}")

    def read_audio(self, chunk_size: int = 12000) -> AudioChunk:
        """
        Reads a chunk of audio.
        chunk_size: number of samples. For 12kHz, 12000 = 1 sec.
        Returns PCM 16-bit bytes.
        """
        buffer = bytearray()
        first_timestamp = None
        target_bytes = chunk_size * 2 # 16-bit = 2 bytes per sample
        
        while len(buffer) < target_bytes:
            try:
                msg = self.audio_queue.get(timeout=0.5)
                if first_timestamp is None:
                    first_timestamp = msg['timestamp']
                buffer.extend(msg['data'])
            except queue.Empty:
                if not self._running:
                    print("Stream stopped while reading.")
                    break
        
        return AudioChunk(
            data=bytes(buffer[:target_bytes]),
            sample_rate=12000,
            timestamp=first_timestamp or time.time()
        )
