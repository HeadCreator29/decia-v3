from services.voice import listen, speak


def main():

    text = listen()

    if text:

        print()
        print("RESULTADO:")
        print(text)

        speak(
            "Te escuché. Dijiste: " + text
        )


if __name__ == "__main__":
    main()