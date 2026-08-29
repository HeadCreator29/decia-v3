import re

from brain.intent_types import (
    ARCHIVE_DIRECT,
    ARCHIVE_SEARCH,
    MEMORY_SEARCH,
    TIME,
    DATE,
    PLANNER_CREATE,
    PLANNER_QUERY,
)

from utils.normalizer import normalize_strict

from utils.date_parser import PLANNER_DATE_MARKERS

from brain.handlers import (
    is_deictic_entity,
    PLANNER_TIME_ONLY_RE,
)


CONTEXT_CLARIFY = "CONTEXT_CLARIFY"


# ==========================================
# SEGUIMIENTO CONVERSACIONAL
# ==========================================
#
# Resuelve preguntas cortas de seguimiento
# ("y sobre X", "y qué día", "y entonces")
# únicamente cuando existe contexto relevante.
# Nunca inventa contexto por sí mismo.


_RE_Y_QUE_DIA = re.compile(
    r"^y\s+que\s+(dia|fecha)\b"
)

_RE_Y_EL_DIA = re.compile(
    r"^y\s+el\s+(dia|fecha)\b"
)

_RE_Y_LA_FECHA = re.compile(
    r"^y\s+la\s+fecha\b"
)

_RE_Y_QUE_HORA = re.compile(
    r"^y\s+que\s+hora\b"
)

_RE_Y_LA_HORA = re.compile(
    r"^y\s+la\s+hora\b"
)

_RE_Y_TEMPORAL = re.compile(
    r"^y\s+("
    r"ayer|hoy|anteayer"
    r"|esta\s+semana"
    r"|(?:la\s+)?semana\s+pasada"
    r"|(?:el\s+)?mes\s+pasado"
    r"|este\s+mes"
    r"|hace\s+(?:una?|\d+)\s+(?:dias?|semanas?|mes(?:es)?)"
    r"|el\s+(?:lunes|martes|miercoles|jueves"
    r"|viernes|sabado|domingo)"
    r")\b"
)

_TEMPORAL_ADVERBS = {
    "ayer",
    "hoy",
    "anteayer",
}

_RE_Y_QUE_MAS = re.compile(
    r"^y\s+(que\s+mas|entonces|algo\s+mas)\b"
)

_RE_Y_SOBRE = re.compile(
    r"^y\s+sobre\s+(.+)"
)

_RE_SOBRE = re.compile(
    r"^sobre\s+(.+)"
)

_QUESTION_WORDS = {
    "que", "quien", "quienes", "como",
    "cuando", "cual", "cuales", "donde",
    "por", "para",
}


def resolve_follow_up(message, context):

    if context is None:

        return None

    mode = getattr(
        context, "conversation_mode", None
    )

    last_intent = getattr(
        context, "last_intent", None
    )

    normalized = normalize_strict(message)

    if not normalized:

        return None

    fragment = _deictic_fragment(normalized)

    if fragment:

        antecedent = getattr(
            context, "last_entity", None
        )

        if (
            antecedent
            and not is_deictic_entity(
                antecedent
            )
        ):
            if (
                mode == "memory"
                or last_intent == MEMORY_SEARCH
            ):
                return (
                    MEMORY_SEARCH,
                    f"sobre {antecedent}",
                )

            if (
                mode == "archive"
                or last_intent in (
                    ARCHIVE_SEARCH,
                    ARCHIVE_DIRECT,
                )
            ):
                return (
                    ARCHIVE_SEARCH,
                    "que hay registrado "
                    f"sobre {antecedent}",
                )

        return (CONTEXT_CLARIFY, None)

    if not last_intent:

        return None

    # --------------------------------------
    # PLANNER (9.6): completar hora de un
    # recordatorio pendiente ("a las 9" tras
    # "recuérdame estudiar" + "mañana") y
    # "y <marcador>" como consulta del plan
    # (tras un PLANNER_CREATE/QUERY). Las
    # frases "y ..." NO clasifican
    # PLANNER_CREATE (guarda de continuidad
    # memory/archive en fase 8.13/8.15).
    # --------------------------------------

    planner_context = (
        mode == "planner"
        or last_intent in (
            PLANNER_CREATE, PLANNER_QUERY,
        )
    )

    if planner_context:

        base = normalized

        if base.startswith("y "):

            base = base[2:].strip()

        if PLANNER_TIME_ONLY_RE.match(base):

            return (PLANNER_CREATE, base)

        if re.fullmatch(
            PLANNER_DATE_MARKERS, base
        ):

            return (
                PLANNER_QUERY,
                f"que tengo {base}",
            )

    time_context = (
        mode == "time"
        or last_intent in (TIME, DATE)
    )

    search_context = (
        mode in ("archive", "memory")
        or last_intent in (
            ARCHIVE_SEARCH, MEMORY_SEARCH,
        )
    )

    # --------------------------------------
    # "Y QUÉ DÍA / QUÉ FECHA / EL DÍA / LA
    # FECHA" → DATE
    # --------------------------------------

    if (
        re.match(_RE_Y_QUE_DIA, normalized)
        or re.match(_RE_Y_EL_DIA, normalized)
        or re.match(_RE_Y_LA_FECHA, normalized)
    ):

        if time_context:

            return (DATE, "que dia es hoy")

        return None

    # --------------------------------------
    # "Y QUÉ HORA / Y LA HORA" → TIME
    # --------------------------------------

    if (
        re.match(_RE_Y_QUE_HORA, normalized)
        or re.match(_RE_Y_LA_HORA, normalized)
    ):

        if time_context:

            return (TIME, "que hora es")

        return None

    # --------------------------------------
    # "Y AYER / Y HOY" → MEMORY_SEARCH
    # --------------------------------------

    temporal = re.match(
        _RE_Y_TEMPORAL, normalized
    )

    # Solo contexto MEMORY: no fabricar una
    # búsqueda de memoria desde modo archive
    # (no pierde dominio).

    if (
        temporal
        and (
            mode == "memory"
            or last_intent == MEMORY_SEARCH
        )
    ):

        temporal_phrase = temporal.group(1)

        if temporal_phrase in _TEMPORAL_ADVERBS:

            query = f"que paso {temporal_phrase}"

        else:

            query = f"que hice {temporal_phrase}"

        return (MEMORY_SEARCH, query)

    # --------------------------------------
    # "Y QUÉ MÁS / Y ENTONCES" → REPETIR TEMA
    # --------------------------------------

    if re.match(_RE_Y_QUE_MAS, normalized):

        if mode == "archive":

            source = getattr(
                context,
                "previous_user_input",
                "",
            )

            intent = (
                ARCHIVE_DIRECT
                if last_intent == ARCHIVE_DIRECT
                else ARCHIVE_SEARCH
            )

            return (
                intent,
                source or "que hay registrado",
            )

        if mode == "memory":

            source = getattr(
                context,
                "previous_user_input",
                "",
            )

            return (
                MEMORY_SEARCH,
                source or "que recuerdas",
            )

        return None

    # --------------------------------------
    # "Y SOBRE X" / "SOBRE X" → BÚSQUEDA
    # --------------------------------------

    sobre = re.match(
        _RE_Y_SOBRE, normalized
    )

    if not sobre:

        sobre = re.match(
            _RE_SOBRE, normalized
        )

    if sobre and search_context:

        entity = _clean_entity(
            sobre.group(1)
        )

        if not entity:

            return None

        if mode == "memory":

            return (
                MEMORY_SEARCH,
                f"sobre {entity}",
            )

        return (
            ARCHIVE_SEARCH,
            f"que hay registrado sobre {entity}",
        )

    # --------------------------------------
    # "Y <ENTIDAD>" (continuación de tema)
    # --------------------------------------

    if (
        normalized.startswith("y ")
        and search_context
    ):

        rest = normalized[2:].strip()

        if (
            rest in _TEMPORAL_ADVERBS
            or not _is_entity_like(rest)
        ):

            return None

        if mode == "memory":

            return (
                MEMORY_SEARCH,
                f"sobre {rest}",
            )

        return (
            ARCHIVE_SEARCH,
            f"que hay registrado sobre {rest}",
        )

    return None


# ==========================================
# AUXILIARES
# ==========================================


def _clean_entity(raw):

    entity = raw.strip().strip(".,;:!?")

    if not entity:

        return None

    if len(entity.split()) > 4:

        return None

    return entity


def _is_entity_like(text):

    words = text.split()

    if not words or len(words) > 3:

        return False

    if _QUESTION_WORDS.intersection(words):

        return False

    return True


def _deictic_fragment(normalized):

    text = normalized

    if text.startswith("y "):

        text = text[2:].strip()

    if text.startswith("sobre "):

        text = text[6:].strip()

    if not text:

        return False

    return is_deictic_entity(text)