"""
PHASE 6.3 — TIME RESILIENCE / KEYWORD AUDIT
TIME must represent exclusively the request for the
CURRENT time. Bare or contextual mentions of "hora"
(future events, schedule talk) must NOT become TIME.
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
TIME = "TIME"
DATE = "DATE"


def _classify(message):
    return INTENT_LAYER.classify(message)


# ==========================================
# A. TIME POSITIVOS
# ==========================================


class TestTimePositives:

    @pytest.mark.parametrize("ask", [
        "qu\u00e9 hora es",
        "que hora es",
        "\u00bfqu\u00e9 hora tenemos?",
        "qu\u00e9 hora tenemos",
        "dime la hora",
        "me puedes decir la hora",
        "sabes la hora",
        "cu\u00e1l es la hora",
        "qu\u00e9 hora es ahora",
        "qu\u00e9 hora tenemos hoy",
        "dime qu\u00e9 hora es",
        "a qu\u00e9 hora estamos",
    ])
    def test_es_time(self, ask):
        result = _classify(ask)
        assert result.intent == TIME, ask

    def test_que_hora_tenemos_confianza_alta(
        self,
    ):
        assert (
            _classify("qu\u00e9 hora tenemos")
            .confidence >= 0.90
        )

    def test_cual_es_la_hora(self):
        assert (
            _classify("cu\u00e1l es la hora")
            .intent == TIME
        )


# ==========================================
# B. NO-TIME
# ==========================================


class TestNoTime:

    @pytest.mark.parametrize("phrase", [
        "tengo una hora",
        "tengo una hora de salida",
        "hora de salida",
        "hora de compromiso",
        "la hora de la reuni\u00f3n",
        "una hora cualquiera",
        "esa hora",
        "cambi\u00e9 la hora",
        "necesito saber la hora de salida",
        "\u00bfa qu\u00e9 hora salimos?",
    ])
    def test_no_es_time(self, phrase):
        result = _classify(phrase)
        assert result.intent != TIME, phrase

    @pytest.mark.parametrize("phrase", [
        "tengo una hora",
        "hora de salida",
        "la hora de la reuni\u00f3n",
    ])
    def test_ya_no_responde_la_hora(self, phrase):
        with patch(
            "brain.core.ask_ollama",
            return_value="OLLAMA",
        ) as mock_ollama:
            response = think(
                phrase, context=ConversationContext()
            )
        assert "Son las" not in response
        assert (
            mock_ollama.called is True
        ), "debe caer a fallback, no a hora actual"

    def test_esa_hora_pide_clarificacion(self):
        with patch(
            "brain.core.ask_ollama",
            return_value="OLLAMA",
        ) as mock_ollama:
            response = think(
                "esa hora",
                context=ConversationContext(),
            )
        assert mock_ollama.called is False
        assert "Son las" not in response


# ==========================================
# C. INTERACCIÓN TIME / DATE
# ==========================================


class TestTimeDateInteraction:

    def test_date_intacto(self):
        for ask in [
            "que dia es",
            "qu\u00e9 d\u00eda es",
            "dime la fecha",
            "cual es el dia",
            "hoy que dia es",
            "que fecha tenemos",
        ]:
            assert _classify(ask).intent == DATE, ask

    def test_fecha_no_date_sigue_fuera(self):
        for phrase in [
            "fecha de nacimiento",
            "tengo una fecha",
        ]:
            assert (
                _classify(phrase).intent != DATE
            ), phrase

    def test_no_se_pisan(self):
        assert _classify("que hora es").intent == TIME
        assert _classify("que dia es").intent == DATE


# ==========================================
# D. ASSISTED ROUTING
# ==========================================


class TestAssistedRouting:

    def test_que_hora_es_sin_ollama(self):
        with patch(
            "brain.core.ask_ollama",
            return_value="OLLAMA",
        ) as mock_ollama:
            response = think(
                "que hora es",
                context=ConversationContext(),
            )
        assert mock_ollama.called is False
        assert "Son las" in response

    def test_sabes_la_hora_sin_ollama(self):
        with patch(
            "brain.core.ask_ollama",
            return_value="OLLAMA",
        ) as mock_ollama:
            response = think(
                "sabes la hora",
                context=ConversationContext(),
            )
        assert mock_ollama.called is False
        assert "Son las" in response


# ==========================================
# E. ACENTOS
# ==========================================


class TestAccents:

    def test_hora_con_acento(self):
        assert (
            _classify("qu\u00e9 hora es").intent
            == TIME
        )

    def test_hora_sin_acento(self):
        assert _classify("que hora es").intent == TIME

    def test_dia_sigue_date(self):
        assert _classify("qu\u00e9 d\u00eda es").intent == DATE

    def test_cual_con_acento(self):
        assert (
            _classify("cu\u00e1l es la hora").intent
            == TIME
        )


# ==========================================
# F. INTEGRACIÓN TIL 6.1
# ==========================================


class TestTilIntegration:

    def test_que_hora_es_es(self):
        corrected = correct_transcription(
            "que hora es es"
        )
        assert corrected == "que hora es"
        assert (
            _classify(corrected).intent == TIME
        )

    def test_que_hora_es_es_sin_ollama(self):
        corrected = correct_transcription(
            "que hora es es"
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
        assert "Son las" in response

    def test_stutter_fecha_sigue_funcionando(
        self,
    ):
        assert (
            correct_transcription("que dia dia es")
            == "que dia es"
        )


# ==========================================
# G. REGRESIÓN PATRONES TIME EXISTENTES
# ==========================================


class TestExistingTimePatterns:

    @pytest.mark.parametrize("ask", [
        "cuanto es la hora",
        "me dices la hora",
        "puedes decirme la hora",
        "sabes que hora es",
        "hora actual",
        "la hora actual",
        "que hora tienes",
        "que hora tiene",
    ])
    def test_patron_previa_sigue(self, ask):
        assert _classify(ask).intent == TIME, ask

    def test_dime_la_hora_confianza(self):
        result = _classify("dime la hora")
        assert result.intent == TIME
        assert result.confidence >= 0.90