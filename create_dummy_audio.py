import numpy as np
import wave
import os

sample_rate = 12000
duration = 2.0  # seconds
frequency = 440.0  # Hz

t = np.linspace(0, duration, int(sample_rate * duration), endpoint=False)
audio = 0.5 * np.sin(2 * np.pi * frequency * t)

# Convert to 16-bit PCM
audio_integers = np.int16(audio * 32767)

dataset_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'dataset')
os.makedirs(dataset_dir, exist_ok=True)
filename = os.path.join(dataset_dir, 'tone_440hz.wav')

with wave.open(filename, 'wb') as wf:
    wf.setnchannels(1)
    wf.setsampwidth(2)
    wf.setframerate(sample_rate)
    wf.writeframes(audio_integers.tobytes())

print(f"Created {filename}")
