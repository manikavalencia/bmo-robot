# 🤖 BMO Desktop AI Assistant

An interactive, physical desktop assistant inspired by **BMO from Adventure Time**, running locally on a Raspberry Pi 5 with offline speech recognition, local quantized LLMs, and real-time state animations.

## 🚀 Key Features & Tech Stack
* **Hardware:** Raspberry Pi 5, Adafruit Audio HAT, Custom 3D-printed enclosure.
* **UI & Rendering:** Python, `pygame` (dynamic idle and animated talking face loops).
* **Speech-to-Text (STT):** Vosk (offline speech recognition engine).
* **Language Model (LLM):** Ollama (`llama3.2:latest`) running locally on device.
* **Text-to-Speech (TTS):** Piper TTS + SoX audio volume normalization.
* **CAD Design:** 3D enclosure modeled in OnShape.

## 🛠️ System Architecture
1. **Audio Capture:** Background `sounddevice` stream downsamples 48kHz audio to 16kHz for low latency.
2. **STT:** Vosk processes waveform audio offline and outputs finalized transcription text.
3. **LLM Inference:** Prompt is fed into local Ollama model history context to stream responses.
4. **Output Pipeline:** Piper TTS synthesizes the response to ALSA audio output while Pygame updates dynamic facial state animations in sync.

## 📦 Requirements & Usage
```bash
git clone [https://github.com/manikavalencia/bmo-robot.git](https://github.com/manikavalencia/bmo-robot.git)
cd bmo-robot
pip install -r requirements.txt
python bmo.py
