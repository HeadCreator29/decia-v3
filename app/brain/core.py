import re

from services.ollama_service import ask_ollama

from brain.intent_layer import IntentLayer

from brain.intent_types import (
    GREETING,
    THANKS,
    EXIT,
    CALCULATE,
    TIME,
    DATE,
    DECIA_SELF,
    DECIA_CREATOR,
    ARCHIVE_DIRECT,
    ARCHIVE_SEARCH,
    MEMORY_SEARCH,
    MEMORY_CREATE,
    AMBIGUOUS_INPUT,
    FREE_TALK,
    PLANNER_CREATE,
    PLANNER_QUERY,
    DECISION_CREATE,
    DECISION_CONFIRM,
    PREDICTION_CREATE,
    PREDICTION_REVIEW,
    LEARNING_CREATE,
    REFLECTION_CREATE,
    REFLECTION_APPROVE,
    IDENTITY_PROPOSE,
    IDENTITY_APPROVE,
    TEMPORAL_QUERY,
    PATTERN_SUGGEST,
)

from brain.followup import (
    resolve_follow_up,
    CONTEXT_CLARIFY,
)

from brain.handlers import (
    quick_response,
    identity_response,
    personal_identity_handler,
    calculate,
    time_response,
    memory_request,
    create_memory,
    archive_response,
    history_response,
    search_deca_memory,
    format_archive_response,
    extract_search_entity,
    filter_memories_by_entity,
    is_deictic_entity,
    ambiguous_input_response,
    planner_create,
    planner_query,
    handle_reflection_create,
    handle_reflection_approve,
    handle_identity_propose,
    handle_identity_approve,
    handle_temporal_query,
    handle_pattern_suggest,
)


_intent_layer = IntentLayer()

_SOBRE_TAIL_RE = re.compile(
    r"\bsobre\s+[^.,;:!?]+$"
)

_SAFE_INTENTS = {
    GREETING,
    THANKS,
    EXIT,
    CALCULATE,
    TIME,
    DATE,
    DECIA_SELF,
    DECIA_CREATOR,
    ARCHIVE_DIRECT,
    LEARNING_CREATE,
}


def think(message, context=None):

    print(
        f"[DECIA BRAIN] "
        f"Procesando: {message}"
    )

    intent_result = _intent_layer.classify(
        message
    )

    # ======================================
    # RESOLUCIÓN DE SEGUIMIENTO
    # (solo si la intención primaria no
    #  clasificó claramente y existe
    #  contexto relevante)
    # ======================================

    if (
        context is not None
        and intent_result.intent in (
            FREE_TALK, AMBIGUOUS_INPUT,
        )
    ):

        resolved = resolve_follow_up(
            message, context
        )

        if resolved:

            follow_intent, follow_message = (
                resolved
            )

            if follow_intent == CONTEXT_CLARIFY:

                return "¿Sobre qué?"

            print(
                "[DECIA BRAIN] "
                f"Seguimiento -> "
                f"{follow_intent} | "
                f"{follow_message}"
            )

            message = follow_message

            intent_result.intent = (
                follow_intent
            )

    # ======================================
    # ASSISTED ROUTING (OBSERVATION → DECISION)
    # ======================================

    is_safe = intent_result.intent in _SAFE_INTENTS
    has_confidence = (
        intent_result.confidence >= 0.90
    )

    def _finish(
        response, mode=None, entity=None,
        invalidate=False, intent=None,
        topic=None,
    ):

        if context is not None:

            if invalidate:

                context.invalidate()

            elif mode is not None:

                context.set_context(
                    intent=(
                        intent
                        if intent is not None
                        else intent_result.intent
                    ),
                    mode=mode,
                    topic=topic,
                    entity=entity,
                    source_message=message,
                )

        return response

    if intent_result.intent == REFLECTION_CREATE:
        response = handle_reflection_create(
            message, intent_result.entities, context
        )
        if response:
            return _finish(
                response, invalidate=True,
            )

    if intent_result.intent == REFLECTION_APPROVE:
        response = handle_reflection_approve(
            message, intent_result.entities, context
        )
        if response:
            return _finish(
                response, invalidate=True,
            )

    if intent_result.intent == IDENTITY_PROPOSE:
        response = handle_identity_propose(
            message, intent_result.entities, context
        )
        if response:
            return _finish(
                response, invalidate=True,
            )

    if intent_result.intent == IDENTITY_APPROVE:
        response = handle_identity_approve(
            message, intent_result.entities, context
        )
        if response:
            return _finish(
                response, invalidate=True,
            )

    if intent_result.intent == TEMPORAL_QUERY:
        response = handle_temporal_query(
            message, intent_result.entities, context
        )
        if response:
            return _finish(
                response, invalidate=True,
            )

    if intent_result.intent == PATTERN_SUGGEST:
        response = handle_pattern_suggest(
            message, intent_result.entities, context
        )
        if response:
            return _finish(
                response, invalidate=True,
            )

    if is_safe and has_confidence:

        IntentLayer.log_result(
            intent_result,
            used=True,
            reason="high_confidence_safe_intent",
        )

        if intent_result.intent == GREETING:
            return _finish(
                quick_response(message),
                invalidate=True,
            )

        if intent_result.intent == THANKS:
            return _finish(
                quick_response(message),
                invalidate=True,
            )

        if intent_result.intent == EXIT:
            return _finish(
                "Hasta luego.",
                invalidate=True,
            )

        if intent_result.intent == CALCULATE:
            response = calculate(message)
            if response is not None:
                return _finish(
                    response, invalidate=True,
                )

        if intent_result.intent in (TIME, DATE):
            response = time_response(message)
            if response:
                return _finish(
                    response, mode="time",
                )

        if intent_result.intent in (
            DECIA_SELF, DECIA_CREATOR,
        ):
            response = identity_response(
                message
            )
            if response:
                return _finish(
                    response, invalidate=True,
                )

        if intent_result.intent == ARCHIVE_DIRECT:
            response = archive_response(
                message
            )
            if response:
                return _finish(
                    response, mode="archive",
                )

        if intent_result.intent == DECISION_CREATE:
            response = handle_decision_create(
                message, intent_result.entities, context
            )
            if response:
                return _finish(
                    response, invalidate=True,
                )

        if intent_result.intent == DECISION_CONFIRM:
            response = handle_decision_confirm(
                message, intent_result.entities, context
            )
            if response:
                return _finish(
                    response, invalidate=True,
                )

        if intent_result.intent == PREDICTION_CREATE:
            response = handle_prediction_create(
                message, intent_result.entities, context
            )
            if response:
                return _finish(
                    response, invalidate=True,
                )

        if intent_result.intent == PREDICTION_REVIEW:
            response = handle_prediction_review(
                message, intent_result.entities, context
            )
            if response:
                return _finish(
                    response, invalidate=True,
                )

        if intent_result.intent == LEARNING_CREATE:
            from brain.handlers import handle_learning_create
            response = handle_learning_create(
                message, intent_result.entities, context
            )
            if response:
                return _finish(
                    response, invalidate=True,
                )

    else:

        IntentLayer.log_result(
            intent_result,
            used=False,
            reason="below_threshold",
        )

    # ======================================
    # PLANNER (9.6) — EVENTOS / RECORDATORIOS
    # Determinista: NUNCA OLLAMA y NUNCA toca
    # memories.json. Los intents PLANNER no son
    # safe-intents: caen aquí por routing
    # secuencial tras el bloque assisted-routing.
    # ======================================

    if intent_result.intent in (
        PLANNER_CREATE, PLANNER_QUERY,
    ):

        print(
            "[DECIA BRAIN] "
            "INTENT ACCEPTED -> "
            f"{intent_result.intent}"
        )

        print(
            "[DECIA BRAIN] "
            "EXECUTOR USED | "
            "Ruta: PLANNER"
        )

        if intent_result.intent == PLANNER_CREATE:

            response, plan_desc, plan_kind = (
                planner_create(message, context)
            )

            return _finish(
                response,
                mode="planner",
                topic=plan_kind,
                entity=plan_desc,
                intent=PLANNER_CREATE,
            )

        response = planner_query(message)

        return _finish(
            response,
            mode="planner",
            intent=PLANNER_QUERY,
        )

    # ======================================
    # RESPUESTA RÁPIDA
    # ======================================

    response = quick_response(message)

    if response:

        print(
            "[DECIA BRAIN] "
            "Ruta: RESPUESTA RÁPIDA"
        )

        return _finish(
            response, invalidate=True,
        )

    # ======================================
    # IDENTIDAD
    # ======================================

    response = identity_response(message)

    if response:

        print(
            "[DECIA BRAIN] "
            "Ruta: IDENTIDAD"
        )

        return _finish(
            response, invalidate=True,
        )

    # ======================================
    # IDENTIDAD PERSONAL
    # ======================================

    response = personal_identity_handler(
        message
    )

    if response:

        print(
            "[DECIA BRAIN] "
            "Ruta: IDENTIDAD PERSONAL"
        )

        return _finish(
            response, invalidate=True,
        )

    # ======================================
    # CÁLCULO
    # ======================================

    response = calculate(message)

    if response is not None:

        print(
            "[DECIA BRAIN] "
            "Ruta: CÁLCULO"
        )

        return _finish(
            response, invalidate=True,
        )

    # ======================================
    # HORA / FECHA
    # ======================================

    if intent_result.intent in (TIME, DATE):

        response = time_response(message)

        if response:

            print(
                "[DECIA BRAIN] "
                "Ruta: HORA/FECHA"
            )

            return _finish(
                response, mode="time",
            )

    # ======================================
    # NUEVA MEMORIA
    # (MEMORY_CREATE ya detectado por el
    #  Intent Layer → la entidad es el
    #  fallback para transcripciones que
    #  anteponen el nombre, p.ej.
    #  "Desee, recuerda que ...")
    # ======================================

    memory_content = memory_request(message)

    if (
        not memory_content
        and intent_result.intent == MEMORY_CREATE
    ):

        memory_content = (
            intent_result.entities.get("memory")
        )

    if memory_content:

        print(
            "[DECIA BRAIN] "
            "INTENT ACCEPTED -> "
            f"{intent_result.intent}"
        )

        print(
            "[DECIA BRAIN] "
            "EXECUTOR USED | "
            "Ruta: NUEVA MEMORIA"
        )

        memory = create_memory(
            memory_content
        )

        print(
            "[DECIA BRAIN] "
            "Ruta: NUEVA MEMORIA"
        )

        if memory["time"]:

            if memory.get("duplicate"):

                return _finish(
                    f"Ya tengo esa memoria "
                    f"registrada para "
                    f"{memory['date']} "
                    f"a las {memory['time']}.",
                    invalidate=True,
                )

            return _finish(
                f"Lo recordaré. "
                f"Quedó registrada para "
                f"{memory['date']} "
                f"a las {memory['time']}.",
                invalidate=True,
            )

        if memory.get("duplicate"):

            return _finish(
                "Ya tengo esa memoria "
                f"registrada para "
                f"{memory['date']}.",
                invalidate=True,
            )

        return _finish(
            "Lo recordaré. "
            f"Quedó registrada para "
            f"{memory['date']}.",
            invalidate=True,
        )

    # ======================================
    # HISTORIA GENERAL (G6)
    # Consultas históricas desnudas
    # ("que paso", "qué sucedió", "que hubo")
    # sin entidad ni temporal: deterministas,
    # sin consultar memorias ni OLLAMA.
    # ======================================

    response = history_response(message)

    if response:

        print(
            "[DECIA BRAIN] "
            "Ruta: HISTORIA"
        )

        return _finish(
            response, mode="archive",
            intent=ARCHIVE_SEARCH,
        )

    # ======================================
    # ARCHIVO DIRECTO
    # ======================================

    response = archive_response(message)

    if response:

        print(
            "[DECIA BRAIN] "
            "Ruta: ARCHIVO DIRECTO"
        )

        return _finish(
            response, mode="archive",
        )

    # ======================================
    # BÚSQUEDA DE ARCHIVO / MEMORIA
    # (intención clara → ejecutar su ruta;
    #  sin resultados → respuesta
    #  determinista, NUNCA OLLAMA)
    # ======================================

    if intent_result.intent in (
        ARCHIVE_SEARCH, MEMORY_SEARCH,
    ):

        print(
            "[DECIA BRAIN] "
            "INTENT ACCEPTED -> "
            f"{intent_result.intent}"
        )

        print(
            "[DECIA BRAIN] "
            "EXECUTOR USED | "
            "Ruta: BÚSQUEDA ARCHIVO/MEMORIA"
        )

        search_entity = (
            extract_search_entity(message)
        )

        if (
            search_entity
            and is_deictic_entity(
                search_entity
            )
        ):

            antecedent = None

            if context is not None:

                antecedent = (
                    context.last_entity
                )

            if (
                antecedent
                and not is_deictic_entity(
                    antecedent
                )
            ):

                search_entity = str(
                    antecedent
                )

                message = re.sub(
                    _SOBRE_TAIL_RE,
                    f"sobre {search_entity}",
                    message,
                    count=1,
                )

            else:

                return "¿Sobre qué?"

        prefer_field = (
            "memories"
            if intent_result.intent
            == MEMORY_SEARCH
            else None
        )

        memory = search_deca_memory(
            message,
            prefer_field=prefer_field,
        )

        if (
            memory
            and intent_result.intent
            == MEMORY_SEARCH
            and memory.get("field")
            != "memories"
        ):

            memory = None

        if memory and search_entity:

            memory = filter_memories_by_entity(
                memory, search_entity,
            )

        if memory:

            response = format_archive_response(
                memory
            )

            if response:

                return _finish(
                    response,
                    mode=(
                        "archive"
                        if intent_result.intent
                        == ARCHIVE_SEARCH
                        else "memory"
                    ),
                    entity=search_entity,
                )

        if intent_result.intent == MEMORY_SEARCH:

            if search_entity:

                return _finish(
                    "No recuerdo nada "
                    f"sobre {search_entity}.",
                    mode="memory",
                    entity=search_entity,
                )

            return _finish(
                "No tengo memorias "
                "registradas.",
                mode="memory",
            )

        if search_entity:

            return _finish(
                "No encontré información "
                f"registrada sobre "
                f"{search_entity}.",
                mode="archive",
                entity=search_entity,
            )

        return _finish(
            "No encontré información "
            "registrada en el archivo.",
            mode="archive",
        )

    # ======================================
    # ENTRADAS AMBIGUAS
    # ======================================

    response = ambiguous_input_response(
        message
    )

    if response:

        print(
            "[DECIA BRAIN] "
            "Ruta: ENTRADA AMBIGUA"
        )

        if context is not None and (
            context.conversation_mode
            in ("archive", "memory", "planner")
            or context.last_intent in (
                ARCHIVE_SEARCH,
                MEMORY_SEARCH,
                PLANNER_CREATE,
                PLANNER_QUERY,
            )
        ):
            # B1: la clarificación determinista no
            # debe borrar un tema HISTORY/MEMORY/
            # ARCHIVE en curso. Tras "¿Sí? ¿Qué
            # necesitas?" el usuario continúa con
            # follow-ups ("y el lunes", "y que
            # mas") que deben resolver sobre el
            # mismo dominio. F8 (9.7.3): la
            # continuidad PLANNER (borrador en
            # dos pasos / consulta en curso)
            # también se conserva: "no se" entre
            # dos pasos no debe tumbar "y manana"
            # ni desviar la siguiente frase a
            # MEMORY_SEARCH u OLLAMA. En
            # contextos que no son búsqueda
            # (TIME, DATE, frío) se mantiene la
            # invalidación.
            return _finish(response)

        return _finish(
            response, invalidate=True,
        )

    # ======================================
    # OLLAMA
    # ======================================

    print(
        "[DECIA BRAIN] "
        "Ruta: OLLAMA"
    )

    conversation_context = None

    if context is not None:

        context.invalidate()

        conversation_context = (
            context.get_messages()
        )

    return ask_ollama(
        message, context=conversation_context
    )
