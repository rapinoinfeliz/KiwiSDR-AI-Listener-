import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.core.feature_extractor import BasicFeatureExtractor
from src.core.auto_tuner import HillClimbingAutoTuner
from src.core.interfaces import AudioChunk, ASRResult

def test_tuner():
    extractor = BasicFeatureExtractor()
    tuner = HillClimbingAutoTuner(initial_params={"frequency": 10000.0})
    
    print("--- Test 1: Silence ---")
    # Fake audio (1 sec of silence)
    dummy_audio = AudioChunk(data=b'\x00'*32000, sample_rate=16000, timestamp=0.0)
    features = extractor.extract_features(dummy_audio)
    print("Features:", features)
    
    asr_res = ASRResult(
        text="",
        confidence_avg=0.0,
        confidence_min=0.0,
        words=[],
        language="en"
    )
    
    score1 = tuner.evaluate(asr_res, features)
    print("Score:", score1)
    
    next_params = tuner.get_next_parameters(score1)
    print("Next Params:", next_params)
    
    print("\n--- Test 2: Good Speech ---")
    features["energy"] = 0.5
    features["snr_est"] = 15.0
    asr_res.confidence_avg = 0.8
    asr_res.words = [{"word": "hello", "start":0, "end":0.2, "probability":0.9} for _ in range(3)]
    
    score2 = tuner.evaluate(asr_res, features)
    print("Score:", score2)
    
    next_params2 = tuner.get_next_parameters(score2)
    print("Next Params 2:", next_params2)

if __name__ == "__main__":
    test_tuner()
