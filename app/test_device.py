import sounddevice as sd
import numpy as np
import time


DEVICE = 1
SAMPLE_RATE = 16000
DURATION = 10


print("=== PRUEBA DE NIVEL DEL MICROFONO ===")
print()
print("Durante los primeros 3 segundos: NO HABLES.")
print("Después habla durante 3 segundos.")
print("Luego vuelve a guardar silencio.")
print()


audio = sd.rec(
    int(DURATION * SAMPLE_RATE),
    samplerate=SAMPLE_RATE,
    channels=1,
    dtype="float32",
    device=DEVICE
)

sd.wait()

audio = np.squeeze(audio)


chunk_size = int(SAMPLE_RATE * 0.5)

print()
print("=== NIVELES ===")
print()

for i in range(0, len(audio), chunk_size):

    chunk = audio[i:i + chunk_size]

    if len(chunk) == 0:
        continue

    rms = np.sqrt(
        np.mean(np.square(chunk))
    )

    peak = np.max(
        np.abs(chunk)
    )

    print(
        f"{i / SAMPLE_RATE:4.1f}s - "
        f"RMS: {rms:.5f} | "
        f"PEAK: {peak:.5f}"
    )