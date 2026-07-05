import threading
import time
from .interfaces import IRadioClient, IASREngine, IAutoTuner, IFeatureExtractor, IQueue, AudioChunk

class RadioWorker(threading.Thread):
    def __init__(self, radio: IRadioClient, queue: IQueue):
        super().__init__()
        self.radio = radio
        self.queue = queue
        self.running = False
        self.daemon = True # Dies when main thread dies

    def run(self):
        self.running = True
        print("[RadioWorker] Starting radio connection...")
        # Start connection asynchronously if possible, or blocking depending on the adapter.
        # Wait, the adapter runs in its own threads internally. Connect will start it.
        try:
            self.radio.connect()
        except Exception as e:
            print(f"[RadioWorker] Connection failed: {e}")
            self.running = False
            return
        
        # Give it a moment to stabilize
        time.sleep(2)
        
        while self.running:
            # 1. Check for control messages
            control_msg = self.queue.pop("control")
            if control_msg:
                print(f"[RadioWorker] Applying new parameters: {control_msg}")
                self.radio.set_parameters(control_msg)
            
            # 2. Read audio (e.g. 5 seconds)
            # This blocks until 5 seconds of audio are read
            try:
                audio_chunk = self.radio.read_audio(chunk_size=5)
                if audio_chunk and len(audio_chunk.data) > 0:
                    self.queue.push("audio", audio_chunk)
                else:
                    if hasattr(self.radio, '_running') and not self.radio._running:
                        print("[RadioWorker] Radio connection died. Stopping worker.")
                        break
                    time.sleep(0.5)
            except Exception as e:
                print(f"[RadioWorker] Error reading audio: {e}")
                time.sleep(1)
                
    def stop(self):
        self.running = False

class InferenceWorker(threading.Thread):
    def __init__(self, 
                 asr: IASREngine, 
                 extractor: IFeatureExtractor, 
                 tuner: IAutoTuner, 
                 queue: IQueue):
        super().__init__()
        self.asr = asr
        self.extractor = extractor
        self.tuner = tuner
        self.queue = queue
        self.running = False
        self.daemon = True

    def run(self):
        self.running = True
        print("[InferenceWorker] Starting inference loop...")
        
        while self.running:
            audio_chunk = self.queue.pop("audio")
            
            if not audio_chunk:
                continue
                
            print(f"\n[InferenceWorker] Processing {len(audio_chunk.data)} bytes of audio...")
            
            # 1. Extract Features
            features = self.extractor.extract_features(audio_chunk)
            print(f"[InferenceWorker] Features: SNR={features.get('snr_est', 0):.1f}dB, ZCR={features.get('zero_crossing_rate', 0):.3f}")
            
            # 2. ASR Transcribe
            asr_res = self.asr.transcribe(audio_chunk)
            print(f"[InferenceWorker] ASR: '{asr_res.text}' (Conf: {asr_res.confidence_avg:.2f})")
            
            # 3. Evaluate Objective Function
            score = self.tuner.evaluate(asr_res, features)
            print(f"[InferenceWorker] Objective Score: {score:.2f}")
            
            # 4. Get next params and push to control queue
            next_params = self.tuner.get_next_parameters(score)
            self.queue.push("control", next_params)
            
    def stop(self):
        self.running = False
