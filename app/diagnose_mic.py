import time
import sounddevice as sd
import numpy as np


SAMPLE_RATE = 16000
DURATION = 3


print("=== DIAGNÓSTICO DE MICRÓFONO ===")
print("Habla durante 3 segundos para cada prueba.")
print()

devices = sd.query_devices()

input_devices = [
    (i, dev)
    for i, dev in enumerate(devices)
    if dev["max_input_channels"] > 0
]

print(
    f"Encontrados {len(input_devices)} "
    f"dispositivos de entrada.\n"
)

for device_id, device_info in input_devices:

    name = device_info["name"]

    print(f"[{device_id}] {name}")
    print("  Grabando 3 segundos... habla ahora!")

    try:

        audio = sd.rec(
            int(DURATION * SAMPLE_RATE),
            samplerate=SAMPLE_RATE,
            channels=1,
            dtype="float32",
            device=device_id,
        )

        sd.wait()

        audio = np.squeeze(audio)

        rms = np.sqrt(
            np.mean(np.square(audio))
        )

        peak = np.max(np.abs(audio))

        marker = ""

        if rms > 0.01:

            marker = " <--- FUNCIONA"

        print(
            f"  RMS={rms:.5f} | "
            f"PEAK={peak:.5f}"
            f"{marker}"
        )

    except Exception as error:

        print(f"  ERROR: {error}")

    print()


print("=== FIN ===")
print(
    "Busca el dispositivo con RMS más alto."
)
print(
    "Ese es tu micrófono correcto."
)
