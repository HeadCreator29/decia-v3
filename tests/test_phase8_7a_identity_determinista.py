"""
PHASE 8.7A — IDENTITY DETERMINISTA (F2)

Amplia la respuesta determinista de DECIA_SELF para las
variantes que ya clasificaban como DECIA_SELF pero caian
a OLLAMA: para que sirves / de donde vienes /
para que estas creada / cuales son tus funciones.

Determinista: 0 llamadas a OLLAMA en los casos corregidos.
No toca thresholds, TIL, OLLAMA, modelo, memories.json,
search_archive ni search_deca_memory.
"""
import sys

from pathlib import Path

sys.path.insert(
    0,
    str(Path(__file__).resolve().parents[1] / "app"),
)

from unittest.mock import patch

import pytest

from brain.core import think
from brain.context import ConversationContext
from brain.intent_layer import IntentLayer
from brain.intent_types import (
    DECIA_SELF,
    DECIA_CREATOR,
    GREETING,
    EXIT,
    AMBIGUOUS_INPUT,
    FREE_TALK,
    TIME,
    CALCULATE,
    MEMORY_SEARCH,
)

IL = IntentLayer()


def _classify(message):
    return IL.classify(message)


def _think(message, context=None):
    with patch(
        "brain.core.ask_ollama",
    ) as mock_ollama:
        response = think(message, context=context)
        return response, mock_ollama.call_count


# ==========================================
# A. FRASES OBJETIVO + VARIANTES
# ==========================================


@pytest.mark.parametrize(
    "query",
    [
        "para que sirves",
        "¿Para qué sirves?",
        "para qué sirves",
        "PARA QUE SIRVES",
        "para que sirves.",
        "de donde vienes",
        "De dónde vienes?",
        "¿DE DONDE VIENES?",
        "de donde vienes.",
        "para que estas creada",
        "¿Para qué estás creada?",
        "PARA QUE ESTAS CREADA",
        "cuales son tus funciones",
        "¿Cuáles son tus funciones?",
        "CUALES SON TUS FUNCIONES",
    ],
)
def test_8_7a_variantes_deterministas(query):
    result = _classify(query)
    assert result.intent == DECIA_SELF

    response, calls = _think(query)

    assert calls == 0
    assert response.startswith("Soy DECIA,")
    assert "DECIA" in response


def test_8_7a_frases_objetivo_intent():
    for query in (
        "para que sirves",
        "de donde vienes",
        "para que estas creada",
        "cuales son tus funciones",
    ):
        assert _classify(query).intent == DECIA_SELF


# ==========================================
# B. REGRESIÓN: IDENTIDAD EXISTENTE
# ==========================================


@pytest.mark.parametrize(
    "query",
    [
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
    ],
)
def test_8_7b_identidad_no_regresion(query):
    assert _classify(query).intent == DECIA_SELF

    response, calls = _think(query)

    assert calls == 0
    assert response.startswith("Soy DECIA,")


# ==========================================
# C. DECIA_CREATOR INTACTO
# ==========================================


@pytest.mark.parametrize(
    "query",
    [
        "quien te creo",
        "quien es tu creador",
        "quien es tu creadora",
        "como naciste",
        "quien te hizo",
        "como te crearon",
    ],
)
def test_8_7c_creator_intacto(query):
    assert _classify(query).intent == DECIA_CREATOR

    response, calls = _think(query)

    assert calls == 0
    assert response.startswith("Fui creada por")


def test_8_7c_no_cruza_con_decia_self():
    assert _classify("quien te creo").intent in (
        DECIA_CREATOR, DECIA_SELF,
    )
    assert (
        _classify("quien te creo").intent
        != DECIA_SELF
    )


# ==========================================
# D. FALSOS POSITIVOS
# ==========================================


@pytest.mark.parametrize(
    "query",
    [
        "para que sirve deca",
        "para que es esto",
        "para que sirve esto",
        "de donde sale esta idea",
        "de donde viene el nombre",
    ],
)
def test_8_7d_no_falsos_positivos(query):
    result = _classify(query)

    assert result.intent != DECIA_SELF
    assert result.intent != DECIA_CREATOR


def test_8_7d_de_donde_viene_deca():
    result = _classify("de donde viene deca")
    assert result.intent != DECIA_SELF
    assert result.intent != DECIA_CREATOR

    response, calls = _think("de donde viene deca")
    assert calls == 0
    assert response != "OLLAMA"
    assert response is not None
    assert not response.startswith("Soy DECIA,")
    assert response.startswith(
        "Inicio del proyecto"
    )


# ==========================================
# E. INTENTS CERCANOS SIN CAMBIOS
# ==========================================


def test_8_7e_hora_sin_cambios():
    assert _classify("que hora es").intent == TIME
    response, calls = _think("que hora es")
    assert calls == 0
    assert response.startswith("Son las")


def test_8_7e_calculo_sin_cambios():
    assert _classify("cuanto es 15 por 3").intent \
        == CALCULATE
    response, calls = _think("cuanto es 15 por 3")
    assert calls == 0
    assert response == "45"


def test_8_7e_greeting_sin_cambios():
    assert _classify("hola").intent == GREETING
    response, calls = _think("hola")
    assert calls == 0
    assert "Hola" in response


# ==========================================
# F. INVARIANTE DE CONTEXTO (invalidate)
# ==========================================


def test_8_7f_identidad_invalida_contexto():
    ctx = ConversationContext(max_turns=10)
    ctx.set_context(
        intent=MEMORY_SEARCH,
        mode="memory",
        entity="kanye",
        source_message="que recuerdas sobre kanye",
    )

    response, calls = _think(
        "para que sirves", context=ctx,
    )

    assert calls == 0
    assert response.startswith("Soy DECIA,")

    response2, calls2 = _think(
        "y ayer", context=ctx,
    )

    assert calls2 == 0
    assert "¿" in response2
    assert ctx.last_intent is None