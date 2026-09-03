import re

from datetime import datetime, timedelta

import utils.date_parser as _dp

from services.archive import (
    get_identity,
    save_identity,
    get_user,
    save_user,
    search_archive,
    save_memory,
    get_history,
)

from services.planner import (
    save_plan,
    query_plans,
    update_plan_time,
    load_plans,
)

from services.plugins.decision import DecisionPlugin
from services.plugins.prediction import PredictionPlugin
from services.plugins.learning import LearningPlugin
from services.plugins.reflection import ReflectionPlugin

from personality.personality import (
    NAME,
    ROLE,
)

from utils.normalizer import (
    normalize,
    normalize_strict,
)

from utils.math_eval import safe_eval

from utils.date_parser import (
    get_month_name,
    parse_memory_datetime,
    format_date_spanish,
    parse_relative_time,
    plan_relative_datetime,
    PLANNER_DATE_MARKERS,
)


# ==========================================
# RESPUESTAS RÁPIDAS
# ==========================================


def quick_response(message):

    message = normalize_strict(message)

    greetings = [
        "hola",
        "buenas",
        "buenos dias",
        "buenas tardes",
        "buenas noches",
    ]

    if any(g in message for g in greetings):

        return (
            "¡Hola! Soy DECIA. "
            "¿En qué puedo ayudarte?"
        )

    if "gracias" in message:

        return "De nada."

    return None


# ==========================================
# IDENTIDAD DE DECIA
# ==========================================


def identity_response(message):

    message = normalize_strict(message)

    # --------------------------------------
    # IDENTIDAD DE DECIA
    # --------------------------------------

    questions = [
        "quien eres",
        "que eres",
        "como te llamas",
        "cual es tu nombre",
        "que es decia",
        "hablame de decia",
        "hablame sobre decia",
        "que significa decia",
        "quien es decia",
        "cual es tu proposito",
        "para que sirves",
        "de donde vienes",
        "para que estas creada",
        "cuales son tus funciones",
    ]

    if any(q in message for q in questions):

        return (
            f"Soy {NAME}, "
            f"{ROLE.strip()}"
        )

    # --------------------------------------
    # QUIÉN TE CREÓ
    # --------------------------------------

    creator_questions = [
        "quien te creo",
        "quien te creó",
        "quien es tu creador",
        "quien es tu creadora",
        "quien hizo",
        "quien te hizo",
        "como te crearon",
        "como naciste",
    ]

    for pattern in creator_questions:

        if pattern in message:

            identity = get_identity()

            creator = identity.get(
                "creator", "Idelvi"
            )

            return (
                f"Fui creada por {creator}, "
                f"el fundador de DECA."
            )

    return None


# ==========================================
# IDENTIDAD PERSONAL (PREFERRED NAME)
# ==========================================


def personal_identity_handler(message):

    message_norm = normalize_strict(message)

    user = get_user()

    # --------------------------------------
    # A) CONSULTAR NOMBRE REAL → user_name
    # --------------------------------------

    user_name_ask = [
        "como me llamo",
        "cual es mi nombre",
        "cuales es mi nombre",
        "que nombre tienes para mi",
        "por que nombre me llamas",
        "como me tienes guardado",
        "quien soy",
        "y quien soy",
    ]

    for pattern in user_name_ask:

        if pattern in message_norm:

            name = user.get(
                "user_name", "Idelvi"
            )

            return f"Tu nombre es {name}."

    # --------------------------------------
    # B) CONSULTAR NOMBRE DE TRATO
    #    → preferred_name
    # --------------------------------------

    if (
        "como quieres llamarme"
        in message_norm
    ):

        name = user.get(
            "preferred_name", "Creador"
        )

        return (
            f"Quiero llamarte {name}."
        )

    # --------------------------------------
    # B2) "¿CÓMO ME LLAMAS?" / "¿CÓMO
    #     ME LLAMA?" → preferred_name
    # --------------------------------------

    if (
        "como me llama"
        in message_norm
    ):

        name = user.get(
            "preferred_name", "Creador"
        )

        return (
            f"Te llamo {name}."
        )

    # --------------------------------------
    # E) "LLÁMAME" SIN NOMBRE → PEDIR NOMBRE
    # --------------------------------------

    if re.match(
        r"llamame\s*$", message_norm
    ):

        return (
            "¿Cómo quieres que te llame? "
            "Dime un nombre."
        )

    # --------------------------------------
    # C) DECLARAR NOMBRE REAL → user_name
    # --------------------------------------

    user_name_declare = [
        r"mi nombre es\s+(.+)",
        r"el nombre mio es\s+(.+)",
        r"nombre mio es\s+(.+)",
        r"me llamo\s+(.+)",
        r"yo me llamo\s+(.+)",
        r"el mio es\s+(.+)",
        r"ese es mi nombre\s+(.+)",
    ]

    for pattern in user_name_declare:

        match = re.search(
            pattern, message_norm
        )

        if match:

            new_name = _extract_name(
                match.group(1)
            )

            if not new_name:

                continue

            user[
                "user_name"
            ] = new_name

            save_user(user)

            return (
                f"Entendido. "
                f"Tu nombre es {new_name}."
            )

    # --------------------------------------
    # D) PREFERENCIA DE TRATO
    #    → preferred_name
    # --------------------------------------

    preferred_name_declare = [
        r"puedes llamarme\s+(.+)",
        r"quiero que me llames\s+(.+)",
        r"me vas a llamar\s+(.+)",
        r"vas a llamarme\s+(.+)",
        r"desde ahora llamame\s+(.+)",
        r"de ahora en adelante llamame\s+(.+)",
        r"llamame\s+(.+)",
    ]

    for pattern in preferred_name_declare:

        match = re.search(
            pattern, message_norm
        )

        if match:

            new_name = _extract_name(
                match.group(1)
            )

            if not new_name:

                continue

            user[
                "preferred_name"
            ] = new_name

            save_user(user)

            return (
                f"De ahora en adelante "
                f"te llamaré {new_name}."
            )

    return None


def _extract_name(raw):

    name = raw.split(",")[0]

    name = name.strip().strip(".,;:!?")

    name = name.strip()

    if not name:

        return None

    return name.capitalize()


# ==========================================
# CÁLCULOS
# ==========================================


def calculate(message):

    message = normalize(message).strip()

    message = message.replace("¿", "")
    message = message.replace("?", "")
    message = message.replace("¡", "")
    message = message.replace("!", "")

    message = re.sub(
        r"^(cuanto\s+es|que\s+es|calcular)\s+",
        "", message,
    )

    message = message.replace(" mas ", "+")
    message = message.replace(" menos ", "-")
    message = message.replace(" por ", "*")
    message = message.replace(" entre ", "/")

    message = re.sub(r"\s*[x×]\s*", "*", message)

    pattern = r"^[\d\s\+\-\*\/\(\)\.]+$"

    if not re.match(pattern, message):

        return None

    result = safe_eval(message)

    if result is None:

        return None

    return str(result)


# ==========================================
# HORA Y FECHA
# ==========================================


DIAS_SEMANA = {
    0: "lunes", 1: "martes", 2: "miércoles",
    3: "jueves", 4: "viernes", 5: "sábado",
    6: "domingo",
}


def _relative_day_offset(normalized):

    if "anteayer" in normalized:

        return -2

    if "ayer" in normalized:

        return -1

    if "manana" in normalized:

        return 1

    return 0


def time_response(message):

    normalized = normalize_strict(message)

    now = datetime.now()

    is_date = (
        "fecha" in normalized
        or "dia" in normalized
    )

    if is_date:

        offset = _relative_day_offset(normalized)

        target = now + timedelta(days=offset)

        weekday = DIAS_SEMANA[target.weekday()]
        month = get_month_name(f"{target.month:02d}")

        if offset == -1:

            return (
                f"Ayer fue {weekday} "
                f"{target.day} de {month} "
                f"de {target.year}."
            )

        if offset == -2:

            return (
                f"Anteayer fue {weekday} "
                f"{target.day} de {month} "
                f"de {target.year}."
            )

        if offset == 1:

            return (
                f"Mañana será {weekday} "
                f"{target.day} de {month} "
                f"de {target.year}."
            )

        return (
            f"Hoy es {weekday} "
            f"{target.day} de {month} "
            f"de {target.year}."
        )

    hour = now.hour
    minute = now.minute

    period = (
        "de la mañana"
        if 6 <= hour < 12
        else "de la tarde"
        if 12 <= hour < 19
        else "de la noche"
    )

    display_hour = hour if hour <= 12 else hour - 12

    if hour == 0:

        display_hour = 12

    if minute == 0:

        return (
            f"Son las {display_hour} "
            f"en punto {period}."
        )

    return (
        f"Son las {display_hour}:{minute:02d} "
        f"{period}."
    )


# ==========================================
# ARCHIVO DECA
# ==========================================


def archive_response(message):

    message = normalize(message)

    try:

        identity = get_identity()

    except Exception:

        return None

    # --------------------------------------
    # CUÁNDO COMENZÓ DECA
    # --------------------------------------

    if (
        "cuando comenzo deca" in message
        or "cuando empezo deca" in message
    ):

        date = identity["origin"]["date"]

        return (
            f"DECA comenzó el "
            f"{format_date_spanish(date)}."
        )

    # --------------------------------------
    # ORIGEN DE DECA
    # --------------------------------------

    if (
        "origen de deca" in message
        or "de donde viene deca" in message
    ):

        return identity["origin"]["description"]

    # --------------------------------------
    # QUÉ SIGNIFICA DECA
    # --------------------------------------

    if (
        "que significa deca" in message
        or "significado de deca" in message
    ):

        return identity["meaning"]

    # --------------------------------------
    # VALORES
    # --------------------------------------

    if (
        "valores de deca" in message
        or "cuales son los valores de deca"
        in message
    ):

        values = ", ".join(
            identity["values"]
        )

        return (
            "Los valores fundamentales de DECA son: "
            f"{values}."
        )

    # --------------------------------------
    # VISIÓN
    # --------------------------------------

    if (
        "vision de deca" in message
        or "cual es la vision de deca"
        in message
    ):

        return identity["vision"]

    # --------------------------------------
    # QUIÉN CREÓ DECA
    # --------------------------------------

    if (
        "quien creo deca" in message
        or "quien es el creador de deca"
        in message
    ):

        return (
            f"DECA fue creado por "
            f"{identity['creator']}."
        )

    # --------------------------------------
    # HÁBLAME / CUÉNTAME DE DECA
    # --------------------------------------

    if (
        "hablame de deca" in message
        or "cuentame de deca" in message
        or "cuentame un poco sobre deca"
        in message
        or "que es deca" in message
        or "cuentame sobre deca" in message
        or "hablame sobre deca" in message
    ):

        return identity["meaning"]

    return None


# ==========================================
# HISTORIA GENERAL (G6)
# ==========================================


_HISTORY_BARE_RE = re.compile(
    r"^(?:q|que)\s+(?:paso|sucedio|"
    r"ocurrio|hubo|acontecio)\s*$",
    re.IGNORECASE,
)


def history_response(message):
    # G6: consulta histórica desnuda (sin entidad
    # y sin referencia temporal, p. ej. "que paso",
    # "qué sucedió", "que hubo"). NO consulta
    # memories.json ni OLLAMA: responde con el
    # archivo de historia (history.json) y, si no
    # hay contenido, con un aviso determinista
    # de archivo.
    if not _HISTORY_BARE_RE.match(
        normalize_strict(message)
    ):

        return None

    try:

        history = get_history()

    except Exception:

        history = None

    events = (
        (history or {}).get("events") or []
    )

    if not events:

        return (
            "No encontré información "
            "registrada en el archivo."
        )

    return format_archive_response({
        "field": "events",
        "data": events,
    })


# ==========================================
# MEMORIA INTELIGENTE
# ==========================================


def search_deca_memory(message, prefer_field=None):

    try:

        results = search_archive(message)

    except Exception:

        return None

    if not results:

        return None

    if prefer_field:

        field_results = [
            r
            for r in results
            if r.get("field") == prefer_field
        ]

        if field_results:

            best_result = field_results[0]

        else:

            best_result = results[0]

    else:

        best_result = results[0]

    if best_result["score"] < 80:

        return None

    print(
        f"[DECIA ARCHIVE] "
        f"Memoria encontrada: "
        f"{best_result['file']} | "
        f"campo={best_result['field']} | "
        f"score={best_result['score']}"
    )

    return best_result


# ==========================================
# ENTIDAD DE BÚSQUEDA ("SOBRE X")
# ==========================================


_SEARCH_ENTITY_RE = re.compile(
    r"\b(?:sobre|con)\s+(.+)$",
    re.IGNORECASE,
)

_ENTITY_STOP_WORDS = {
    "que", "de", "el", "la", "los", "las",
    "del", "lo", "un", "una", "mi", "tu",
}

_ENTITY_TEMPORAL_STOP_WORDS = {
    "hoy", "ayer", "anteayer",
    "manana", "mañana",
    "dia", "dias", "día", "días",
    "semana", "semanas",
    "mes", "meses",
    "pasado", "pasada", "pasados",
    "pasadas",
    "hace",
    "lunes", "martes", "miercoles",
    "miércoles", "jueves", "viernes",
    "sabado", "sábado", "domingo",
}

_DEICTIC_PRONOUNS = {
    "este", "esta", "esto",
    "ese", "esa", "eso",
    "aquel", "aquella", "aquello",
    "el", "ella", "ello",
    "ellos", "ellas",
    "los", "las",
    "lo mismo",
    "esto mismo", "eso mismo",
    "aquel mismo",
}

_ENTITY_TEMPORAL_CONNECTORS = (
    _DEICTIC_PRONOUNS
    | {
        "el", "la", "los", "las",
        "del", "de", "al",
        "un", "una", "en",
    }
)


def is_deictic_entity(entity):

    if not entity:

        return False

    normalized = normalize_strict(entity)

    return (
        normalized in _DEICTIC_PRONOUNS
    )


def _clean_entity_temporal(entity):
    # G7: separa la entidad limpia de la cola
    # temporal. Reutiliza la des-contaminación
    # temporal existente (_ENTITY_TEMPORAL_STOP_WORDS);
    # solo se recorta la cola temporal CONTIGUA al
    # final (palabras temporales + sus conectores
    # inmediatos), para no mutilar determinantes
    # del sintagma de la entidad ("la seleccion el
    # lunes" -> "la seleccion") ni frases con el
    # temporal en posición interior ("la semana
    # pasada en canada" no se toca).
    words = entity.split()

    cleaned = []

    seen_temporal = False

    done = False

    for word in reversed(words):

        if done:

            cleaned.insert(0, word)

            continue

        normalized = normalize_strict(word)

        if (
            normalized
            in _ENTITY_TEMPORAL_STOP_WORDS
        ):

            seen_temporal = True

            continue

        if seen_temporal and (
            normalized
            in _ENTITY_TEMPORAL_CONNECTORS
            or word.isdigit()
        ):

            continue

        cleaned.insert(0, word)

        done = True

    result = " ".join(cleaned)

    return result.strip(".,;:!?")


def extract_search_entity(message):

    match = _SEARCH_ENTITY_RE.search(
        message
    )

    if not match:

        return None

    entity = match.group(1).strip()
    entity = entity.strip(".,;:!?")

    if not entity:

        return None

    entity = _clean_entity_temporal(entity)

    if not entity:

        return None

    return entity


def filter_memories_by_entity(result, entity):

    if not entity:

        return result

    if not isinstance(result, dict):

        return result

    if result.get("field") not in (
        "memories", "events",
    ):

        return result

    words = re.findall(
        r"[a-zñáéíóúü]+",
        entity.lower(),
    )

    words = [
        w for w in words
        if w not in _ENTITY_STOP_WORDS
    ]

    if not words:

        return None

    # Las palabras temporales de la frase
    # contaminan la entidad de búsqueda
    # ("sobre kanye la semana pasada");
    # si tras removerlas no queda entidad
    # real, se devuelve el resultado tal
    # cual (la fecha ya filtró la búsqueda).

    entity_words = [
        w for w in words
        if w not in _ENTITY_TEMPORAL_STOP_WORDS
    ]

    if not entity_words:

        return result

    words = entity_words

    items = result.get("data") or []

    matched = []

    for item in items:

        haystack = " ".join((
            str(item.get(
                "description", ""
            )),
            str(item.get(
                "title", ""
            )),
            str(item.get(
                "date", ""
            )),
        )).lower()

        if any(
            _entity_word_matches(
                word, haystack,
            )
            for word in words
        ):

            matched.append(item)

    field = result.get("field")

    if not matched:

        # MEMORY sin coincidencia mantiene su
        # contrato: None (core responde el aviso
        # de memoria). EVENTS sin coincidencia
        # conserva el dominio archive con data
        # vacía para que MEMORY no suplante
        # EVENTS (igual que el filtro temporal
        # vacío de 8.9C/G4).
        if field == "memories":

            return None

        data = []

        total = 0

    else:

        data = matched[:20]

        total = len(matched)

    filtered = dict(result)

    filtered["data"] = data

    filtered["total"] = total

    return filtered


def _entity_word_matches(word, haystack):

    haystack_words = haystack.split()

    if word in haystack:

        return True

    for hword in haystack_words:

        if (
            len(word) >= 3
            and len(hword) >= 3
            and (
                word in hword
                or hword in word
            )
        ):

            return True

        if (
            len(word) >= 4
            and len(hword) >= 4
        ):

            limit = min(
                len(word), len(hword)
            )

            shared = 0

            while (
                shared < limit
                and word[shared]
                == hword[shared]
            ):

                shared += 1

            if shared >= 3:

                return True

    return False


# ==========================================
# FORMATEAR ARCHIVO
# ==========================================


def format_archive_response(result):

    field = result["field"]
    data = result["data"]

    # --------------------------------------
    # SIGNIFICADO
    # --------------------------------------

    if field == "meaning":

        return data

    # --------------------------------------
    # ORIGEN
    # --------------------------------------

    if field == "origin":

        date = data["date"]

        return (
            f"DECA comenzó el "
            f"{format_date_spanish(date)}."
        )

    # --------------------------------------
    # VISIÓN
    # --------------------------------------

    if field == "vision":

        return data

    # --------------------------------------
    # VALORES
    # --------------------------------------

    if field == "values":

        return (
            "Los valores fundamentales de DECA son: "
            + ", ".join(data)
            + "."
        )

    # --------------------------------------
    # CREADOR
    # --------------------------------------

    if field == "creator":

        return (
            f"DECA fue creado por {data}."
        )

    # --------------------------------------
    # HISTORIA
    # --------------------------------------

    if field == "events":

        responses = []

        for event in data:

            date = event.get("date", "")
            title = event.get("title", "")
            description = event.get(
                "description", ""
            )

            if date:

                formatted = (
                    format_date_spanish(date)
                )

                responses.append(
                    f"{formatted} — "
                    f"{title}: "
                    f"{description}"
                )

            else:

                responses.append(
                    f"{title}: {description}"
                )

        return "\n".join(responses)

    # --------------------------------------
    # MEMORIAS
    # --------------------------------------

    if field == "memories":

        responses = []

        for memory in data:

            date = memory.get("date", "")
            time = memory.get("time")
            description = memory.get(
                "description", ""
            )

            if time:

                responses.append(
                    f"{date} a las {time} — "
                    f"{description}"
                )

            else:

                responses.append(
                    f"{date} — "
                    f"{description}"
                )

        total = result.get("total")

        if (
            total is not None
            and len(data) < total
        ):

            remaining = total - len(data)

            responses.append(
                f"… y {remaining} más."
            )

        return "\n".join(responses)

    return None


# ==========================================
# DECISION FLOWS HANDLERS
# ==========================================


def handle_decision_create(message, entities, context) -> str:
    """Handle DECISION_CREATE intent.

    Creates a new decision record from conversation input.
    Returns a confirmation message.

    Expected entities:
        decision_problem: {problem, arguments, decision, rationale, confidence}
    """
    plugin = DecisionPlugin()

    problem = entities.get("decision_problem", {}).get("problem", "")
    arguments = entities.get("decision_problem", {}).get("arguments", [])
    decision = entities.get("decision_problem", {}).get("decision", "")
    rationale = entities.get("decision_problem", {}).get("rationale", "")
    confidence = entities.get("decision_problem", {}).get("confidence", 0.7)

    if not problem or not decision:
        return "No identifiqué un problema de decisión claro. ¿Podrías reformular?"

    result = plugin.create(
        problem=problem,
        arguments=arguments or ["No specified"],
        decision=decision,
        rationale=rationale or "No rationale provided",
        confidence=confidence,
    )

    decision_id = result["id"]
    status = result["status"]

    return (
        f"Decision registrada con ID {decision_id}. "
        f"Estado: {status}. "
        f"Puedo confirmarla later con 'confirmo decisión' y el resultado."
    )


def handle_decision_confirm(message, entities, context) -> str:
    """Handle DECISION_CONFIRM intent.

    Confirms a decision with outcome and learning.
    Links the decision to relevant memories.

    Expected entities:
        decision_id: The decision UUID string
        outcome: The result outcome
        learning: Learning from the outcome
        memory_ids: Optional list of memory IDs to link
    """
    plugin = DecisionPlugin()

    decision_id = entities.get("decision_id", "")
    outcome = entities.get("outcome", "")
    learning = entities.get("learning", "")
    memory_ids = entities.get("memory_ids", [])

    if not decision_id:
        return "No identifiqué un ID de decisión. ¿De qué decisión hablas?"

    result = plugin.confirm(
        decision_id=decision_id,
        outcome=outcome or "No outcome specified",
        learning=learning or "No learning recorded",
    )

    if result is None:
        return f"No encontré una decisión con ID {decision_id}."

    status = result["status"]

    # Link memories if provided
    for memory_id in (memory_ids or []):
        plugin.link_memory(
            decision_id=decision_id,
            memory_id=memory_id,
            relation_type="supports",
        )

    return (
        f"Decision {decision_id} confirmada. "
        f"Estado: {status}. "
        f"Outcome: {outcome}. "
        f"Learning: {learning}. "
        f"Memorias vinculadas: {len(memory_ids) or 0}."
    )


# ==========================================
# REFLECTION FLOWS HANDLERS
# ==========================================


def handle_reflection_create(message, entities, context) -> str:
    """Handle REFLECTION_CREATE intent.

    Creates a new reflection draft from conversation input.
    Returns a confirmation message.

    Expected entities:
        reflection_text: The reflection text content (string or dict)
    """
    plugin = ReflectionPlugin()

    reflection_text = entities.get("reflection_text", "")
    # Handle both string and dict entity formats
    if isinstance(reflection_text, dict):
        reflection_text = reflection_text.get("reflection_text", "")

    if not reflection_text:
        return "No identifiqué un texto de reflexión claro. ¿Podrías reformular?"

    result = plugin.draft(
        conversation_id=context.get("conversation_id", "") if context else "",
        draft_content=reflection_text,
    )

    reflection_id = result["id"]
    status = result["status"]

    return (
        f"Borrador de reflexión registrado con ID {reflection_id}. "
        f"Estado: {status}. "
        f"Puedo aprobarla later con 'aprobar reflexión' y el contenido."
    )


def handle_reflection_approve(message, entities, context) -> str:
    """Handle REFLECTION_APPROVE intent.

    Approves/edits a reflection draft.
    Returns a confirmation message.

    Expected entities:
        reflection_id: The reflection UUID string
        edited_content: Optional user edits/approval content
    """
    plugin = ReflectionPlugin()

    reflection_id = entities.get("reflection_id", "")
    edited_content = entities.get("edited_content", "")

    if not reflection_id:
        return "No identifiqué un ID de reflexión. ¿De qué reflexión hablas?"

    result = plugin.approve(
        reflection_id=reflection_id,
        edited_content=edited_content or "",
    )

    if result is None:
        return f"No encontré una reflexión con ID {reflection_id}."

    status = result["status"]

    if status == "APPROVED":
        return (
            f"Reflexión {reflection_id} aprobada. "
            f"Contenido: '{result['approved_content']}'."
        )
    else:
        return (
            f"Reflexión {reflection_id} en borrador. "
            f"Estado: {status}."
        )


# ==========================================
# PREDICTION FLOWS HANDLERS
# ==========================================


def handle_prediction_create(message, entities, context) -> str:
    """Handle PREDICTION_CREATE intent.

    Creates a new prediction record from conversation input.
    Returns a confirmation with review date.

    Expected entities:
        prediction_text: The prediction statement
        horizons: List of horizon dicts with {label, timeframe, target_date}
        confidence: Initial confidence score (0.0-1.0)
        reasons: List of reason strings
    """
    plugin = PredictionPlugin()

    prediction_text = entities.get("prediction_text", {}).get("prediction_text", "")
    horizons = entities.get("prediction_text", {}).get("horizons", [])
    confidence = entities.get("prediction_text", {}).get("confidence", 0.5)
    reasons = entities.get("prediction_text", {}).get("reasons", [])

    if not prediction_text:
        return "No identifiqué un texto de predicción claro. ¿Podrías reformular?"

    result = plugin.create(
        prediction_text=prediction_text,
        horizons=horizons or [],
        confidence=confidence,
        reasons=reasons or [],
    )

    prediction_id = result["id"]
    status = result["status"]

    # Schedule initial review date (7 days from now)
    from datetime import datetime, timedelta, timezone

    review_date = (datetime.now().astimezone() + timedelta(days=7)).isoformat()
    plugin.schedule_review(prediction_id=prediction_id, review_date=review_date)

    return (
        f"Predicción registrada con ID {prediction_id}. "
        f"Estado: {status}. "
        f"Puedo revisarla later con 'revisar predicción' y el resultado. "
        f"Fecha de revisión: {review_date[:10]}."
    )


def handle_prediction_review(message, entities, context) -> str:
    """Handle PREDICTION_REVIEW intent.

    Shows due/upcoming predictions and allows resolution.

    Expected entities:
        prediction_id: The prediction UUID string (optional)
    """
    plugin = PredictionPlugin()

    prediction_id = entities.get("prediction_id", "")

    if prediction_id:
        # Get specific prediction
        prediction = plugin.get_by_id(prediction_id)
        if prediction is None:
            return f"No encontré una predicción con ID {prediction_id}."

        return (
            f"Predicción ID {prediction_id}: "
            f"'{prediction['prediction_text']}' "
            f"Estado: {prediction['status']}. "
            f"Confianza: {prediction['confidence']}. "
            f"Horizontes: {len(prediction.get('horizons', []))}. "
            f"Razón: {prediction.get('reasons', ['Ninguna'])[0]}."
        )
    else:
        # Show due reviews
        due = plugin.get_due_reviews()
        all_preds = plugin.get_by_status("OPEN")

        if due:
            lines = []
            for p in due[:5]:  # Show max 5
                review_date = p.get("review_date", "sin fecha")
                lines.append(
                    f"- ID {p['id']}: '{p['prediction_text'][:50]}...' "
                    f"Estado: {p['status']} | "
                    f"Revisar: {review_date[:10] if review_date else 'pendiente'}"
                )
            return "Predicciones por revisar:\n" + "\n".join(lines)

        if all_preds:
            return (
                f"No tienes predicciones por revisar en este momento. "
                f"Tienes {len(all_preds)} predicción(iones) abierta(s)."
            )

        return "No tienes predicciones registradas."

    # ==========================================
    # NEAR-BARE HISTÓRICO AMBIGUO (8.12)
# Whitelist de consultas histórico-ambiguas
# incompletas: clarificación determinista,
# sin búsqueda en history.json ni OLLAMA.
# ==========================================


_NEAR_BARE_HISTORICAL_RE = re.compile(
    r"^(?:que\s+hubo\s+(?:algo|alguien)|"
    r"que\s+paso\s+(?:cuando\s+llegue|"
    r"despues|luego)|"
    r"que\s+sucedio\s+cuando\s+llegue)$",
)


def ambiguous_input_response(message):

    if "?" in message:

        return None

    message = normalize_strict(message)

    # 8.12: near-bare históricas ambiguas e incompletas
    # ("que hubo algo", "que paso cuando llegue", etc.)
    # SON ambiguas, NO HISTORY: ruta determinista de
    # clarificación, 0 búsquedas, 0 OLLAMA. Whitelist
    # explícita (sin regex amplio).
    if _NEAR_BARE_HISTORICAL_RE.match(message):

        return "¿Sí? ¿Qué necesitas?"

    words = message.split()

    if len(words) > 2:

        return None

    intent_keywords = [
        "hola",
        "buenas",
        "gracias",
        "decia",
        "guarda",
        "recuerda",
        "anota",
        "memoriza",
        "calcula",
        "cuanto",
        "cuantos",
        "cuanta",
        "cuantas",
        "suma",
        "resta",
        "multiplica",
        "divide",
        "estas",
        "tal",
        "cuentame",
        "aburrido",
        "cansado",
    ]

    for keyword in intent_keywords:

        if keyword in message:

            return None

    return (
        "¿Sí? ¿Qué necesitas?"
    )


# ==========================================
# DETECTAR NUEVA MEMORIA
# ==========================================


TRIGGERS = [
    "guarda que",
    "guarda esto",
    "recuerda que",
    "recuerda esto",
    "anota que",
    "anota esto",
    "memoriza que",
    "quiero que recuerdes",
    "quiero que guardes",
]


def memory_request(message):

    normalized = normalize_strict(message)

    if normalized.startswith("decia"):

        normalized = normalized[5:].strip()

    for trigger in TRIGGERS:

        if normalized.startswith(trigger):

            content = normalized[
                len(trigger):
            ].strip()

            if content:

                return content

    return None


# ==========================================
# CREAR MEMORIA
# ==========================================


def create_memory(content):

    print(
        "[DECIA MEMORY] "
        f"CREATE_MEMORY | "
        f"description=\"{content}\""
    )

    now = datetime.now().astimezone()

    memory_time = parse_memory_datetime(
        content
    )

    memory = {

        "id": now.strftime(
            "mem_%Y%m%d_%H%M%S_%f"
        ),

        "timestamp": now.isoformat(
            timespec="seconds"
        ),

        "date": memory_time["date"],

        "time": memory_time["time"],

        "recorded_at": now.strftime(
            "%Y-%m-%d %H:%M:%S"
        ),

        "type": "actividad",

        "title": "Memoria de DECIA",

        "description": content,
    }

    try:

        result = save_memory(memory)

    except Exception as error:

        print(
            f"[DECIA MEMORY] "
            f"Error al guardar: {error}"
        )

        result = False

    print(
        "[DECIA MEMORY] "
        "SAVE_MEMORY | result="
        + (
            "created"
            if result is True
            else "duplicate"
            if result == "duplicate"
            else "error"
        )
    )

    memory["saved"] = result == True

    memory["duplicate"] = result == "duplicate"

    return memory


# ==========================================
# PLANNER (PHASE 9.6) — EVENTOS Y
# RECORDATORIOS FUTUROS
# ==========================================
#
# Rutas deterministas: NUNCA OLLAMA y NUNCA
# escriben en memories.json. Guardan en el
# archivo propio data/archive/planner.json vía
# services.planner (escritura atómica, dedup
# exacto por (kind, fecha, hora o "", desc)).
# Reloj: usan utils.date_parser.datetime (el
# mismo que @_seed_clock congela en los tests);
# handlers.datetime NO se usa aquí.
# ==========================================


_PLANNER_TIME_SOURCE = (
    r"a\s+las\s+\d{1,2}(?::\d{2})?\s*"
    r"(?:de\s+la\s+ma[n\u00f1]ana|de\s+la"
    r"\s+tarde|de\s+la\s+noche|am|pm)?"
)

_PLANNER_TIME_RE = re.compile(
    _PLANNER_TIME_SOURCE
)

PLANNER_TIME_ONLY_RE = re.compile(
    r"^(?:y\s+)?" + _PLANNER_TIME_SOURCE + r"$"
)

_PLANNER_MARKER_RE = re.compile(
    PLANNER_DATE_MARKERS
)

_PLANNER_WORD = {
    "event": "evento",
    "reminder": "recordatorio",
}


def _tokens_in_span(tokens, start, end):
    # Índices de tokens (normalizados, con
    # espacios simples) que se solapan con el
    # rango [start, end) del texto normalizado.
    selected = []

    pos = 0

    for index, token in enumerate(tokens):

        t_start = pos

        t_end = t_start + len(token)

        if t_start < end and t_end > start:

            selected.append(index)

        pos = t_end + 1

    return selected


def _planner_description(raw):
    # Descripción VERBATIM del plan: se eliminan
    # del mensaje original el disparador
    # ("decia"?/"recuerdame"), todos los
    # marcadores de fecha futura y la expresión
    # de hora, alineando tokens raw ↔ tokens
    # normales (normalize_strict solo quita
    # puntuación y colapsa espacios).
    raw_words = raw.split()

    if not raw_words:

        return None

    normalized = normalize_strict(raw)

    norm_tokens = normalized.split()

    drop = set()

    index = 0

    if (
        norm_tokens
        and norm_tokens[0] == "decia"
        and len(norm_tokens) > 1
    ):

        drop.add(0)

        index = 1

    if (
        index < len(norm_tokens)
        and norm_tokens[index] == "recuerdame"
    ):

        drop.add(index)

        index += 1

    for match in _PLANNER_MARKER_RE.finditer(
        normalized
    ):

        for i in _tokens_in_span(
            norm_tokens,
            match.start(),
            match.end(),
        ):

            drop.add(i)

    time_match = _PLANNER_TIME_RE.search(
        normalized
    )

    if time_match:

        for i in _tokens_in_span(
            norm_tokens,
            time_match.start(),
            time_match.end(),
        ):

            drop.add(i)

    kept = [
        word
        for j, word in enumerate(raw_words)
        if j not in drop
    ]

    description = (
        " ".join(kept).strip(" .,;:!?")
    )

    if description == "y":

        description = None

    return description or None


def _split_coordinated_clauses(normalized):
    # Split simple coordination "X y Y" where both parts
    # have planner markers. Returns list of clause strings
    # or None if no coordination detected.
    parts = normalized.split(" y ")
    if len(parts) != 2:
        return None
    # Check both parts have planner date markers
    has_marker_0 = bool(_PLANNER_MARKER_RE.search(parts[0]))
    has_marker_1 = bool(_PLANNER_MARKER_RE.search(parts[1]))
    if has_marker_0 and has_marker_1:
        return parts
    # Also check for time markers in both parts
    has_time_0 = bool(_PLANNER_TIME_RE.search(parts[0]))
    has_time_1 = bool(_PLANNER_TIME_RE.search(parts[1]))
    if has_time_0 and has_time_1:
        return parts
    # Pattern: first clause has date marker, second has time only
    # e.g., "manana tengo clase y a las 3 reunion"
    if has_marker_0 and has_time_1 and not has_marker_1:
        return parts
    return None


def _planner_time_only(normalized):

    return bool(
        PLANNER_TIME_ONLY_RE.match(normalized)
    )


def _find_pending_null_time_plan(
    kind, date, description
):

    try:

        plans = load_plans().get("plans", [])

    except Exception:

        return None

    target = normalize(description)

    for plan in plans:

        if (
            plan.get("kind") == kind
            and plan.get("due_date") == date
            and not plan.get("due_time")
            and plan.get("status") == "pending"
            and normalize(
                plan.get("description", "")
            ) == target
        ):

            return plan

    return None


def planner_create(message, context=None):

    raw = message

    normalized = normalize_strict(raw)

    now = _dp.datetime.now().astimezone()

    # --------------------------------------
    # BORRADOR PREVIO (flujo en dos pasos)
    # --------------------------------------

    draft_kind = None

    draft_desc = None

    draft_prev = None

    if context is not None:

        if (
            getattr(context, "conversation_mode", None)
            == "planner"
        ):

            topic = getattr(context, "last_topic", None)

            if topic in ("event", "reminder"):

                draft_kind = topic

                draft_desc = getattr(
                    context, "last_entity", None
                )

                draft_prev = getattr(
                    context,
                    "previous_user_input",
                    None,
                )

    # --------------------------------------
    # TIPO (evento vs recordatorio)
    # --------------------------------------

    base = normalized

    if base.startswith("decia "):

        base = base[6:].strip()

    msg_kind = (
        "reminder"
        if base.startswith("recuerdame")
        else "event"
    )

    kind = draft_kind or msg_kind

    # --------------------------------------
    # COORDINACIÓN SIMPLE: "X y Y"
    # Detectar y procesar dos cláusulas con marcadores
    # --------------------------------------

    clauses = _split_coordinated_clauses(normalized)
    if clauses is not None:
        responses = []
        final_desc = None
        final_kind = kind
        shared_date = None
        shared_date_str = None
        
        for i, clause in enumerate(clauses):
            # Process each clause
            sub_raw = clause
            sub_normalized = normalize_strict(sub_raw)
            sub_due_date = _dp.plan_relative_datetime(sub_normalized, now)
            sub_due_time = parse_relative_time(sub_raw)
            
            # For second clause with time only, use shared date from first clause
            if i == 1 and sub_due_date is None and sub_due_time is not None and shared_date is not None:
                sub_due_date = shared_date
            
            # Apply same morning-time default logic
            if sub_due_date is None and sub_due_time is not None:
                time_lower = sub_raw.lower()
                if ("de la ma\u00f1ana" in time_lower
                        or "de la manana" in time_lower):
                    sub_due_date = (now + timedelta(days=1)).date()
            
            if sub_due_date is not None and sub_due_date >= now.date():
                # Store shared date from first clause
                if i == 0:
                    shared_date = sub_due_date
                    shared_date_str = sub_due_date.strftime("%Y-%m-%d")
                
                sub_description = _planner_description(sub_raw)
                if not sub_description:
                    sub_description = _PLANNER_WORD[kind].capitalize()
                
                date_str = sub_due_date.strftime("%Y-%m-%d")
                now_real = datetime.now().astimezone()
                
                plan = {
                    "id": now_real.strftime(
                        "plan_%Y%m%d_%H%M%S_%f"
                    ),
                    "kind": kind,
                    "due_date": date_str,
                    "due_time": sub_due_time or None,
                    "description": sub_description,
                    "status": "pending",
                    "created_at": now_real.isoformat(
                        timespec="seconds"
                    ),
                }
                
                result = save_plan(plan)
                word = _PLANNER_WORD[kind]
                
                if result == "duplicate":
                    responses.append(
                        f"Ya tengo ese {word} registrado "
                        f"para {format_date_spanish(date_str)}."
                    )
                elif result == "error":
                    responses.append(
                        "No pude guardar el plan."
                    )
                else:
                    resp = (
                        "Perfecto. He registrado "
                        f"el {word} para "
                        f"{format_date_spanish(date_str)}"
                    )
                    if sub_due_time:
                        resp += f" a las {sub_due_time}"
                    resp += "."
                    responses.append(resp)
                
                final_desc = sub_description
                final_kind = kind
        
        if responses:
            return (" ".join(responses), final_desc, final_kind)
        # If no valid plans from coordination, fall through to single plan logic

    # --------------------------------------
    # FECHA / HORA
    # --------------------------------------

    due_date = _dp.plan_relative_datetime(
        normalized, now
    )

    due_time = parse_relative_time(raw)

    time_only = (
        due_date is None
        and _planner_time_only(normalized)
    )

    if (
        time_only
        and draft_kind is not None
        and draft_desc
        and draft_prev
    ):

        # Completar la hora de un plan pendiente
        # creado antes SIN hora: "a las 9"
        # actualiza due_time de ese plan.

        date = _dp.plan_relative_datetime(
            draft_prev, now
        )

        if date is not None:

            date_str = date.strftime("%Y-%m-%d")

            plan = _find_pending_null_time_plan(
                kind, date_str, draft_desc,
            )

            if plan:

                if update_plan_time(
                    plan["id"], due_time
                ):

                    word = _PLANNER_WORD[kind]

                    return (
                        "Perfecto. Actualicé "
                        f"la hora del {word} para "
                        f"{format_date_spanish(date_str)} "
                        f"a las {due_time}.",
                        draft_desc,
                        kind,
                    )

            due_date = date

    # --------------------------------------
    # HORA MAÑANA SIN FECHA EXPLÍCITA -> MAÑANA
    # Si hay hora con "de la mañana/manana" pero no hay
    # marcador de fecha, asumimos que es para mañana.
    # No aplicar para "tarde"/"noche" (podrían ser hoy).
    # --------------------------------------

    if due_date is None and due_time is not None:
        time_lower = raw.lower()
        if ("de la ma\u00f1ana" in time_lower
                or "de la manana" in time_lower):
            due_date = (now + timedelta(days=1)).date()

    if due_date is None:

        description = (
            _planner_description(raw)
            or draft_desc
        )

        return (
            "¿Para cuándo? Dime la fecha.",
            description,
            kind,
        )

    if due_date < now.date():

        return (
            "Esa fecha ya pasó. "
            "No puedo registrarla.",
            None,
            None,
        )

    # --------------------------------------
    # DESCRIPCIÓN
    # --------------------------------------

    description = (
        _planner_description(raw)
        or draft_desc
    )

    if not description:

        description = _PLANNER_WORD[kind].capitalize()

    date_str = due_date.strftime("%Y-%m-%d")

    now_real = datetime.now().astimezone()

    plan = {
        "id": now_real.strftime(
            "plan_%Y%m%d_%H%M%S_%f"
        ),
        "kind": kind,
        "due_date": date_str,
        "due_time": due_time or None,
        "description": description,
        "status": "pending",
        "created_at": now_real.isoformat(
            timespec="seconds"
        ),
    }

    result = save_plan(plan)

    word = _PLANNER_WORD[kind]

    if result == "duplicate":

        return (
            f"Ya tengo ese {word} registrado "
            f"para {format_date_spanish(date_str)}.",
            description,
            kind,
        )

    if result == "error":

        return (
            "No pude guardar el plan.",
            description,
            kind,
        )

    response = (
        "Perfecto. He registrado "
        f"el {word} para "
        f"{format_date_spanish(date_str)}"
    )

    if due_time:

        response += f" a las {due_time}"

    response += "."

    return (response, description, kind)


def planner_query(message):

    normalized = normalize_strict(message)

    now = _dp.datetime.now().astimezone()

    due_date = _dp.plan_relative_datetime(
        normalized, now
    )

    date_str = (
        due_date.strftime("%Y-%m-%d")
        if due_date
        else None
    )

    try:

        plans = query_plans(
            due_date=date_str, status="pending",
        )

    except Exception:

        plans = []

    if not plans:

        if date_str:

            return (
                "No tengo planes registrados "
                f"para "
                f"{format_date_spanish(date_str)}."
            )

        return "No tienes planes pendientes."

    lines = []

    for plan in plans:

        plan_date = plan["due_date"]

        plan_time = plan.get("due_time") or None

        plan_desc = plan["description"]

        if plan_time:

            lines.append(
                f"{format_date_spanish(plan_date)} "
                f"a las {plan_time} — "
                f"{plan_desc}"
            )

        else:

            lines.append(
                f"{format_date_spanish(plan_date)} "
                f"— {plan_desc}"
            )

    return "\n".join(lines)


def handle_learning_create(message, entities, context) -> str:
    """Handle LEARNING_CREATE intent.

    Creates a new learning entry from conversation input.
    Returns a confirmation message.

    Expected entities:
        lesson_text: The learned text/content
    """
    from services.plugins.learning import LearningPlugin

    plugin = LearningPlugin()

    lesson_text = entities.get("lesson_text", {}).get("lesson_text", "")
    if not lesson_text:
        return "No identifiqué una lección clara. ¿Podrías decirme qué aprendiste?"

    # Auto-capture as a learning entry
    decision_id = entities.get("decision_id", "") or ""
    prediction_id = entities.get("prediction_id", "") or ""

    if decision_id:
        trigger_type = "DECISION"
        trigger_id = decision_id
        expected = ""
        actual = lesson_text
    elif prediction_id:
        trigger_type = "PREDICTION"
        trigger_id = prediction_id
        expected = ""
        actual = lesson_text
    else:
        trigger_type = "DECISION"
        trigger_id = ""
        expected = ""
        actual = lesson_text

    # Capture the learning
    result = plugin.capture(
        trigger_id=trigger_id,
        trigger_type=trigger_type,
        expected=expected,
        actual=actual,
        confidence=0.8,
    )

    learning_id = result["id"]
    lesson = result["lesson"]
    confidence = result["confidence"]

    return (
        f"Lección aprendida registrada con ID {learning_id}. "
        f"Confianza: {confidence}. "
        f"Lección: {lesson}. "
        f"Puedo capturar más aprendizajes con 'aprendi que...'"
    )


# ==========================================
# IDENTITY PROPOSE / APPROVE FLOWS
# ==========================================


def handle_identity_propose(message, entities, context) -> str:
    """Handle IDENTITY_PROPOSE intent.

    Creates an identity change proposal from conversation input.
    Returns a confirmation message with the proposal ID.

    Expected entities:
        identity_changes: dict of changes to propose (e.g., new values, principles)
    """
    from brain.plugins.identity_propose import PLUGIN as PROPOSE_PLUGIN

    plugin = PROPOSE_PLUGIN

    # Handle both string and dict entity formats
    identity_changes = entities.get("identity_changes", "")
    if isinstance(identity_changes, dict):
        identity_changes = identity_changes.get("identity_changes", "")
    
    if not identity_changes:
        return (
            "No identifiqué cambios de identidad claros. "
            "¿Podrías decirme qué valores, principios o reglas deseas modificar?"
        )

    # Parse the identity changes string into a changes dict
    # Expected format: "valores honestidad transparencia" or "principios nuevo principio"
    changes = {}
    parts = identity_changes.split()
    if parts:
        key = parts[0]  # First word is the field (valores, principios, reglas, etc.)
        value = " ".join(parts[1:]) if len(parts) > 1 else ""
        if key in ("valores", "principios", "reglas"):
            changes[key] = [v.strip() for v in value.split(",")] if value else [value]
        else:
            changes[key] = value if value else key

    # Create the proposal via the plugin's internal mechanism
    # The IdentityCorePlugin will handle the actual proposal creation
    from app.services.plugins.identity_core import IdentityCorePlugin

    identity_core = IdentityCorePlugin(storage_path=context.get("storage_path") if context else None)

    proposal_result = identity_core.propose_change(changes=changes)

    proposal_id = proposal_result["proposal"]["proposal_id"]
    changes_parts = []
    for k, v in changes.items():
        if isinstance(v, list):
            changes_parts.append(f"{k}: {', '.join(v)}")
        else:
            changes_parts.append(f"{k}: {v}")
    changes_summary = ", ".join(changes_parts)

    return (
        f"Propuesta de cambio de identidad registrada con ID {proposal_id}. "
        f"Cambios propuestos: {changes_summary}. "
        f"Para aprobar usa 'aprobar identidad' o 'aceptar propuesta identidad'."
    )


def handle_identity_approve(message, entities, context) -> str:
    """Handle IDENTITY_APPROVE intent.

    Approves a proposed identity change. Requires explicit ceremony
    for hard limits (user confirmation via 'approved_by').

    Expected entities:
        proposal_id: The proposal ID to approve (may include approved_by suffix)
        approved_by: The user/actor performing the ceremony (optional)
    """
    from brain.plugins.identity_approve import PLUGIN as APPROVE_PLUGIN

    # First, check if this is a ceremony request
    # The proposal_id entity may contain both proposal_id and approved_by
    raw_proposal_id = entities.get("proposal_id", "")
    approved_by = entities.get("approved_by", "")

    # Parse raw_proposal_id to extract proposal_id and approved_by
    # Expected format: "prop_... confirmo" or "prop_... nombre_usuario"
    proposal_id = raw_proposal_id
    if raw_proposal_id and not approved_by:
        parts = raw_proposal_id.strip().split()
        if len(parts) >= 2:
            proposal_id = parts[0]
            approved_by = " ".join(parts[1:])

    if not proposal_id:
        return (
            "No identifiqué un ID de propuesta de identidad. "
            "¿De qué propuesta hablas? Usa 'aceptar propuesta identidad'."
        )

    if not approved_by:
        # No approved_by — require ceremony prompt
        return (
            "Para aprobar cambios de identidad se requiere una ceremonia "
            "de confirmación. Confirma con tu nombre o 'confirmo' para "
            "proceder con la aprobación."
        )

    from app.services.plugins.identity_core import IdentityCorePlugin

    identity_core = IdentityCorePlugin(storage_path=context.get("storage_path") if context else None)

    try:
        updated = identity_core.approve_change(
            proposal_id=proposal_id, approved_by=approved_by
        )
        new_version = updated.get("version", 1)
        return (
            f"Cambio de identidad aprobado. "
            f"Nueva versión: v{new_version}. "
            f"Registro agregado al audit log."
        )
    except ValueError as e:
        return f"No pude aprobar el cambio: {e}"


# ==========================================
# TEMPORAL QUERY HANDLER
# ==========================================


def handle_temporal_query(message, entities, context) -> str:
    """Handle TEMPORAL_QUERY intent.

    Queries memories, events, and other archive data across a time range.
    Returns a fused chronological result.

    Expected entities:
        time_range: Dict with start/end dates or year/month keywords
    """
    from app.services.plugins.search import SearchPlugin
    from app.services.archive import get_history

    plugin = SearchPlugin()

    # Extract time range from entities
    time_range = entities.get("time_range", "")
    if isinstance(time_range, dict):
        time_range = time_range.get("time_range", "")

    if not time_range:
        return "No identifiqué un rango temporal claro. ¿Podrías decirme qué período buscas?"

    # Parse time range - simple approach for year/month queries
    # For now, use the SearchPlugin query with date range filter
    # The entity might contain year/month keywords
    
    # Try to extract year from the query
    year_match = re.search(r"\b(20\d{2})\b", time_range)
    month_match = re.search(r"\b(enero|febrero|marzo|abril|mayo|junio|julio|agosto|septiembre|octubre|noviembre|diciembre)\b", time_range, re.IGNORECASE)
    
    start_date = None
    end_date = None
    
    if year_match:
        year = int(year_match.group(1))
        start_date = f"{year}-01-01"
        end_date = f"{year}-12-31"
    
    if month_match:
        month_name = month_match.group(1).lower()
        months = {
            "enero": 1, "febrero": 2, "marzo": 3, "abril": 4,
            "mayo": 5, "junio": 6, "julio": 7, "agosto": 8,
            "septiembre": 9, "octubre": 10, "noviembre": 11, "diciembre": 12
        }
        month = months.get(month_name)
        if month:
            if start_date:
                # Year already set, just narrow to month
                start_date = f"{year}-{month:02d}-01"
                if month == 12:
                    end_date = f"{year+1}-01-01"
                else:
                    end_date = f"{year}-{month+1:02d}-01"
            else:
                # Just month, assume current year
                from datetime import datetime
                year = datetime.now().year
                start_date = f"{year}-{month:02d}-01"
                if month == 12:
                    end_date = f"{year+1}-01-01"
                else:
                    end_date = f"{year}-{month+1:02d}-01"

    if start_date and end_date:
        # Search memories in date range
        result = plugin.query("", {"date_range": (start_date, end_date), "limit": 20})
        memories = result.get("results", [])
        
        # Also search history
        history = get_history()
        events = history.get("events", [])
        filtered_events = []
        for e in events:
            event_date = e.get("date", "")
            if start_date <= event_date <= end_date:
                filtered_events.append(e)
        
        # Fuse results chronologically
        fused = []
        for m in memories:
            fused.append({
                "date": m.get("date", ""),
                "type": "memory",
                "content": m.get("content", ""),
            })
        for e in filtered_events:
            fused.append({
                "date": e.get("date", ""),
                "type": "event",
                "content": f"{e.get('title', '')}: {e.get('description', '')}",
            })
        
        fused.sort(key=lambda x: x["date"])
        
        if not fused:
            return f"No hay memorias ni eventos registrados entre {start_date} y {end_date}."
        
        lines = [f"Resultados temporales ({start_date} a {end_date}):"]
        for item in fused[:20]:
            date_str = item.get("date", "")
            content = item.get("content", "")[:80]
            lines.append(f"  {date_str} [{item['type']}] {content}")
        
        return "\n".join(lines)
    
    return "No pude identificar un rango temporal válido. Especifica año o mes."


# ==========================================
# PATTERN SUGGEST HANDLER
# ==========================================


def handle_pattern_suggest(message, entities, context) -> str:
    """Handle PATTERN_SUGGEST intent.

    Returns detected patterns and suggested planner tasks.
    """
    from app.services.plugins.patterns import PatternsPlugin

    plugin = PatternsPlugin()

    # Extract domain filter if provided
    domains = None
    pattern_query = entities.get("pattern_query", "")
    if isinstance(pattern_query, dict):
        pattern_query = pattern_query.get("pattern_query", "")
    
    # Check for domain keywords in the query
    domain_keywords = {
        "memoria": "memory",
        "memorias": "memory",
        "decisión": "decision",
        "decisiones": "decision",
        "predicción": "prediction",
        "predicciones": "prediction",
        "aprendizaje": "learning",
        "aprendizajes": "learning",
        "reflexión": "reflection",
        "reflexiones": "reflection",
    }
    
    for kw, domain in domain_keywords.items():
        if kw in pattern_query.lower():
            domains = [domain]
            break

    # Detect patterns
    patterns = plugin.detect_recurring_patterns(domains=domains)

    if not patterns:
        return "No se detectaron patrones recurrentes en los datos actuales."

    # Format response
    lines = ["Patrones detectados:"]
    all_tasks = []
    
    for i, pattern in enumerate(patterns[:10], 1):
        theme = pattern.get("theme", "")
        occ = pattern.get("occurrences", 0)
        ptype = pattern.get("type", "")
        tasks = pattern.get("suggested_tasks", [])
        
        lines.append(f"  {i}. {theme} ({ptype}) — {occ} ocurrencias")
        
        for task in tasks:
            task_desc = task.get("title", "")
            freq = task.get("frequency", "")
            reason = task.get("reason", "")
            lines.append(f"     → Tarea sugerida: {task_desc} ({freq})")
            all_tasks.append({
                "title": task_desc,
                "frequency": freq,
                "reason": reason,
            })

    if all_tasks:
        lines.append(f"\nTotal tareas sugeridas: {len(all_tasks)}")
        lines.append("Usa 'recuerdame' para agendar alguna.")

    return "\n".join(lines)
