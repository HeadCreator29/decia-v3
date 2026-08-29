import time

from brain import think, ConversationContext

from services.voice import listen, speak
from utils.speech_corrections import (
    correct_transcription,
)


def main():

    context = ConversationContext(
        max_turns=10
    )

    print("╔════════════════════════════╗")
    print("║           DECIA            ║")
    print("║      Sistema iniciado      ║")
    print("╚════════════════════════════╝")
    print()

    speak(
        "Habla con DECIA. Di salir para cerrar."
    )

    while True:

        # ==========================================
        # ESCUCHAR
        # ==========================================

        raw_input = listen()

        if not raw_input:

            continue

        print()

        # ==========================================
        # SALIR
        # ==========================================

        normalized = (
            raw_input.lower().strip()
        )

        if normalized in [
            "salir",
            "exit",
            "quit",
        ]:

            speak("Hasta luego.")

            print("[DECIA] Sistema cerrado.")

            break

        # ==========================================
        # PENSAR
        # ==========================================

        start_time = time.perf_counter()

        processed_input = correct_transcription(
            raw_input
        )

        response = think(
            processed_input, context=context
        )

        if response == "Hasta luego.":

            print("[DECIA] Sistema cerrado.")

            break

        elapsed = (
            time.perf_counter() - start_time
        )

        context.add_user_message(processed_input)

        context.add_assistant_message(
            response
        )

        # ==========================================
        # MOSTRAR RESPUESTA
        # ==========================================

        print(f"DECIA > {response}")

        print(
            f"       └─ Respuesta en "
            f"{elapsed:.2f} segundos"
        )

        # ==========================================
        # HABLAR
        # ==========================================

        speak(response)

        print()


if __name__ == "__main__":
    main()
