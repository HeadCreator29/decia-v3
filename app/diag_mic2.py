"""
DECIA v2 — Diagnóstico enfocado: sd.rec() vs InputStream
Compara directamente el problema del buffer.
"""
import time
import numpy as np
import sounddevice as sd

DEVICE = 1
RATE = 16000
CHANNELS = 1
DTYPE = "float32"

print("=" * 60)
print("  DIAGNÓSTICO ENFOCADO: BUFFER DE CAPTURA")
print("=" * 60)

# =============================================
# TEST A: sd.rec() 0.1s (como listen())
# =============================================
print("\n[A] sd.rec() chunks de 0.1s — HABLA 4 segundos")
print("-" * 40)

chunk_size = int(RATE * 0.1)
rms_a = []
for i in range(40):
    chunk = sd.rec(chunk_size, samplerate=RATE, channels=CHANNELS, dtype=DTYPE, device=DEVICE)
    sd.wait()
    chunk = np.squeeze(chunk)
    rms = np.sqrt(np.mean(np.square(chunk)))
    rms_a.append(rms)

rms_a_arr = np.array(rms_a)
print(f"  RMS promedio: {rms_a_arr.mean():.6f}")
print(f"  RMS máximo:   {rms_a_arr.max():.6f}")

# =============================================
# TEST B: InputStream con reads de 0.1s
# =============================================
print("\n[B] InputStream con reads de 0.1s — HABLA 4 segundos")
print("-" * 40)

rms_b = []
try:
    with sd.InputStream(device=DEVICE, channels=CHANNELS, samplerate=RATE, dtype=DTYPE) as stream:
        for i in range(40):
            data, _ = stream.read(int(RATE * 0.1))
            data = np.squeeze(data)
            rms = np.sqrt(np.mean(np.square(data)))
            rms_b.append(rms)
    rms_b_arr = np.array(rms_b)
    print(f"  RMS promedio: {rms_b_arr.mean():.6f}")
    print(f"  RMS máximo:   {rms_b_arr.max():.6f}")
except Exception as e:
    print(f"  ERROR: {e}")

# =============================================
# TEST C: sd.rec() con sample rate nativo (44100)
# =============================================
print("\n[C] sd.rec() 0.1s con RATE=44100 (nativo del dispositivo) — HABLA 4 segundos")
print("-" * 40)

chunk_size_c = int(44100 * 0.1)
rms_c = []
for i in range(40):
    chunk = sd.rec(chunk_size_c, samplerate=44100, channels=CHANNELS, dtype=DTYPE, device=DEVICE)
    sd.wait()
    chunk = np.squeeze(chunk)
    rms = np.sqrt(np.mean(np.square(chunk)))
    rms_c.append(rms)

rms_c_arr = np.array(rms_c)
print(f"  RMS promedio: {rms_c_arr.mean():.6f}")
print(f"  RMS máximo:   {rms_c_arr.max():.6f}")

# =============================================
# TEST D: sd.rec() 2s aislado (baseline)
# =============================================
print("\n[D] sd.rec() 2s aislado — HABLA 2 segundos")
print("-" * 40)

audio_d = sd.rec(int(RATE * 2), samplerate=RATE, channels=CHANNELS, dtype=DTYPE, device=DEVICE)
sd.wait()
rms_d = np.sqrt(np.mean(np.square(audio_d)))
peak_d = np.max(np.abs(audio_d))
print(f"  RMS:   {rms_d:.6f}")
print(f"  Peak:  {peak_d:.6f}")

# =============================================
# TEST E: sd.rec() 5s aislado
# =============================================
print("\n[E] sd.rec() 5s aislado — HABLA 5 segundos")
print("-" * 40)

audio_e = sd.rec(int(RATE * 5), samplerate=RATE, channels=CHANNELS, dtype=DTYPE, device=DEVICE)
sd.wait()
rms_e = np.sqrt(np.mean(np.square(audio_e)))
peak_e = np.max(np.abs(audio_e))
print(f"  RMS:   {rms_e:.6f}")
print(f"  Peak:  {peak_e:.6f}")

# =============================================
# TEST F: Blocksize explícito en InputStream
# =============================================
print("\n[F] InputStream con blocksize=1600 (0.1s) — HABLA 4 segundos")
print("-" * 40)

rms_f = []
try:
    with sd.InputStream(device=DEVICE, channels=CHANNELS, samplerate=RATE, dtype=DTYPE, blocksize=1600) as stream:
        for i in range(40):
            data, _ = stream.read(1600)
            data = np.squeeze(data)
            rms = np.sqrt(np.mean(np.square(data)))
            rms_f.append(rms)
    rms_f_arr = np.array(rms_f)
    print(f"  RMS promedio: {rms_f_arr.mean():.6f}")
    print(f"  RMS máximo:   {rms_f_arr.max():.6f}")
except Exception as e:
    print(f"  ERROR: {e}")

# =============================================
# TEST G: sd.rec() chunks de 0.1s con el RATE nativo 44100
# y luego resample manual
# =============================================
print("\n[G] sd.rec() 0.1s @ 44100 → resample a 16000 — HABLA 4 segundos")
print("-" * 40)

chunk_size_g = int(44100 * 0.1)
rms_g = []
for i in range(40):
    chunk = sd.rec(chunk_size_g, samplerate=44100, channels=CHANNELS, dtype=DTYPE, device=DEVICE)
    sd.wait()
    chunk = np.squeeze(chunk)
    # Resample simple: tomar cada ~2.75 samples
    indices = np.linspace(0, len(chunk) - 1, int(RATE * 0.1)).astype(int)
    chunk_resampled = chunk[indices]
    rms = np.sqrt(np.mean(np.square(chunk_resampled)))
    rms_g.append(rms)

rms_g_arr = np.array(rms_g)
print(f"  RMS promedio: {rms_g_arr.mean():.6f}")
print(f"  RMS máximo:   {rms_g_arr.max():.6f}")

# =============================================
# RESUMEN COMPARATIVO
# =============================================
print("\n" + "=" * 60)
print("  RESUMEN COMPARATIVO")
print("=" * 60)
print(f"  [A] sd.rec() 0.1s @ 16kHz:     RMS max = {rms_a_arr.max():.6f}")
if rms_b:
    print(f"  [B] InputStream 0.1s @ 16kHz:  RMS max = {rms_b_arr.max():.6f}")
print(f"  [C] sd.rec() 0.1s @ 44100Hz:   RMS max = {rms_c_arr.max():.6f}")
print(f"  [D] sd.rec() 2s @ 16kHz:       RMS = {rms_d:.6f}")
print(f"  [E] sd.rec() 5s @ 16kHz:       RMS = {rms_e:.6f}")
if rms_f:
    print(f"  [F] InputStream block=1600:    RMS max = {rms_f_arr.max():.6f}")
print(f"  [G] sd.rec() 0.1s @ 44100→16k: RMS max = {rms_g_arr.max():.6f}")

print()
if rms_b and rms_a_arr.max() < rms_b_arr.max() * 0.5:
    print("  CONCLUSIÓN: InputStream >> sd.rec() para chunks cortos")
    print("  CAUSA: sd.rec() abre/cierra stream por cada llamada")
elif rms_c_arr.max() > rms_a_arr.max() * 5:
    print("  CONCLUSIÓN: sd.rec() @ 44100 >> sd.rec() @ 16000")
    print("  CAUSA: El resampling de PortAudio reduce la calidad")
else:
    print("  CONCLUSIÓN: Todos los métodos muestran niveles bajos")
    print("  CAUSA: El nivel de entrada del micrófono es bajo")
print("=" * 60)
