import re


REPLACEMENTS = {
    "á": "a",
    "é": "e",
    "í": "i",
    "ó": "o",
    "ú": "u",
    "ü": "u",
}


def normalize(text):

    text = text.lower().strip()

    for old, new in REPLACEMENTS.items():

        text = text.replace(old, new)

    return text


def normalize_strict(text):

    text = normalize(text)

    text = text.replace("¿", "")
    text = text.replace("?", "")
    text = text.replace("¡", "")
    text = text.replace("!", "")
    text = text.replace(",", "")
    text = text.replace(".", "")
    text = text.replace(":", "")
    text = text.replace(";", "")

    return " ".join(text.split())
