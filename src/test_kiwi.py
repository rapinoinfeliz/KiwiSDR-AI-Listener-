import wave
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.core.kiwi_adapter import KiwiSDRAdapter

def save_wav(filename: str, audio_data: bytes, sample_rate: int = 12000):
    with wave.open(filename, 'wb') as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2) # 16-bit
        wf.setframerate(sample_rate)
        wf.writeframes(audio_data)

if __name__ == "__main__":
    # We need a public KiwiSDR for testing.
    # We can use a random public one, for example:
    # 195.148.65.178:8073 (Finland) or others from rx.linkfanel.net
    # Let's try 69.27.184.62:8073 (KFS WebSDR CA) - wait, that's WebSDR, KiwiSDR has different IPs.
    # Let's use `kiwisdr.sk3w.se:8073` (Sweden) or `kiwisdr.com:8073` might not be a real receiver.
    # I'll use a widely known one: `sdr.hu` no longer exists.
    # Let's try `81.93.247.140:8073` (a random public kiwi usually online) or we can just try connecting and see.
    # Let's use a very popular one: e.g. w3hf.ddns.net:8073
    
    host = 'kiwisdr.sk3w.se'
    port = 8073
    freq = 10000.0 # 10 MHz AM WWV
    
    print(f"Connecting to {host}:{port} at {freq} kHz...")
    
    adapter = KiwiSDRAdapter(host=host, port=port, frequency=freq, mode='am')
    adapter.connect()
    
    print("Reading 5 seconds of audio...")
    # 12000 samples = 1 sec
    audio_chunk = adapter.read_audio(chunk_size=12000 * 5)
    
    print(f"Read {len(audio_chunk.data)} bytes.")
    
    wav_path = "test_output.wav"
    save_wav(wav_path, audio_chunk.data, audio_chunk.sample_rate)
    
    print(f"Saved to {wav_path}")
    
    sys.exit(0)
