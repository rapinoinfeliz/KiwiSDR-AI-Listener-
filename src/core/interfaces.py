from abc import ABC, abstractmethod
from typing import Any, Dict, List
from pydantic import BaseModel

class AudioChunk(BaseModel):
    data: bytes
    sample_rate: int
    timestamp: float

class ASRResult(BaseModel):
    text: str
    confidence_avg: float
    confidence_min: float
    words: List[Dict[str, Any]]
    language: str
    
class IFeatureExtractor(ABC):
    @abstractmethod
    def extract_features(self, audio: AudioChunk) -> Dict[str, float]:
        """Extract features like SNR, energy, spectral centroid, etc."""
        pass

class IASREngine(ABC):
    @abstractmethod
    def transcribe(self, audio: AudioChunk) -> ASRResult:
        """Transcribe audio and return text with confidence metrics."""
        pass

class IAutoTuner(ABC):
    @abstractmethod
    def evaluate(self, asr_result: ASRResult, features: Dict[str, float]) -> float:
        """Calculate the objective function score."""
        pass
        
    @abstractmethod
    def get_next_parameters(self, current_score: float) -> Dict[str, Any]:
        """Get the next set of SDR parameters to apply (e.g., via Hill Climbing)."""
        pass

class IRadioClient(ABC):
    @abstractmethod
    def connect(self) -> None:
        pass
        
    @abstractmethod
    def set_parameters(self, params: Dict[str, Any]) -> None:
        """Set SDR parameters like frequency, mode, passband."""
        pass
        
    @abstractmethod
    def read_audio(self, chunk_size: int) -> AudioChunk:
        pass

class IQueue(ABC):
    @abstractmethod
    def push(self, topic: str, message: Any) -> None:
        pass
        
    @abstractmethod
    def pop(self, topic: str) -> Any:
        pass

class SDRNode(BaseModel):
    host: str
    port: int
    score: float = 0.5
    visits: int = 0
    name: str = "Unknown"

class IDiscoveryService(ABC):
    @abstractmethod
    def fetch_nodes(self) -> List[SDRNode]:
        """Fetch a list of available SDR nodes from a public directory."""
        pass

class IScheduler(ABC):
    @abstractmethod
    def get_best_node(self) -> SDRNode:
        """Select the next node to connect to using Multi-Armed Bandit."""
        pass
        
    @abstractmethod
    def update_node_score(self, host: str, port: int, reward: float) -> None:
        """Update the internal score of a node based on the reward (intelligibility)."""
        pass

class ITranslator(ABC):
    @abstractmethod
    def translate(self, text: str, source_lang: str, target_lang: str) -> str:
        """Translate transcribed text into the target language."""
        pass
