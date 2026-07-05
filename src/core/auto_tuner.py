from typing import Dict, Any
from .interfaces import IAutoTuner, ASRResult
import random

class HillClimbingAutoTuner(IAutoTuner):
    def __init__(self, initial_params: Dict[str, Any]):
        self.current_params = initial_params.copy()
        self.best_score = -1.0
        self.best_params = initial_params.copy()
        
        # Weights for the objective function
        self.w_asr_confidence = 1.0
        self.w_word_rate = 0.5
        self.w_snr = 0.2
        self.w_energy = 0.1

    def evaluate(self, asr_result: ASRResult, features: Dict[str, float]) -> float:
        """
        Calculates the objective score combining ASR intelligibility and DSP features.
        Higher score means better intelligibility.
        """
        duration_sec = features.get("duration_sec", 1.0)
        if duration_sec <= 0:
            duration_sec = 1.0
            
        # 1. ASR Confidence
        confidence = asr_result.confidence_avg
        
        # 2. Word Rate
        word_count = len(asr_result.words)
        words_per_sec = word_count / duration_sec
        normalized_wps = min(words_per_sec / 3.0, 1.0)
        
        # 3. SNR (normalized 0-30 dB to 0-1)
        snr = features.get("snr_est", 0.0)
        normalized_snr = max(0.0, min(snr / 30.0, 1.0))
        
        # 4. Energy
        energy = features.get("energy", 0.0)
        energy_score = 1.0 if energy > 0.01 else 0.0
        
        score = (
            self.w_asr_confidence * confidence +
            self.w_word_rate * normalized_wps +
            self.w_snr * normalized_snr +
            self.w_energy * energy_score
        )
        
        if score > self.best_score:
            self.best_score = score
            self.best_params = self.current_params.copy()
            
        return score

    def get_next_parameters(self, current_score: float) -> Dict[str, Any]:
        """
        Implements a simple stochastic hill climbing search over SDR parameters.
        For Phase 2, we just perturb the frequency to find a better signal.
        """
        if current_score >= self.best_score:
            # We found a better peak or are staying at peak. Explore slightly.
            delta = random.choice([-0.1, 0.1, -0.5, 0.5])
        else:
            # Score dropped. Revert to best parameters and try a bigger jump to escape local minima.
            self.current_params = self.best_params.copy()
            delta = random.choice([-1.0, 1.0, -2.5, 2.5])
            
        if "frequency" in self.current_params:
            new_freq = self.current_params["frequency"] + delta
            # Ensure within typical HF bounds (100 kHz - 30000 kHz)
            self.current_params["frequency"] = max(100.0, min(30000.0, new_freq))
            
        return self.current_params
