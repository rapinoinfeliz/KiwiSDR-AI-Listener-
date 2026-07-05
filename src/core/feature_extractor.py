import numpy as np
import scipy.signal
from typing import Dict
from .interfaces import IFeatureExtractor, AudioChunk

class BasicFeatureExtractor(IFeatureExtractor):
    def extract_features(self, audio: AudioChunk) -> Dict[str, float]:
        # Convert audio to float32
        data = np.frombuffer(audio.data, np.int16).astype(np.float32) / 32768.0
        
        # 0. Duration
        duration_sec = len(data) / audio.sample_rate if audio.sample_rate > 0 else 0.0
        
        if len(data) == 0:
            return {
                "energy": 0.0,
                "zero_crossing_rate": 0.0,
                "snr_est": 0.0,
                "spectral_centroid": 0.0,
                "duration_sec": 0.0
            }
            
        # 1. Energy (RMS)
        energy = np.sqrt(np.mean(data**2))
        
        # 2. Zero Crossing Rate
        zero_crossings = np.sum(np.abs(np.diff(np.signbit(data))))
        zcr = zero_crossings / len(data)
        
        # 3. Spectral Centroid
        fft_data = np.abs(np.fft.rfft(data))
        freqs = np.fft.rfftfreq(len(data), 1.0 / audio.sample_rate)
        
        if np.sum(fft_data) > 0:
            spectral_centroid = np.sum(freqs * fft_data) / np.sum(fft_data)
        else:
            spectral_centroid = 0.0
            
        # 4. Rough SNR estimation
        # Assuming speech has high energy variance and noise is the floor.
        # We estimate noise floor from the lowest 10% of energy frames (20ms frames).
        frame_len = int(audio.sample_rate * 0.02) 
        if len(data) >= frame_len:
            frames = np.array_split(data, len(data) // frame_len)
            frame_energies = [np.mean(f**2) for f in frames if len(f) > 0]
            if frame_energies:
                noise_floor = np.percentile(frame_energies, 10) + 1e-10
                signal_peak = np.percentile(frame_energies, 90) + 1e-10
                snr_est = 10 * np.log10(signal_peak / noise_floor)
            else:
                snr_est = 0.0
        else:
            snr_est = 0.0

        return {
            "energy": float(energy),
            "zero_crossing_rate": float(zcr),
            "snr_est": float(snr_est),
            "spectral_centroid": float(spectral_centroid),
            "duration_sec": float(duration_sec)
        }
