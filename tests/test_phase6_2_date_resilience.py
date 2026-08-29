"""
PHASE 6.2 — DATE RESILIENCE / KEYWORD AUDIT
DATE detection must accept natural variants and ASR
equivalents WITHOUT turning bare mentions of "día" or
"fecha" into DATE, and without breaking TIME.
"""
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

sys.path.insert(
    0,
    str(Path(__file__).resolve().parents[1] / "app"),
)

from brain.intent_layer import IntentLayer
from brain.core import think
from brain.context import ConversationContext

from utils.speech_corrections import (
    correct_transcription,
)

INTENT_LAYER = IntentLayer()
DATE = "DATE"
TIME = "TIME"


def _classify(message):
    return INTENT_LAYER.classify(message)


# ==========================================
# A. DATE POSITIVOS
# ==========================================


class TestDatePositives:

    @pytest.mark.parametrize("ask", [
        "que dia es",
        "qu\u00e9 d\u00eda es",
        "que fecha es",
        "qu\u00e9 fecha es",
        "cu\u00e1l es la fecha",
        "cual es el dia",
        "cual es el dia de hoy",
        "dime que dia es",
        "dime la fecha",
        "hoy que dia es",
        "que dia tenemos",
        "que fecha tenemos",
        "en que fecha estamos",
        "que dia estamos",
        "a que dia estamos",
    ])
    def test_es_date(self, ask):
        result = _classify(ask)
        assert result.intent == DATE, ask

    @pytest.mark.parametrize("ask", [
        "cual es el dia",
        "que dia tenemos",
        "que fecha tenemos",
    ])
    def test_responde_fecha_sin_ollama(self, ask):
        with patch(
            "brain.core.ask_ollama",
            return_value="OLLAMA",
        ) as mock_ollama:
            response = think(
                ask, context=ConversationContext()
            )
        assert mock_ollama.called is False
        assert "Hoy es" in response


# ==========================================
# B. TIME POSITIVOS
# ==========================================


class TestTimePositives:

    @pytest.mark.parametrize("ask", [
        "que hora es",
        "qu\u00e9 hora es",
        "dime la hora",
        "qu\u00e9 hora tenemos",
        "a qu\u00e9 hora estamos",
    ])
    def test_es_time(self, ask):
        result = _classify(ask)
        assert result.intent == TIME, ask

    def test_dime_la_hora_responde_hora(self):
        result = _classify("dime la hora")
        assert result.intent == TIME
        assert result.confidence >= 0.90


# ==========================================
# C. FRASES NORMALES CON "día" (NO DATE)
# ==========================================


class TestDiaNoDate:

    @pytest.mark.parametrize("phrase", [
        "qu\u00e9 d\u00eda voy a ir",
        "qu\u00e9 d\u00eda hacemos eso",
        "el d\u00eda est\u00e1 bonito",
    ])
    def test_no_es_date(self, phrase):
        result = _classify(phrase)
        assert result.intent != DATE, phrase


# ==========================================
# D. FRASES NORMALES CON "fecha" (NO DATE)
# ==========================================


class TestFechaNoDate:

    @pytest.mark.parametrize("phrase", [
        "tengo una fecha",
        "fecha de nacimiento",
        "fecha de lanzamiento",
    ])
    def test_no_es_date(self, phrase):
        result = _classify(phrase)
        assert result.intent != DATE, phrase

    @pytest.mark.parametrize("phrase", [
        "tengo una fecha",
        "fecha de nacimiento",
        "fecha de lanzamiento",
    ])
    def test_ya_no_responde_la_fecha(self, phrase):
        with patch(
            "brain.core.ask_ollama",
            return_value="OLLAMA",
        ) as mock_ollama:
            response = think(
                phrase, context=ConversationContext()
            )
        assert "Hoy es" not in response
        assert "Son las" not in response
        assert (
            mock_ollama.called is True
        ), "debe caer a fallback, no a fecha"


# ==========================================
# E. INTERACCIÓN DATE / TIME
# ==========================================


class TestDateTimeInteraction:

    def test_no_se_pisan(self):
        date_result = _classify("que dia es")
        time_result = _classify("que hora es")
        assert date_result.intent == DATE
        assert time_result.intent == TIME
        assert (
            date_result.confidence
            == time_result.confidence
            == 1.0
        )

    def test_sin_candidatos_no_es_date(self):
        assert (
            _classify("es tarde").intent
            != DATE
        )
        assert (
            _classify("es tarde").intent
            != TIME
        )


# ==========================================
# F. TIL 6.1 → DATE
# ==========================================


class TestTilIntegration:

    def test_que_dia_dia_es_llega_a_date(self):
        corrected = correct_transcription(
            "que dia dia es"
        )
        assert corrected == "que dia es"
        result = _classify(corrected)
        assert result.intent == DATE
        assert result.confidence >= 0.90

    def test_que_dia_dia_es_sin_ollama(self):
        corrected = correct_transcription(
            "que dia dia es"
        )
        with patch(
            "brain.core.ask_ollama",
            return_value="OLLAMA",
        ) as mock_ollama:
            response = think(
                corrected,
                context=ConversationContext(),
            )
        assert mock_ollama.called is False
        assert "Hoy es" in response


# ==========================================
# G. ACENTOS / SIN ACENTOS
# ==========================================


class TestAccents:

    @pytest.mark.parametrize("ask", [
        "qu\u00e9 d\u00eda es",
        "qu\u00e9 fecha es",
        "cu\u00e1l es la fecha",
    ])
    def test_date_con_acentos(self, ask):
        assert _classify(ask).intent == DATE

    @pytest.mark.parametrize("ask", [
        "que dia es",
        "que fecha es",
        "cual es la fecha",
    ])
    def test_date_sin_acentos(self, ask):
        assert _classify(ask).intent == DATE

    def test_hora_con_acento(self):
        assert (
            _classify("qu\u00e9 hora es").intent
            == TIME
        )