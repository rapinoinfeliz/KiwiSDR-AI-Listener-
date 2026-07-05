import numpy as np
import scipy.signal
from faster_whisper import WhisperModel
from .interfaces import IASREngine, AudioChunk, ASRResult

class FasterWhisperEngine(IASREngine):
    def __init__(self, model_size="tiny", device="cpu", compute_type="int8"):
        """
        Initializes the Faster Whisper engine.
        Using 'tiny' model and 'cpu' by default for compatibility in the sandbox.
        """
        print(f"Loading Whisper model '{model_size}' on {device}...")
        self.model = WhisperModel(model_size, device=device, compute_type=compute_type)
        print("Whisper model loaded.")

    def transcribe(self, audio: AudioChunk) -> ASRResult:
        # Convert PCM 16-bit bytes to float32 numpy array normalized between -1.0 and 1.0
        audio_data = np.frombuffer(audio.data, np.int16).astype(np.float32) / 32768.0
        
        # Whisper requires 16000Hz sample rate.
        if audio.sample_rate != 16000:
            num_samples = int(len(audio_data) * 16000 / audio.sample_rate)
            audio_data = scipy.signal.resample(audio_data, num_samples)

        # Transcribe with word timestamps to get confidence per word
        segments, info = self.model.transcribe(audio_data, beam_size=5, word_timestamps=True)
        
        full_text = ""
        words = []
        confidences = []
        
        for segment in segments:
            full_text += segment.text + " "
            if segment.words:
                for word in segment.words:
                    words.append({
                        "word": word.word,
                        "start": word.start,
                        "end": word.end,
                        "probability": word.probability
                    })
                    confidences.append(word.probability)
                
        avg_conf = sum(confidences) / len(confidences) if confidences else 0.0
        min_conf = min(confidences) if confidences else 0.0
        
        return ASRResult(
            text=full_text.strip(),
            confidence_avg=avg_conf,
            confidence_min=min_conf,
            words=words,
            language=info.language
        )
