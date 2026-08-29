"""
Test rápido: InputStream en listen() de DECIA
Verifica que el stream captura audio correctamente.
"""
import numpy as np
import sounddevice as sd

DEVICE = 1
RATE = 16000
CHANNELS = 1
DTYPE = "float32"
CHUNK = int(RATE * 0.1)

print("=" * 50)
print("  TEST: InputStream capture")
print("  >>> HABLA 4 segundos <<<")
print("=" * 50)

stream = sd.InputStream(
    device=DEVICE,
    channels=CHANNELS,
    samplerate=RATE,
    dtype=DTYPE,
    blocksize=CHUNK,
)

stream.start()

rms_values = []

try:
    for i in range(40):
        data, _ = stream.read(CHUNK)
        chunk = np.squeeze(data)
        rms = np.sqrt(np.mean(np.square(chunk)))
        rms_values.append(rms)
        if i < 5 or i % 10 == 0:
            bar = "#" * min(int(rms * 1000), 60)
            print(f"  chunk {i:2d}: RMS={rms:.5f} {bar}")
finally:
    stream.stop()
    stream.close()

rms_arr = np.array(rms_values)

print()
print(f"  RMS promedio: {rms_arr.mean():.6f}")
print(f"  RMS maximo:   {rms_arr.max():.6f}")
print(f"  RMS minimo:   {rms_arr.min():.6f}")
print(f"  Umbral:       0.025")
print(f"  ¿Detecta voz? {'SI' if rms_arr.max() >= 0.025 else 'NO'}")

# Comparar con sd.rec()
print()
print("  Comparacion con sd.rec() 2s:")
audio = sd.rec(int(RATE * 2), samplerate=RATE, channels=CHANNELS, dtype=DTYPE, device=DEVICE)
sd.wait()
rms_rec = np.sqrt(np.mean(np.square(audio)))
print(f"  sd.rec() 2s RMS: {rms_rec:.6f}")
print(f"  InputStream max: {rms_arr.max():.6f}")
if rms_arr.max() > rms_rec:
    print(f"  InputStream es {rms_arr.max()/rms_rec:.1f}x mejor que sd.rec()")
print()
print("  FIN")
