# KiwiSDR AI Listener

An autonomous, AI-driven closed-loop controller for KiwiSDR networks.

This project transforms public KiwiSDR receivers into an intelligent High-Frequency (HF) radio monitoring network. It uses real-time Digital Signal Processing (DSP) and Automatic Speech Recognition (ASR) to evaluate signal quality and intelligibility, actively tuning the radio to find voice communications across the HF spectrum.

## Architecture

The system is built on a highly modular, decoupled architecture separating IO-bound radio streaming from CPU/GPU-bound neural network inference.

1.  **RadioWorker**: Continuously streams audio from a KiwiSDR WebSocket and dispatches 16-bit PCM chunks into a memory queue. It listens for control messages (e.g., frequency hops) and applies them dynamically without dropping the connection.
2.  **InferenceWorker**: Consumes audio chunks, extracts mathematical features (SNR, Zero-Crossing Rate, Spectral Energy), and runs transcription via Faster-Whisper.
3.  **AutoTuner (Hill Climbing)**: Acts as the system's brain. It calculates an Objective Score based on Whisper's transcription confidence and the DSP features. If the score is low (e.g., static noise or silence), the tuner commands the radio to hop frequencies using a hill-climbing algorithm.
4.  **Discovery & BanditScheduler**: Provides high availability. It fetches a global list of public KiwiSDRs and uses a Multi-Armed Bandit (UCB1) algorithm to dynamically switch between SDR nodes if a connection drops or if propagation conditions degrade.
5.  **LLM Translator**: Pluggable interface via LiteLLM to translate transcribed intercepts into a target language in real-time.

## Installation

Ensure you have Python 3.12+ installed. This project uses `uv` for fast dependency management.

```bash
# Clone the repository
git clone https://github.com/rapinoinfeliz/KiwiSDR-AI-Listener-.git
cd KiwiSDR-AI-Listener-

# Run the project directly (uv will automatically sync dependencies)
uv run python main.py
```

## Usage

Start the autonomous listener:

```bash
uv run python main.py
```

By default, the system will:
1. Fetch a list of available public KiwiSDRs.
2. Connect to the most reliable node.
3. Tune to a default frequency (e.g., 10000.0 kHz).
4. Extract features, transcribe audio, and automatically hop frequencies if no human voice is detected.

### Local Testing / Mock Mode

If your network blocks non-standard ports (like 8073) or you want to test the inference pipeline without internet access, run the system in mock mode. The mock adapter generates synthetic static noise and clear tones to simulate tuning.

```bash
uv run python main.py --mock
```

## Structure

*   `src/core/interfaces.py`: Core system contracts (IQueue, IAutoTuner, IRadioClient, etc).
*   `src/core/kiwi_adapter.py`: Wrapper for the KiwiSDR WebSocket client.
*   `src/core/asr_engine.py`: Faster-Whisper integration.
*   `src/core/feature_extractor.py`: DSP signal analysis.
*   `src/core/auto_tuner.py`: Hill-Climbing objective function and frequency controller.
*   `src/core/scheduler.py`: Multi-Armed Bandit node selection.
*   `src/core/discovery.py`: Fetches and parses public SDR directories.
*   `src/core/translator.py`: LiteLLM integration for text translation.
*   `main.py`: The entrypoint that wires the dependencies and manages the worker threads.

## Disclaimer

This project connects to public, amateur-operated KiwiSDR nodes. Please be respectful of their bandwidth and concurrent user limits. This tool is intended for educational purposes, radio propagation research, and AI/DSP experimentation.
