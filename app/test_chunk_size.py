"""Test: Does chunk size affect capture?"""
import numpy as np
import sounddevice as sd

SAMPLE_RATE = 16000
DEVICE = 1
DURATIONS = [0.1, 0.25, 0.5, 1.0, 2.0]

print("=== TEST: Tamaño de chunk vs captura ===")
print("Habla durante cada test\n")

for dur in DURATIONS:
    chunk_size = int(SAMPLE_RATE * dur)
    audio = sd.rec(
        chunk_size,
        samplerate=SAMPLE_RATE,
        channels=1,
        dtype="float32",
        device=DEVICE
    )
    sd.wait()
    rms = np.sqrt(np.mean(np.square(audio)))
    status = "VOZ" if rms >= 0.025 else "---"
    print(f"  {dur:.2f}s ({chunk_size:5d} samples): "
          f"RMS={rms:.5f} {status}")

print()
print("Ahora prueba con chunks de 0.1s CONSECUTIVOS:")
print("(Habla durante los 3 segundos)\n")

chunk_size = int(SAMPLE_RATE * 0.1)
for i in range(30):
    audio = sd.rec(
        chunk_size,
        samplerate=SAMPLE_RATE,
        channels=1,
        dtype="float32",
        device=DEVICE
    )
    sd.wait()
    rms = np.sqrt(np.mean(np.square(audio)))
    if i < 5 or i % 5 == 0:
        status = "VOZ" if rms >= 0.025 else "---"
        print(f"  chunk {i:3d} (0.1s): RMS={rms:.5f} {status}")
    if rms >= 0.025:
        print(f"  >>> Voz detectada en chunk {i}!")

print("\n=== FIN ===")
