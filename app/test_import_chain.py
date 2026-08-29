import time
import sounddevice as sd
import numpy as np


print("=== TEST 1: Solo sounddevice ===")

audio = sd.rec(
    int(2 * 16000),
    samplerate=16000,
    channels=1,
    dtype="float32",
    device=1,
)

sd.wait()

rms = np.sqrt(np.mean(np.square(audio)))

print(f"RMS={rms:.5f}")

print()


print(
    "=== TEST 2: Después de importar "
    "faster_whisper ==="
)

from faster_whisper import WhisperModel

whisper_model = WhisperModel(
    "small", device="cpu", compute_type="int8"
)

audio = sd.rec(
    int(2 * 16000),
    samplerate=16000,
    channels=1,
    dtype="float32",
    device=1,
)

sd.wait()

rms = np.sqrt(np.mean(np.square(audio)))

print(f"RMS={rms:.5f}")

print()


print(
    "=== TEST 3: Después de importar "
    "pyttsx3 e init ==="
)

import pyttsx3

engine = pyttsx3.init()

engine.setProperty("rate", 175)

engine.setProperty("volume", 1.0)

audio = sd.rec(
    int(2 * 16000),
    samplerate=16000,
    channels=1,
    dtype="float32",
    device=1,
)

sd.wait()

rms = np.sqrt(np.mean(np.square(audio)))

print(f"RMS={rms:.5f}")

print()


print(
    "=== TEST 4: Después de hablar ==="
)

engine.say("probando")

engine.runAndWait()

engine.stop()

time.sleep(0.3)

audio = sd.rec(
    int(2 * 16000),
    samplerate=16000,
    channels=1,
    dtype="float32",
    device=1,
)

sd.wait()

rms = np.sqrt(np.mean(np.square(audio)))

print(f"RMS={rms:.5f}")

print()


print(
    "=== TEST 5: Después de importar "
    "brain ==="
)

import sys

sys.path.insert(0, r"C:\Users\idelv\Desktop\DECIA_v2\app")

from brain.handlers import (
    quick_response,
    identity_response,
)

audio = sd.rec(
    int(2 * 16000),
    samplerate=16000,
    channels=1,
    dtype="float32",
    device=1,
)

sd.wait()

rms = np.sqrt(np.mean(np.square(audio)))

print(f"RMS={rms:.5f}")

print()


print("=== TEST 6: Segundo intento post-brain ===")

audio = sd.rec(
    int(2 * 16000),
    samplerate=16000,
    channels=1,
    dtype="float32",
    device=1,
)

sd.wait()

rms = np.sqrt(np.mean(np.square(audio)))

print(f"RMS={rms:.5f}")

print()
print("=== FIN ===")
