import json
import os
import re
import subprocess
import sys
import threading
import numpy as np
import ollama
import pygame
import sounddevice as sd
from vosk import KaldiRecognizer, Model

# ==========================================
# CONFIGURATION & INITIALIZATION
# ==========================================

DISPLAY_SIZE = (800, 460)
IDLE_ANIMATION_SPEED = 32
TALKING_ANIMATION_SPEED = 6
HISTORY_FILE = "data.json"

OLLAMA_MODEL = "llama3.2:latest"
VOSK_MODEL_PATH = "model/vosk-model-small-en-us-0.15"

VOSK_SAMPLE_RATE = 16000
HARDWARE_SAMPLE_RATE = 48000

# Initialize Pygame
pygame.init()
screen = pygame.display.set_mode(DISPLAY_SIZE)
clock = pygame.time.Clock()

# Load BMO Face Textures (Idle & Talking)
idle_image_paths = [
    "faces/bmo01.jpg",
    "faces/bmo00.jpg",
    "faces/bmo04.jpg",
    "faces/bmo06.jpg",
]
talking_image_paths = [
    "faces/bmo_talk1.jpg",  # Make sure to add these when you design them!
    "faces/bmo_talk2.jpg",
]

def load_frames(paths):
    frames = []
    for path in paths:
        if os.path.exists(path):
            img = pygame.image.load(path).convert()
            frames.append(pygame.transform.scale(img, DISPLAY_SIZE))
        else:
            # Fallback to first idle frame if talking frames aren't created yet
            if idle_image_paths and os.path.exists(idle_image_paths[0]):
                img = pygame.image.load(idle_image_paths[0]).convert()
                frames.append(pygame.transform.scale(img, DISPLAY_SIZE))
    return frames

idle_frames = load_frames(idle_image_paths)
talking_frames = load_frames(talking_image_paths) if all(os.path.exists(p) for p in talking_image_paths) else idle_frames

current_frame = 0
frame_counter = 0
is_speaking = False  # State flag for talking animation

# Ensure History File Exists
if not os.path.exists(HISTORY_FILE) or os.stat(HISTORY_FILE).st_size == 0:
    with open(HISTORY_FILE, "w") as f:
        json.dump(
            [{"role": "system", "content": "You are BMO from Adventure Time."}],
            f,
            indent=4,
        )

# Initialize Vosk Model
if not os.path.exists(VOSK_MODEL_PATH):
    print(f"Error: Vosk model path not found at {VOSK_MODEL_PATH}")
    sys.exit(1)

vosk_model = Model(VOSK_MODEL_PATH)
recognizer = KaldiRecognizer(vosk_model, VOSK_SAMPLE_RATE)


# ==========================================
# AUDIO & THREADED SPEECH PROCESSING
# ==========================================

def bmo_speak_threaded(text: str):
    """Generates audio with Piper, normalizes with SoX, and plays in a background thread."""
    global is_speaking
    is_speaking = True
    
    try:
        output_wav = "/tmp/bmo_speech.wav"
        quiet_wav = "/tmp/bmo_quiet.wav"

        # 1. Generate speech via Piper TTS
        piper_cmd = f'echo "{text}" | piper --model bmo_voices/bmo.onnx --output_file {output_wav}'
        subprocess.run(piper_cmd, shell=True, check=True)

        # 2. Lower volume using SoX (10% volume)
        subprocess.run(f"sox {output_wav} {quiet_wav} vol 0.1", shell=True)

        # 3. Play audio through ALSA device
        subprocess.run(f"aplay -D plughw:2,0 {quiet_wav}", shell=True)
        
    except Exception as e:
        print(f"Error during speech synthesis/playback: {e}")
    finally:
        is_speaking = False

def clean_speech(text: str):
    """Strips stage directions and parenthetical tags, then triggers threaded speech."""
    text = re.sub(r'\*.*?\*', '', text)
    text = re.sub(r'\(.*?\)', '', text)
    text = re.sub(r'\s+', ' ', text).strip()

    if text:
        speech_thread = threading.Thread(target=bmo_speak_threaded, args=(text,))
        speech_thread.daemon = True
        speech_thread.start()


# ==========================================
# OLLAMA CONVERSATION ENGINE
# ==========================================

def process_ai_message(user_input: str):
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, "r") as file:
            try:
                history = json.load(file)
            except json.JSONDecodeError:
                history = []
    else:
        history = []

    history.append({"role": "user", "content": user_input})

    recent_context = history[-4:] if len(history) > 4 else history[1:]
    messages = [
        {"role": "system", "content": "Talk like BMO from Adventure Time."}
    ] + recent_context

    stream = ollama.chat(model=OLLAMA_MODEL, messages=messages, stream=True)
    full_response = ""

    for chunk in stream:
        content = chunk["message"]["content"]
        full_response += content

    clean_speech(full_response)

    # FIXED: Role must be 'assistant' for Ollama history compatibility
    history.append({"role": "assistant", "content": full_response})

    with open(HISTORY_FILE, "w") as file:
        json.dump(history, file, indent=4)


# ==========================================
# MICROPHONE CALLBACK & STT ENGINE
# ==========================================

def mic_callback(indata, frames, time, status):
    audio_array = np.frombuffer(indata, dtype=np.int16)
    num_samples = int(len(audio_array) * VOSK_SAMPLE_RATE / HARDWARE_SAMPLE_RATE)

    resampled = np.interp(
        np.linspace(0, len(audio_array), num_samples, endpoint=False),
        np.arange(len(audio_array)),
        audio_array,
    ).astype(np.int16)

    if recognizer.AcceptWaveform(resampled.tobytes()):
        result = json.loads(recognizer.Result())
        text = result.get('text', '').strip()
        if text:
            print(f"[FINAL]: {text}")
            process_ai_message(text)
    else:
        partial = json.loads(recognizer.PartialResult())
        partial_text = partial.get("partial", "").strip()
        if partial_text:
            print(f"[PARTIAL]: {partial_text}")


# ==========================================
# MAIN EXECUTION LOOP
# ==========================================

def main():
    global frame_counter, current_frame

    try:
        stream = sd.RawInputStream(
            samplerate=HARDWARE_SAMPLE_RATE,
            blocksize=8000,
            dtype='int16',
            channels=1,
            callback=mic_callback
        )
        stream.start()
        print("BMO Voice System online and listening with talking animations...")
    except Exception as e:
        print(f"Error starting audio stream: {e}")
        return

    running = True
    while running:
        try:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False

            # Switch between talking and idle frames/speeds based on state
            active_frames = talking_frames if is_speaking else idle_frames
            current_speed = TALKING_ANIMATION_SPEED if is_speaking else IDLE_ANIMATION_SPEED

            frame_counter += 1
            if frame_counter >= current_speed:
                frame_counter = 0
                current_frame = (current_frame + 1) % len(active_frames)

            screen.fill((0, 0, 0))
            screen.blit(active_frames[current_frame], (0, 0))
            pygame.display.flip()
            clock.tick(45)

        except KeyboardInterrupt:
            running = False

    stream.stop()
    stream.close()
    pygame.quit()
    sys.exit(0)


if __name__ == "__main__":
    main()
