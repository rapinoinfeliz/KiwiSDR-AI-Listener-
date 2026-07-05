import wave
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.core.asr_engine import FasterWhisperEngine
from src.core.interfaces import AudioChunk

def load_wav(filename: str) -> AudioChunk:
    with wave.open(filename, 'rb') as wf:
        sample_rate = wf.getframerate()
        data = wf.readframes(wf.getnframes())
        return AudioChunk(data=data, sample_rate=sample_rate, timestamp=0.0)

if __name__ == "__main__":
    audio_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'dataset', 'tone_440hz.wav')
    print(f"Loading {audio_path}...")
    audio = load_wav(audio_path)
    
    engine = FasterWhisperEngine(model_size="tiny", device="cpu")
    print("Transcribing...")
    
    result = engine.transcribe(audio)
    print("----- RESULT -----")
    print(f"Text: {result.text}")
    print(f"Language: {result.language}")
    print(f"Avg Confidence: {result.confidence_avg:.3f}")
    print(f"Min Confidence: {result.confidence_min:.3f}")
    print(f"Words count: {len(result.words)}")
