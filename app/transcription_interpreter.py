import json
import re
from urllib import request


# ==========================================
# CONFIGURACIÓN
# ==========================================

OLLAMA_URL = "http://localhost:11434/api/chat"
ANALYZER_MODEL = "llama3.2:3b"
ANALYZER_TEMPERATURE = 0.1
ANALYZER_MAX_TOKENS = 80
CONFIDENCE_THRESHOLD = 0.85
MAX_CHANGE_RATIO = 0.50


# ==========================================
# REGLAS DE SOSPECHA
# ==========================================

SUSPICION_RULES = [
    {
        "trigger": "planeta",
        "known_entities": [
            "mercurio", "venus", "tierra",
            "marte", "jupiter", "júpiter",
            "saturno", "urano", "neptuno",
            "plutón", "pluton",
            "luna", "sol",
        ],
        "description": (
            "palabra después de 'planeta' "
            "no coincide con planetas conocidos"
        ),
    },
]


# ==========================================
# PROMPT DEL ANALIZADOR
# ==========================================

ANALYZER_SYSTEM_PROMPT = """\
Eres un analizador de transcripciones de voz.

Tu ÚNICO trabajo es determinar si una palabra \
fue transcrita incorrectamente por reconocimiento \
de voz.

REGLAS ESTRICTAS:
1. NO respondas al usuario.
2. NO reformules la frase.
3. NO agregues información.
4. NO expliques tu razonamiento en la respuesta.
5. Solo propón una corrección si la evidencia \
contextual es muy fuerte.
6. Si la frase puede ser legítima sin corrección, \
indica que no hay corrección.

Devuelve ÚNICAMENTE un JSON válido:

{
    "should_correct": true,
    "confidence": 0.95,
    "corrected_text": "texto corregido",
    "reason": "breve explicación"
}

o

{
    "should_correct": false,
    "confidence": 1.0,
    "corrected_text": null,
    "reason": "la transcripción parece correcta"
}

NO agregues texto fuera del JSON.
NO uses bloques de código markdown.
"""


# ==========================================
# RESULTADOS
# ==========================================


class SuspicionResult:

    def __init__(
        self,
        is_suspicious,
        reason="",
        suspect_word="",
        context_window="",
    ):
        self.is_suspicious = is_suspicious
        self.reason = reason
        self.suspect_word = suspect_word
        self.context_window = context_window


class ValidationResult:

    def __init__(
        self,
        should_correct,
        confidence,
        corrected_text,
        reason,
    ):
        self.should_correct = should_correct
        self.confidence = confidence
        self.corrected_text = corrected_text
        self.reason = reason


# ==========================================
# DETECTOR DE SOSPECHA
# ==========================================


def check_suspicion(text):

    if not text or not text.strip():
        return SuspicionResult(is_suspicious=False)

    normalized = text.lower().strip()
    words = normalized.split()

    for rule in SUSPICION_RULES:

        trigger = rule["trigger"]

        if trigger not in words:
            continue

        idx = words.index(trigger)

        if idx + 1 >= len(words):
            continue

        next_word = words[idx + 1]

        cleaned = re.sub(r'[^\w]', '', next_word)

        cleaned_no_accents = (
            cleaned
            .replace("á", "a").replace("é", "e")
            .replace("í", "i").replace("ó", "o")
            .replace("ú", "u").replace("ü", "u")
        )

        if cleaned_no_accents in rule["known_entities"]:
            continue

        if cleaned and len(cleaned) > 2:
            return SuspicionResult(
                is_suspicious=True,
                reason=rule["description"],
                suspect_word=cleaned,
                context_window=(
                    f"{trigger} {cleaned}"
                ),
            )

    return SuspicionResult(is_suspicious=False)


# ==========================================
# ANALIZADOR CONTEXTUAL (OLLAMA)
# ==========================================


def analyze_with_ollama(original_text, suspicion):

    print(
        "[DECIA INTERPRETER] "
        "Consultando analizador contextual..."
    )

    user_message = (
        f'Transcripción original: "{original_text}"\n\n'
        f"Contexto de sospecha: {suspicion.reason}\n"
        f"Palabra sospechosa: {suspicion.suspect_word}\n"
        f'Ventana de contexto: '
        f'"{suspicion.context_window}"\n\n'
        f"Analiza si la transcripción es correcta o si "
        f"probablemente hubo un error de "
        f"reconocimiento de voz."
    )

    data = {
        "model": ANALYZER_MODEL,
        "think": False,
        "keep_alive": -1,
        "messages": [
            {
                "role": "system",
                "content": ANALYZER_SYSTEM_PROMPT,
            },
            {
                "role": "user",
                "content": user_message,
            },
        ],
        "stream": False,
        "options": {
            "temperature": ANALYZER_TEMPERATURE,
            "num_predict": ANALYZER_MAX_TOKENS,
        },
    }

    payload = json.dumps(data).encode("utf-8")

    http_request = request.Request(
        OLLAMA_URL,
        data=payload,
        headers={
            "Content-Type": "application/json"
        },
    )

    try:

        with request.urlopen(
            http_request, timeout=30
        ) as response:

            result = json.loads(
                response.read().decode("utf-8")
            )

    except Exception as error:

        print(
            f"[DECIA INTERPRETER] "
            f"Error en análisis: {error}"
        )
        return None

    answer = (
        result.get("message", {})
        .get("content", "")
    )

    return answer


# ==========================================
# VALIDACIÓN DE RESPUESTA
# ==========================================


def validate_ollama_response(
    response_text, original_text
):

    if not response_text:
        return None

    json_match = re.search(
        r'\{.*\}', response_text, re.DOTALL
    )

    if not json_match:
        print(
            "[DECIA INTERPRETER] "
            "No se encontró JSON en la respuesta"
        )
        return None

    try:
        data = json.loads(json_match.group())
    except json.JSONDecodeError:
        print(
            "[DECIA INTERPRETER] "
            "JSON inválido en la respuesta"
        )
        return None

    should_correct = data.get("should_correct")
    confidence = data.get("confidence")
    corrected = data.get("corrected_text")
    reason = data.get("reason", "")

    if should_correct is None:
        return None

    if confidence is None:
        return None

    if not isinstance(confidence, (int, float)):
        return None

    if confidence < 0.0 or confidence > 1.0:
        print(
            "[DECIA INTERPRETER] "
            f"Confianza fuera de rango: {confidence}"
        )
        return None

    if not should_correct:
        return ValidationResult(
            should_correct=False,
            confidence=confidence,
            corrected_text=None,
            reason=reason,
        )

    if not corrected or not isinstance(corrected, str):
        return None

    if len(corrected.strip()) == 0:
        return None

    original_words = set(
        original_text.lower().split()
    )
    corrected_words = set(corrected.lower().split())
    unchanged = original_words & corrected_words

    if len(original_words) > 0:
        change_ratio = (
            1 - len(unchanged) / len(original_words)
        )
    else:
        change_ratio = 0

    if change_ratio > MAX_CHANGE_RATIO:
        print(
            "[DECIA INTERPRETER] "
            f"Cambio demasiado grande: "
            f"{change_ratio:.0%}"
        )
        return None

    conversational = [
        "hola", "claro", "por supuesto",
        "puedo ayudarte", "déjame", "permíteme",
    ]

    corrected_lower = corrected.lower()

    for marker in conversational:
        if marker in corrected_lower:
            print(
                "[DECIA INTERPRETER] "
                "Respuesta conversacional detectada"
            )
            return None

    return ValidationResult(
        should_correct=True,
        confidence=confidence,
        corrected_text=corrected,
        reason=reason,
    )


# ==========================================
# ORQUESTADOR DE INTERPRETACIÓN
# ==========================================


def interpret_transcription(text, suspicion):

    print(
        f"[DECIA INTERPRETER] "
        f"Sospecha detectada: {suspicion.reason}"
    )

    raw_response = analyze_with_ollama(
        text, suspicion
    )

    if raw_response is None:

        print(
            "[DECIA INTERPRETER] "
            "Error en análisis. "
            "Conservando transcripción original."
        )
        return text

    validation = validate_ollama_response(
        raw_response, text
    )

    if validation is None:

        print(
            "[DECIA INTERPRETER] "
            "Respuesta inválida. "
            "Conservando transcripción original."
        )
        return text

    if not validation.should_correct:

        print(
            "[DECIA INTERPRETER] "
            "Analizador indica: sin corrección. "
            "Conservando transcripción original."
        )
        return text

    if validation.confidence < CONFIDENCE_THRESHOLD:

        print(
            "[DECIA INTERPRETER] "
            f"Confianza insuficiente: "
            f"{validation.confidence:.2f} "
            f"< {CONFIDENCE_THRESHOLD}. "
            f"Conservando transcripción original."
        )
        return text

    print(
        f"[DECIA INTERPRETER] "
        f"Propuesta: \"{validation.corrected_text}\""
    )
    print(
        f"[DECIA INTERPRETER] "
        f"Confianza: {validation.confidence:.2f}"
    )
    print(
        "[DECIA INTERPRETER] "
        "Corrección aceptada."
    )

    return validation.corrected_text
