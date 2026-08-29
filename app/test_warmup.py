"""Test: warm-up capture before chunked loop."""
import time
import numpy as np
import sounddevice as sd

SAMPLE_RATE = 16000
MICROPHONE_DEVICE = 1
VOICE_THRESHOLD = 0.025


def test_no_warmup():
    print("\n=== TEST 1: Sin calentamiento ===")
    chunk_size = int(SAMPLE_RATE * 0.1)
    for i in range(30):
        chunk = sd.rec(
            chunk_size,
            samplerate=SAMPLE_RATE,
            channels=1,
            dtype="float32",
            device=MICROPHONE_DEVICE
        )
        sd.wait()
        rms = np.sqrt(np.mean(np.square(chunk)))
        status = "VOZ" if rms >= VOICE_THRESHOLD else "---"
        if i < 5 or i % 5 == 0:
            print(f"  chunk {i:3d}: RMS={rms:.5f} {status}")
        if rms >= VOICE_THRESHOLD:
            print(f"  >>> Voz detectada en chunk {i}")
            sd.stop()
            return True
    print("  No se detectó voz en 3s")
    sd.stop()
    return False


def test_with_warmup():
    print("\n=== TEST 2: Con calentamiento (0.5s dummy) ===")
    warmup_size = int(SAMPLE_RATE * 0.5)
    _ = sd.rec(
        warmup_size,
        samplerate=SAMPLE_RATE,
        channels=1,
        dtype="float32",
        device=MICROPHONE_DEVICE
    )
    sd.wait()
    print("  Calentamiento completado")

    chunk_size = int(SAMPLE_RATE * 0.1)
    for i in range(30):
        chunk = sd.rec(
            chunk_size,
            samplerate=SAMPLE_RATE,
            channels=1,
            dtype="float32",
            device=MICROPHONE_DEVICE
        )
        sd.wait()
        rms = np.sqrt(np.mean(np.square(chunk)))
        status = "VOZ" if rms >= VOICE_THRESHOLD else "---"
        if i < 5 or i % 5 == 0:
            print(f"  chunk {i:3d}: RMS={rms:.5f} {status}")
        if rms >= VOICE_THRESHOLD:
            print(f"  >>> Voz detectada en chunk {i}")
            sd.stop()
            return True
    print("  No se detectó voz en 3s")
    sd.stop()
    return False


def test_with_speak_then_listen():
    print("\n=== TEST 3: speak() + calentamiento + listen ===")
    import pyttsx3
    engine = pyttsx3.init()
    engine.say("Prueba")
    engine.runAndWait()
    engine.stop()
    time.sleep(0.3)
    print("  speak() completado")

    warmup_size = int(SAMPLE_RATE * 0.5)
    _ = sd.rec(
        warmup_size,
        samplerate=SAMPLE_RATE,
        channels=1,
        dtype="float32",
        device=MICROPHONE_DEVICE
    )
    sd.wait()
    print("  Calentamiento completado")

    chunk_size = int(SAMPLE_RATE * 0.1)
    for i in range(30):
        chunk = sd.rec(
            chunk_size,
            samplerate=SAMPLE_RATE,
            channels=1,
            dtype="float32",
            device=MICROPHONE_DEVICE
        )
        sd.wait()
        rms = np.sqrt(np.mean(np.square(chunk)))
        status = "VOZ" if rms >= VOICE_THRESHOLD else "---"
        if i < 5 or i % 5 == 0:
            print(f"  chunk {i:3d}: RMS={rms:.5f} {status}")
        if rms >= VOICE_THRESHOLD:
            print(f"  >>> Voz detectada en chunk {i}")
            sd.stop()
            return True
    print("  No se detectó voz en 3s")
    sd.stop()
    return False


if __name__ == "__main__":
    print("=== TEST CALENTAMIENTO DEL MICRÓFONO ===")
    print("Habla durante los tests para verificar detección")

    test_no_warmup()
    time.sleep(1)
    test_with_warmup()
    time.sleep(1)
    test_with_speak_then_listen()
