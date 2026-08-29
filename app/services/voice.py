import os
import time
import sounddevice as sd
import numpy as np
import pyttsx3
from faster_whisper import WhisperModel


# ==========================================
# CONFIGURACIÓN
# ==========================================

MODEL_SIZE = "small"

MICROPHONE_DEVICE = int(
    os.environ.get("DECIA_MIC_DEVICE", "1")
)

SAMPLE_RATE = 16000

VOICE_THRESHOLD = float(
    os.environ.get(
        "DECIA_VOICE_THRESHOLD", "0.025"
    )
)

SILENCE_DURATION = 1.2

MAX_DURATION = 30


# ==========================================
# WHISPER
# ==========================================

print("[DECIA VOICE] Cargando modelo de voz...")

model = WhisperModel(
    MODEL_SIZE,
    device="cpu",
    compute_type="int8"
)

print("[DECIA VOICE] Modelo de voz listo.")

print(
    f"[DECIA VOICE] "
    f"Micrófono: dispositivo {MICROPHONE_DEVICE} | "
    f"Umbral: {VOICE_THRESHOLD}"
)

try:

    devices = sd.query_devices()

    print("[DECIA VOICE] Dispositivos de audio:")

    for i, dev in enumerate(devices):

        if dev["max_input_channels"] > 0:

            marker = (
                " <--- USANDO"
                if i == MICROPHONE_DEVICE
                else ""
            )

            print(
                f"  [{i}] {dev['name']}"
                f"{marker}"
            )

except Exception:

    pass


# ==========================================
# HABLAR
# ==========================================

def speak(text):

    if not text:

        return

    print(
        "[DECIA VOICE] 🔊 Hablando..."
    )

    engine = pyttsx3.init()

    engine.setProperty("rate", 175)

    engine.setProperty("volume", 1.0)

    engine.say(text)

    engine.runAndWait()

    engine.stop()

    time.sleep(0.3)


# ==========================================
# ESCUCHAR
# ==========================================

def listen():

    print()
    print("[DECIA VOICE] 🎤 Escuchando...")

    chunk_duration = 0.1

    chunk_size = int(
        SAMPLE_RATE * chunk_duration
    )

    audio_chunks = []

    started = False

    silence_time = 0

    start_time = time.perf_counter()

    chunk_count = 0

    max_rms = 0.0

    # ==========================================
    # ESCUCHAR MICRÓFONO
    # ==========================================

    stream = sd.InputStream(
        device=MICROPHONE_DEVICE,
        channels=1,
        samplerate=SAMPLE_RATE,
        dtype="float32",
        blocksize=chunk_size,
    )

    stream.start()

    try:

        while True:

            data, _ = stream.read(chunk_size)

            chunk = np.squeeze(data)

            # --------------------------------------
            # NIVEL DE AUDIO
            # --------------------------------------

            rms = np.sqrt(
                np.mean(
                    np.square(chunk)
                )
            )

            chunk_count += 1

            if rms > max_rms:

                max_rms = rms

            if chunk_count % 10 == 0:

                elapsed = (
                    time.perf_counter()
                    - start_time
                )

                print(
                    f"[DECIA VOICE] "
                    f"RMS={rms:.5f} | "
                    f"máx={max_rms:.5f} | "
                    f"umbral={VOICE_THRESHOLD} | "
                    f"{elapsed:.1f}s"
                )

            # ======================================
            # TODAVÍA NO HABLAS
            # ======================================

            if not started:

                if rms >= VOICE_THRESHOLD:

                    started = True

                    print(
                        "[DECIA VOICE] 🗣️ Voz detectada..."
                    )

                    audio_chunks.append(chunk)

                continue

            # ======================================
            # YA ESTÁS HABLANDO
            # ======================================

            audio_chunks.append(chunk)

            # ======================================
            # DETECTAR SILENCIO
            # ======================================

            if rms < VOICE_THRESHOLD:

                silence_time += chunk_duration

            else:

                silence_time = 0

            # ======================================
            # TERMINASTE DE HABLAR
            # ======================================

            if silence_time >= SILENCE_DURATION:

                break

            # ======================================
            # SEGURIDAD
            # ======================================

            if (
                time.perf_counter() - start_time
                >= MAX_DURATION
            ):

                break

    finally:

        stream.stop()

        stream.close()

    # ==========================================
    # NO HUBO VOZ
    # ==========================================

    if not audio_chunks:

        print(
            "[DECIA VOICE] "
            "No detecté voz."
        )

        print(
            f"[DECIA VOICE] "
            f"RMS máximo detectado: "
            f"{max_rms:.5f} | "
            f"Umbral requerido: "
            f"{VOICE_THRESHOLD}"
        )

        if max_rms < VOICE_THRESHOLD:

            print(
                "[DECIA VOICE] "
                "SUGERENCIA: El micrófono no "
                "está captando audio. "
                "Prueba:"
            )

            print(
                "[DECIA VOICE] "
                "  1. Verifica que el micrófono "
                "esté conectado"
            )

            print(
                "[DECIA VOICE] "
                "  2. Cambia el dispositivo: "
                "DECIA_MIC_DEVICE=1 python main.py"
            )

            print(
                "[DECIA VOICE] "
                "  3. Baja el umbral: "
                "DECIA_VOICE_THRESHOLD=0.01 "
                "python main.py"
            )

        return None

    print(
        "[DECIA VOICE] Procesando voz..."
    )

    # ==========================================
    # UNIR AUDIO
    # ==========================================

    audio = np.concatenate(
        audio_chunks
    )

    # ==========================================
    # CONVERTIR A FLOAT32
    # ==========================================

    audio = audio.astype(
        np.float32
    )

    # ==========================================
    # WHISPER
    # ==========================================

    segments, info = model.transcribe(

        audio,

        language="es",

        beam_size=5,

        temperature=0,

        vad_filter=True,

        vad_parameters={
            "min_silence_duration_ms": 500,
            "speech_pad_ms": 250
        },

        condition_on_previous_text=False,

        no_speech_threshold=0.7,

        log_prob_threshold=-1.0,

        compression_ratio_threshold=2.4
    )

    # ==========================================
    # CONSTRUIR TEXTO
    # ==========================================

    text_parts = []

    for segment in segments:

        segment_text = segment.text.strip()

        if segment_text:

            text_parts.append(
                segment_text
            )

    text = " ".join(
        text_parts
    ).strip()

    # ==========================================
    # VALIDAR RESULTADO
    # ==========================================

    if not text:

        print(
            "[DECIA VOICE] "
            "No entendí nada."
        )

        return None

    print(
        f"[DECIA VOICE] Tú > {text}"
    )

    return text