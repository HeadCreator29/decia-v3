"""
DECIA v2 — Diagnóstico de micrófono
NO modifica ningún archivo existente.
"""
import time
import sys
import numpy as np
import sounddevice as sd

DEVICE = 1
RATE = 16000
DTYPE = "float32"
CHANNELS = 1

print("=" * 60)
print("  DECIA v2 — DIAGNÓSTICO DE MICRÓFONO")
print("=" * 60)

# =============================================
# 1. INFORMACIÓN DEL DISPOSITIVO
# =============================================
print("\n[1] DISPOSITIVO SELECCIONADO")
print("-" * 40)

try:
    dev_info = sd.query_devices(DEVICE, "input")
    print(f"  Índice:     {DEVICE}")
    print(f"  Nombre:     {dev_info['name']}")
    print(f"  Canales:    {dev_info['max_input_channels']}")
    print(f"  Host API:   {dev_info['hostapi']}")
    print(f"  Sample rate (defecto): {dev_info['default_samplerate']}")
    print(f"  Low latency:  min={dev_info['low_latency_min_input']}, max={dev_info['low_latency_max_input']}")
    print(f"  High latency: min={dev_info['high_latency_min_input']}, max={dev_info['high_latency_max_input']}")
except Exception as e:
    print(f"  ERROR: {e}")

# =============================================
# 2. TODOS LOS DISPOSITIVOS DE ENTRADA
# =============================================
print("\n[2] TODOS LOS DISPOSITIVOS DE ENTRADA")
print("-" * 40)

devices = sd.query_devices()
for i, dev in enumerate(devices):
    if dev["max_input_channels"] > 0:
        marker = " <--- USANDO" if i == DEVICE else ""
        print(f"  [{i:2d}] ch={dev['max_input_channels']} "
              f"rate={dev['default_samplerate']:.0f} "
              f"{dev['name']}{marker}")

# =============================================
# 3. CONFIGURACIÓN ACTUAL DE sounddevice
# =============================================
print("\n[3] CONFIGURACIÓN DE SOUNDDEVICE")
print("-" * 40)

print(f"  Samplerate solicitado: {RATE}")
print(f"  Channels solicitado:   {CHANNELS}")
print(f"  dtype solicitado:      {DTYPE}")
print(f"  Device solicitado:     {DEVICE}")

try:
    default_input = sd.default.device[0]
    print(f"  Device default input:  {default_input}")
except:
    print(f"  Device default input:  No configurado")

try:
    default_samplerate = sd.default.samplerate
    print(f"  Default samplerate:    {default_samplerate}")
except:
    print(f"  Default samplerate:    No configurado")

# =============================================
# 4. TEST: CAPTURA AÍSLADA DE 2 SEGUNDOS
# =============================================
print("\n[4] CAPTURA AÍSLADA — 2 segundos")
print("    >>> HABLA AHORA durante 2 segundos <<<")
print("-" * 40)

size_2s = int(RATE * 2)
audio_2s = sd.rec(
    size_2s,
    samplerate=RATE,
    channels=CHANNELS,
    dtype=DTYPE,
    device=DEVICE
)
sd.wait()

rms_2s = np.sqrt(np.mean(np.square(audio_2s)))
peak_2s = np.max(np.abs(audio_2s))
min_2s = np.min(audio_2s)
max_2s = np.max(audio_2s)
std_2s = np.std(audio_2s)
nonzero_2s = np.count_nonzero(audio_2s)
total_2s = audio_2s.size
silence_ratio_2s = 1.0 - (nonzero_2s / total_2s)

print(f"  Forma:       {audio_2s.shape}")
print(f"  dtype:       {audio_2s.dtype}")
print(f"  RMS:         {rms_2s:.6f}")
print(f"  Peak (abs):  {peak_2s:.6f}")
print(f"  Min:         {min_2s:.6f}")
print(f"  Max:         {max_2s:.6f}")
print(f"  Std Dev:     {std_2s:.6f}")
print(f"  Samples == 0: {nonzero_2s}/{total_2s} ({silence_ratio_2s*100:.1f}% silencio)")
print(f"  Umbral:      0.025")
print(f"  ¿Detecta voz? {'SÍ' if rms_2s >= 0.025 else 'NO'}")

# =============================================
# 5. TEST: CHUNKS DE 0.1s (simula listen())
# =============================================
print("\n[5] CHUNKS DE 0.1s — 3 segundos (simula listen())")
print("    >>> HABLA AHORA durante 3 segundos <<<")
print("-" * 40)

chunk_dur = 0.1
chunk_size = int(RATE * chunk_dur)
rms_values = []

for i in range(30):
    chunk = sd.rec(
        chunk_size,
        samplerate=RATE,
        channels=CHANNELS,
        dtype=DTYPE,
        device=DEVICE
    )
    sd.wait()
    chunk = np.squeeze(chunk)
    rms = np.sqrt(np.mean(np.square(chunk)))
    rms_values.append(rms)

rms_arr = np.array(rms_values)
print(f"  Total chunks:   {len(rms_values)}")
print(f"  RMS promedio:   {rms_arr.mean():.6f}")
print(f"  RMS máximo:     {rms_arr.max():.6f}")
print(f"  RMS mínimo:     {rms_arr.min():.6f}")
print(f"  RMS std dev:    {rms_arr.std():.6f}")
print(f"  Umbral:         0.025")
print(f"  ¿Detecta voz?   {'SÍ' if rms_arr.max() >= 0.025 else 'NO'}")

print(f"\n  Primeros 10 chunks:")
for i in range(min(10, len(rms_values))):
    bar = "#" * int(rms_values[i] * 1000)
    print(f"    chunk {i:2d}: RMS={rms_values[i]:.6f} {bar}")

# =============================================
# 6. TEST: CHUNKS DE 0.5s
# =============================================
print("\n[6] CHUNKS DE 0.5s — 3 segundos")
print("    >>> HABLA AHORA durante 3 segundos <<<")
print("-" * 40)

chunk_size_05 = int(RATE * 0.5)
rms_values_05 = []

for i in range(6):
    chunk = sd.rec(
        chunk_size_05,
        samplerate=RATE,
        channels=CHANNELS,
        dtype=DTYPE,
        device=DEVICE
    )
    sd.wait()
    chunk = np.squeeze(chunk)
    rms = np.sqrt(np.mean(np.square(chunk)))
    rms_values_05.append(rms)

rms_arr_05 = np.array(rms_values_05)
print(f"  RMS promedio: {rms_arr_05.mean():.6f}")
print(f"  RMS máximo:   {rms_arr_05.max():.6f}")
print(f"  RMS mínimo:   {rms_arr_05.min():.6f}")

# =============================================
# 7. TEST: CAPTURA CONFERENCIA (channels=2)
# =============================================
print("\n[7] CAPTURA 2 CANALES — 2 segundos (verificar si el mic real es stereo)")
print("    >>> HABLA AHORA <<<")
print("-" * 40)

audio_stereo = sd.rec(
    int(RATE * 2),
    samplerate=RATE,
    channels=2,
    dtype=DTYPE,
    device=DEVICE
)
sd.wait()

rms_ch0 = np.sqrt(np.mean(np.square(audio_stereo[:, 0])))
rms_ch1 = np.sqrt(np.mean(np.square(audio_stereo[:, 1])))
rms_stereo = np.sqrt(np.mean(np.square(audio_stereo)))

print(f"  Forma:       {audio_stereo.shape}")
print(f"  RMS Ch0:     {rms_ch0:.6f}")
print(f"  RMS Ch1:     {rms_ch1:.6f}")
print(f"  RMS global:  {rms_stereo:.6f}")

# =============================================
# 8. TEST: dtype int16 vs float32
# =============================================
print("\n[8] COMPARACIÓN DE dtypes — 2 segundos")
print("    >>> HABLA AHORA <<<")
print("-" * 40)

audio_f32 = sd.rec(
    int(RATE * 2),
    samplerate=RATE,
    channels=CHANNELS,
    dtype="float32",
    device=DEVICE
)
sd.wait()

audio_i16 = sd.rec(
    int(RATE * 2),
    samplerate=RATE,
    channels=CHANNELS,
    dtype="int16",
    device=DEVICE
)
sd.wait()

rms_f32 = np.sqrt(np.mean(np.square(audio_f32)))
rms_i16 = np.sqrt(np.mean(np.square(audio_i16.astype(np.float32) / 32768.0)))

print(f"  float32 dtype: {audio_f32.dtype}, min={audio_f32.min():.6f}, max={audio_f32.max():.6f}")
print(f"  float32 RMS:   {rms_f32:.6f}")
print(f"  int16   dtype: {audio_i16.dtype}, min={audio_i16.min()}, max={audio_i16.max()}")
print(f"  int16   RMS:   {rms_i16:.6f}")

# =============================================
# 9. TEST: sd.InputStream en vez de sd.rec
# =============================================
print("\n[9] InputStream — 2 segundos (alternativa a sd.rec)")
print("    >>> HABLA AHORA <<<")
print("-" * 40)

try:
    frames_read = []
    duration_is = 2.0

    with sd.InputStream(
        device=DEVICE,
        channels=CHANNELS,
        samplerate=RATE,
        dtype=DTYPE,
    ) as stream:
        for _ in range(int(duration_is / 0.1)):
            data, overflowed = stream.read(int(RATE * 0.1))
            frames_read.append(data.copy())

    audio_is = np.concatenate(frames_read)
    audio_is = np.squeeze(audio_is)
    rms_is = np.sqrt(np.mean(np.square(audio_is)))
    print(f"  Forma:       {audio_is.shape}")
    print(f"  RMS:         {rms_is:.6f}")
    print(f"  dtype:       {audio_is.dtype}")
    print(f"  Overflowed:  {overflowed}")
except Exception as e:
    print(f"  ERROR: {e}")

# =============================================
# 10. TEST: DIFERENCIA CONSECUTIVA (sd.rec vs sd.rec)
# =============================================
print("\n[10] SECUENCIA: 2s aislado → pausa → chunks 0.1s")
print("     >>> HABLA CONTINUAMENTE durante todo el test <<<")
print("-" * 40)

# Captura 1: 2 segundos aislado
audio_a = sd.rec(
    int(RATE * 2),
    samplerate=RATE,
    channels=CHANNELS,
    dtype=DTYPE,
    device=DEVICE
)
sd.wait()
rms_a = np.sqrt(np.mean(np.square(audio_a)))
print(f"  [A] 2s aislado:     RMS={rms_a:.6f}")

# Pausa
time.sleep(0.3)

# Captura 2: 5 chunks de 0.1s
print(f"  [B] 5 chunks de 0.1s:")
for i in range(5):
    chunk = sd.rec(
        chunk_size,
        samplerate=RATE,
        channels=CHANNELS,
        dtype=DTYPE,
        device=DEVICE
    )
    sd.wait()
    chunk = np.squeeze(chunk)
    rms = np.sqrt(np.mean(np.square(chunk)))
    print(f"      chunk {i}: RMS={rms:.6f}")

# =============================================
# 11. VERIFICAR HOST API
# =============================================
print("\n[11] HOST APIs DISPONIBLES")
print("-" * 40)

for api in sd.query_hostapis():
    print(f"  [{api['index']}] {api['name']} "
          f"(devices={api['device_count']})")

current_api = sd.query_hostapis()[sd.default.hostapi]
print(f"\n  Host API actual: {current_api['name']}")

# =============================================
# RESUMEN
# =============================================
print("\n" + "=" * 60)
print("  RESUMEN DEL DIAGNÓSTICO")
print("=" * 60)
print(f"  Dispositivo:  [{DEVICE}] {dev_info['name']}")
print(f"  Host API:     {current_api['name']}")
print(f"  Samplerate:   {RATE}")
print(f"  Channels:     {CHANNELS}")
print(f"  dtype:        {DTYPE}")
print(f"  Umbral:       0.025")
print()
print(f"  RMS captura aislada (2s):     {rms_2s:.6f}")
print(f"  RMS chunks 0.1s (máx):       {rms_arr.max():.6f}")
print(f"  RMS chunks 0.5s (máx):       {rms_arr_05.max():.6f}")
print(f"  RMS InputStream (2s):         {rms_is:.6f}")
print()
if rms_2s > rms_arr.max() * 5:
    print("  DIAGNÓSTICO: Captura aislada >> Chunks de 0.1s")
    print("  El problema es el tamaño del chunk.")
elif rms_2s < 0.01 and rms_arr.max() < 0.01:
    print("  DIAGNÓSTICO: Ambas capturas son silencio.")
    print("  El problema es el dispositivo o la configuración de audio.")
elif rms_2s >= 0.025:
    print("  DIAGNÓSTICO: Captura aislada SÍ detecta voz.")
    print("  El problema está en el loop de chunks.")
else:
    print("  DIAGNÓSTICO: Captura aislada tiene señal baja.")
    print("  El problema puede ser el dispositivo o el nivel de entrada.")
print()
print("  FIN DEL DIAGNÓSTICO")
print("=" * 60)
