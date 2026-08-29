"""
PHASE 8.6 — FIXES DETERMINISTAS DE LENGUAJE

F1: fechas relativas (ayer/anteayer/manana) en DATE
F4: DECIA_SELF "cual es tu proposito" (patron mojibake)
F3: EXIT determinista para "me voy" / "ya me voy"

Determinista: ninguno de los casos corregidos llama a OLLAMA.
No altera MEMORY/ARCHIVE ni los invariantes de contexto.
"""
import sys

from pathlib import Path

sys.path.insert(
    0,
    str(Path(__file__).resolve().parents[1] / "app"),
)

from unittest.mock import patch

from datetime import datetime, timedelta

import pytest

from brain.core import think
from brain.intent_layer import IntentLayer
from brain.handlers import (
    DIAS_SEMANA,
    get_month_name,
)
from brain.intent_types import (
    DATE,
    TIME,
    EXIT,
    FREE_TALK,
    AMBIGUOUS_INPUT,
    GREETING,
    DECIA_SELF,
)

IL = IntentLayer()


def _classify(message):
    return IL.classify(message)


def _think(message):
    with patch(
        "brain.core.ask_ollama",
    ) as mock_ollama:
        response = think(message)
        return response, mock_ollama.call_count


def _expected_date(delta_days):
    d = datetime.now() + timedelta(
        days=delta_days
    )
    weekday = DIAS_SEMANA[d.weekday()]
    month = get_month_name(f"{d.month:02d}")
    return (
        f"{weekday} {d.day} de {month} "
        f"de {d.year}"
    )


# ==========================================
# F1 — FECHAS RELATIVAS (DATE)
# ==========================================


@pytest.mark.parametrize(
    "query,prefix,delta",
    [
        ("que fecha fue ayer", "Ayer fue", -1),
        ("que dia fue ayer", "Ayer fue", -1),
        ("que fecha era ayer", "Ayer fue", -1),
        ("que fecha fue anteayer",
         "Anteayer fue", -2),
        ("que dia sera manana",
         "Mañana será", 1),
        ("que fecha sera manana",
         "Mañana será", 1),
        ("que fecha es hoy", "Hoy es", 0),
        ("que dia es hoy", "Hoy es", 0),
    ],
)
def test_f1_fecha_relativa(
    query, prefix, delta,
):
    assert _classify(query).intent == DATE

    response, calls = _think(query)

    assert calls == 0
    assert response == (
        f"{prefix} {_expected_date(delta)}."
    )


def test_f1_fecha_estandar_sigue_today():
    for query in (
        "que dia es",
        "cual es la fecha",
        "dime la fecha",
    ):
        result = _classify(query)
        assert result.intent == DATE

        response, calls = _think(query)

        assert calls == 0
        assert response == (
            f"Hoy es {_expected_date(0)}."
        )


def test_f1_manana_con_que_dia_es():
    assert (
        _classify("que dia es manana").intent
        == DATE
    )

    response, calls = _think("que dia es manana")

    assert calls == 0
    assert response == (
        f"Mañana será {_expected_date(1)}."
    )


def test_f1_hora_sin_cambios():
    assert _classify("que hora es").intent == TIME

    response, calls = _think("que hora es")

    assert calls == 0
    assert response.startswith("Son las")


def test_f1_no_matchea_fecha_incidental():
    result = _classify("que dia sera el partido")
    assert result.intent not in (DATE, EXIT)
    assert result.intent != DECIA_SELF


# ==========================================
# F4 — DECIA_SELF / PROPÓSITO
# ==========================================


@pytest.mark.parametrize(
    "query",
    [
        "cual es tu proposito",
        "cuál es tu propósito",
    ],
)
def test_f4_proposito(query):
    assert _classify(query).intent == DECIA_SELF

    response, calls = _think(query)

    assert calls == 0
    assert response.startswith("Soy DECIA,")
    assert "DECIA" in response


def test_f4_identidad_no_regresion():
    for query in (
        "quien eres",
        "que es decia",
        "hablame de decia",
        "quien es decia",
        "como te llamas",
    ):
        assert _classify(query).intent == DECIA_SELF

        response, calls = _think(query)

        assert calls == 0
        assert response.startswith("Soy DECIA,")


# ==========================================
# F3 — EXIT DETERMINISTA
# ==========================================


@pytest.mark.parametrize(
    "query",
    [
        "me voy",
        "ya me voy",
        "me voy.",
        "salir",
        "salir por favor",
        "adios",
        "nos vemos",
        "hasta luego",
    ],
)
def test_f3_exit(query):
    result = _classify(query)
    assert result.intent == EXIT
    assert (
        result.intent
        not in (
            GREETING,
            AMBIGUOUS_INPUT,
            FREE_TALK,
        )
    )

    response, calls = _think(query)

    assert calls == 0
    assert response == "Hasta luego."


def test_f3_me_voy_no_es_otro_intento():
    result = _classify("me voy")
    assert result.intent == EXIT
    assert result.confidence >= 0.90
    assert (
        result.intent
        not in (GREETING, AMBIGUOUS_INPUT)
    )


@pytest.mark.parametrize(
    "query",
    [
        "me voy a dormir",
        "ya me voy a dormir",
    ],
)
def test_f3_no_falso_exit_dormir(query):
    assert _classify(query).confidence < 0.90

    response, calls = _think(query)

    assert response != "Hasta luego."


@pytest.mark.parametrize(
    "query",
    [
        "me voy al gimnasio",
        "voy a salir a correr",
        "voy a casa",
    ],
)
def test_f3_frase_con_voy_no_despedida(query):
    result = _classify(query)

    assert (
        result.intent
        not in (EXIT, GREETING, AMBIGUOUS_INPUT)
    )

    response, calls = _think(query)

    assert response != "Hasta luego."


def test_f3_no_salir_con_negacion():
    result = _classify("no quiero salir")

    assert (
        result.intent
        not in (EXIT, GREETING, AMBIGUOUS_INPUT)
    )

    response, calls = _think("no quiero salir")

    assert response != "Hasta luego."