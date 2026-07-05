import time
import threading
import sys
from typing import Optional, Callable
from .queue import MemoryQueue
from .workers import RadioWorker, InferenceWorker
from .mock_adapter import MockRadioClient
from .discovery import KiwiSDRDiscoveryService
from .scheduler import BanditScheduler
from .asr_engine import FasterWhisperEngine
from .feature_extractor import BasicFeatureExtractor
from .auto_tuner import HillClimbingAutoTuner
from .database import save_intercept

class EngineController:
    def __init__(self, use_mock: bool = False, event_callback: Optional[Callable] = None):
        self.use_mock = use_mock
        self.event_callback = event_callback
        self.queue = MemoryQueue(maxsize=10)
        self.running = False
        
        self.radio_worker: Optional[RadioWorker] = None
        self.inference_worker: Optional[InferenceWorker] = None
        self.monitor_thread: Optional[threading.Thread] = None
        
        self.scheduler: Optional[BanditScheduler] = None
        self.current_node = None
        
        # Engines (created once)
        self.asr = FasterWhisperEngine(model_size="tiny", device="cpu")
        self.extractor = BasicFeatureExtractor()
        self.tuner = HillClimbingAutoTuner(initial_params={"frequency": 10000.0})

    def emit(self, event_type: str, payload: dict):
        if self.event_callback:
            self.event_callback(event_type, payload)

    def start(self):
        if self.running:
            return
            
        self.running = True
        self.emit("status", {"state": "starting"})
        
        if self.use_mock:
            self.current_node = type("Node", (), {"host": "mock", "port": 0, "name": "Mock"})()
            radio = MockRadioClient(frequency=10000.0)
        else:
            from .kiwi_adapter import KiwiSDRAdapter
            discovery = KiwiSDRDiscoveryService()
            nodes = discovery.fetch_nodes()
            
            if not nodes:
                self.emit("status", {"state": "error", "message": "No nodes found. Falling back to Mock"})
                self.use_mock = True
                self.current_node = type("Node", (), {"host": "mock", "port": 0, "name": "Mock"})()
                radio = MockRadioClient(frequency=10000.0)
            else:
                self.scheduler = BanditScheduler(nodes)
                self.current_node = self.scheduler.get_best_node()
                radio = KiwiSDRAdapter(host=self.current_node.host, port=self.current_node.port, frequency=10000.0)
                self.emit("node", {"host": self.current_node.host, "name": self.current_node.name})

        self.radio_worker = RadioWorker(radio=radio, queue=self.queue)
        self.inference_worker = InferenceWorker(asr=self.asr, extractor=self.extractor, tuner=self.tuner, queue=self.queue)
        
        self.radio_worker.start()
        self.inference_worker.start()
        
        self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.monitor_thread.start()
        
        self.emit("status", {"state": "running"})

    def stop(self):
        self.running = False
        if self.radio_worker:
            self.radio_worker.stop()
        if self.inference_worker:
            self.inference_worker.stop()
        self.emit("status", {"state": "stopped"})

    def _monitor_loop(self):
        while self.running:
            time.sleep(0.5)
            
            # Consume events for UI
            ui_event = self.queue.pop("events")
            if ui_event:
                # Add current node info if missing
                if "node_name" not in ui_event and self.current_node:
                    ui_event["node_name"] = self.current_node.name
                    
                self.emit("ui_event", ui_event)
                
                # Save to DB if it's a transcription
                if ui_event.get("type") == "transcription" and ui_event.get("text"):
                    save_intercept(
                        frequency=ui_event.get("frequency", 10000.0),
                        node_name=ui_event.get("node_name", "Unknown"),
                        text=ui_event.get("text"),
                        translation=ui_event.get("translation", ""),
                        score=ui_event.get("score", 0.0),
                        confidence=ui_event.get("confidence", 0.0)
                    )

            # Consume metrics for Scheduler
            metric_msg = self.queue.pop("metrics")
            if metric_msg and not self.use_mock and self.scheduler and self.current_node:
                if 'score' in metric_msg:
                    self.scheduler.update_node_score(self.current_node.host, self.current_node.port, metric_msg['score'])

            if self.radio_worker and not self.radio_worker.is_alive():
                self.emit("status", {"state": "warning", "message": "Radio connection lost."})
                if not self.use_mock and self.scheduler and self.current_node:
                    self.scheduler.update_node_score(self.current_node.host, self.current_node.port, reward=0.0)
                    
                    self.current_node = self.scheduler.get_best_node()
                    self.emit("node", {"host": self.current_node.host, "name": self.current_node.name})
                    
                    from .kiwi_adapter import KiwiSDRAdapter
                    radio = KiwiSDRAdapter(host=self.current_node.host, port=self.current_node.port, frequency=10000.0)
                    self.radio_worker = RadioWorker(radio=radio, queue=self.queue)
                    self.radio_worker.start()
                else:
                    self.running = False
                    self.emit("status", {"state": "stopped"})
                    break
                    
            if self.inference_worker and not self.inference_worker.is_alive():
                self.running = False
                self.emit("status", {"state": "error", "message": "Inference worker died."})
                break
