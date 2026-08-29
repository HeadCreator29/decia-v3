import sounddevice as sd
import numpy as np
import time


print("=== PRUEBA DEL MICRÓFONO ===")
print()

print("Dispositivos de audio:")
print(sd.query_devices())
print()

sample_rate = 16000
duration = 5

print("Habla durante 5 segundos...")
print()

recording = sd.rec(
    int(duration * sample_rate),
    samplerate=sample_rate,
    channels=1,
    dtype="float32"
)

sd.wait()

audio = np.squeeze(recording)

rms = np.sqrt(
    np.mean(
        np.square(audio)
    )
)

peak = np.max(
    np.abs(audio)
)

print()
print("=== RESULTADO ===")
print(f"RMS  : {rms:.6f}")
print(f"PEAK : {peak:.6f}")