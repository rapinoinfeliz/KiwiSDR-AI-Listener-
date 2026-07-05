import numpy as np
import scipy.io.wavfile as wavfile
import os

def generate_tone(filename, freq=440, duration=5, sample_rate=12000):
    t = np.linspace(0, duration, sample_rate * duration, endpoint=False)
    signal = 0.5 * np.sin(2 * np.pi * freq * t)
    # Add some noise
    signal += np.random.normal(0, 0.05, signal.shape)
    
    # Clip and convert
    signal = np.clip(signal, -1.0, 1.0)
    audio_data = (signal * 32767).astype(np.int16)
    
    wavfile.write(filename, sample_rate, audio_data)
    print(f"Generated {filename}")

def generate_noise(filename, duration=5, sample_rate=12000):
    signal = np.random.normal(0, 0.5, sample_rate * duration)
    signal = np.clip(signal, -1.0, 1.0)
    audio_data = (signal * 32767).astype(np.int16)
    
    wavfile.write(filename, sample_rate, audio_data)
    print(f"Generated {filename}")

def main():
    os.makedirs("dataset", exist_ok=True)
    generate_tone("dataset/tone_440hz.wav", 440)
    generate_noise("dataset/noise_static.wav")
    generate_tone("dataset/bbc.wav", 1000) # Mock
    generate_tone("dataset/ham_ssb.wav", 800) # Mock
    generate_tone("dataset/numbers_am.wav", 600) # Mock

if __name__ == "__main__":
    main()
