from src.core.auto_tuner import HillClimbingAutoTuner
from src.core.interfaces import ASRResult

def test_tuner_evaluation():
    tuner = HillClimbingAutoTuner({"frequency": 10000.0})
    
    # Good signal
    good_asr = ASRResult(
        text="This is a clear voice test", 
        confidence_avg=0.9, 
        confidence_min=0.8,
        language="en",
        words=[{"word": "This"}, {"word": "is"}, {"word": "a"}, {"word": "clear"}, {"word": "voice"}, {"word": "test"}]
    )
    good_features = {"snr_est": 25.0, "energy": 0.5, "duration_sec": 5.0}
    good_score = tuner.evaluate(good_asr, good_features)
    
    # Bad signal
    bad_asr = ASRResult(
        text="", 
        confidence_avg=0.0, 
        confidence_min=0.0,
        language="en",
        words=[]
    )
    bad_features = {"snr_est": 0.0, "energy": 0.001, "duration_sec": 5.0}
    bad_score = tuner.evaluate(bad_asr, bad_features)
    
    assert good_score > bad_score, "Good signal should score higher than bad signal"

def test_tuner_threshold():
    tuner = HillClimbingAutoTuner({"frequency": 10000.0})
    
    # If score is > 0.7, it should return None to not retune
    next_params = tuner.get_next_parameters(0.8)
    assert next_params is None, "Tuner should not hop if score is above threshold"
    
    # If score is bad, it should hop
    next_params_bad = tuner.get_next_parameters(0.1)
    assert next_params_bad is not None
    assert next_params_bad["frequency"] != 10000.0
