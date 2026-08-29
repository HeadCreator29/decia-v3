import re


# ==========================================
# STUTTER / REPETICIÓN INMEDIATA DE TOKENS
# (corrección mecánica conservadora)
# ==========================================


_COLLAPSE_MAX_LEN = 3

_COLLAPSE_PROTECTED = {
    "muy", "ya", "no", "si", "sí",
    "bien", "mas", "más", "así", "asi",
    "vale", "claro",
}


def _is_collapsible_token(word):

    key = word.lower()

    return (
        len(key) <= _COLLAPSE_MAX_LEN
        and key.isalpha()
        and key not in _COLLAPSE_PROTECTED
        and word.islower()
    )


def collapse_repeated_tokens(text):

    if not text or not text.strip():
        return text

    leading = text[: len(text) - len(text.lstrip())]

    trailing = text[len(text.rstrip()) :]

    words = text.split()

    kept = []

    previous = None

    for word in words:

        if (
            word == previous
            and _is_collapsible_token(word)
        ):

            continue

        kept.append(word)

        previous = word

    return (
        leading + " ".join(kept) + trailing
    )


# ==========================================
# REGLAS DE CORRECCIÓN CONTEXTUAL (LOCAL)
# ==========================================

CORRECTION_RULES = [
    (
        re.compile(
            r'\b(planeta)\s+martes?\b',
            re.IGNORECASE,
        ),
        r'\1 Marte',
    ),
    (
        re.compile(
            r'\b(planeta)\s+mal\b',
            re.IGNORECASE,
        ),
        r'\1 Marte',
    ),
    (
        re.compile(r'\bkien\b', re.IGNORECASE),
        r'quien',
    ),
    (
        re.compile(r'\bke\b', re.IGNORECASE),
        r'que',
    ),
    (
        re.compile(r'\bkhe\b', re.IGNORECASE),
        r'que',
    ),
    (
        re.compile(r'\bgrasias\b', re.IGNORECASE),
        r'gracias',
    ),
]


# ==========================================
# FUNCIÓN PRINCIPAL
# ==========================================


def correct_transcription(text):

    if not text or not text.strip():
        return text

    original = text

    corrected = text
    was_corrected = False

    corrected = collapse_repeated_tokens(
        text
    )

    if corrected != text:

        was_corrected = True

    for pattern, replacement in CORRECTION_RULES:

        new_text = pattern.sub(replacement, corrected)

        if new_text != corrected:
            was_corrected = True
            corrected = new_text

    if was_corrected:

        print(
            f"[DECIA CORRECTION] "
            f'"{original}" -> "{corrected}"'
        )

        return corrected

    print("[DECIA CORRECTION] Sin corrección local")

    from transcription_interpreter import (
        check_suspicion,
        interpret_transcription,
    )

    suspicion = check_suspicion(text)

    if not suspicion.is_suspicious:

        return text

    return interpret_transcription(text, suspicion)
