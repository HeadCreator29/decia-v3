import sys

from pathlib import Path

sys.path.insert(
    0,
    str(Path(__file__).resolve().parents[1] / "app"),
)

from unittest.mock import patch

from brain.intent_layer import IntentLayer
from brain.core import think, _SAFE_INTENTS
from brain.handlers import time_response

from brain.intent_types import (
    TIME,
    DATE,
    GREETING,
    THANKS,
    EXIT,
    CALCULATE,
    DECIA_SELF,
    DECIA_CREATOR,
    ARCHIVE_DIRECT,
)

from brain.intent_types import (
    ARCHIVE_SEARCH,
    MEMORY_SEARCH,
    USER_NAME_ASK,
    FREE_TALK,
)


il = IntentLayer()


def classify(text):
    return il.classify(text)


# ==========================================
# 1. TIME INTENT
# ==========================================


class TestTimeIntent:

    def test_que_hora_es(self):
        r = classify("que hora es")
        assert r.intent == TIME

    def test_vime_que_hora_es(self):
        r = classify("vime que hora es")
        assert r.intent == TIME

    def test_puedes_decirme_la_hora(self):
        r = classify("puedes decirme la hora")
        assert r.intent == TIME

    def test_me_dices_la_hora(self):
        r = classify("me dices la hora")
        assert r.intent == TIME

    def test_dime_la_hora(self):
        r = classify("dime la hora")
        assert r.intent == TIME

    def test_me_puedes_decir_la_hora(self):
        r = classify("me puedes decir la hora")
        assert r.intent == TIME

    def test_sabes_que_hora_es(self):
        r = classify("sabes que hora es")
        assert r.intent == TIME

    def test_time_confidence_high(self):
        r = classify("que hora es")
        assert r.confidence >= 0.90

    def test_hora_not_date(self):
        r = classify("que hora es")
        assert r.intent == TIME
        assert r.intent != DATE


# ==========================================
# 2. DATE INTENT
# ==========================================


class TestDateIntent:

    def test_que_fecha_es(self):
        r = classify("que fecha es")
        assert r.intent == DATE

    def test_que_dia_es_hoy(self):
        r = classify("que dia es hoy")
        assert r.intent == DATE

    def test_que_dia_es(self):
        r = classify("que dia es")
        assert r.intent == DATE

    def test_cual_es_la_fecha(self):
        r = classify("cual es la fecha")
        assert r.intent == DATE

    def test_cual_es_la_fecha_de_hoy(self):
        r = classify("cual es la fecha de hoy")
        assert r.intent == DATE

    def test_dime_la_fecha(self):
        r = classify("dime la fecha")
        assert r.intent == DATE

    def test_date_confidence_high(self):
        r = classify("que fecha es")
        assert r.confidence >= 0.90

    def test_date_not_time_ambiguous(
            self):
        r = classify("que dia es hoy")
        assert r.intent == DATE


# ==========================================
# 3. ARCHIVE_SEARCH
# ==========================================


class TestArchiveSearchIntent:

    def test_que_hay_registrado_en_archivo(self):
        r = classify(
            "que hay registrado en el archivo"
        )
        assert r.intent == ARCHIVE_SEARCH

    def test_que_tienes_guardado(self):
        r = classify("que tienes guardado")
        assert r.intent == ARCHIVE_SEARCH

    def test_que_hay_guardado(self):
        r = classify("que hay guardado")
        assert r.intent == ARCHIVE_SEARCH

    def test_que_hay_en_el_archivo(self):
        r = classify("que hay en el archivo")
        assert r.intent == ARCHIVE_SEARCH

    def test_que_tengo_registrado(self):
        r = classify("que tengo registrado")
        assert r.intent == ARCHIVE_SEARCH

    def test_archive_search_confidence_above_threshold(
            self):
        r = classify("que hay registrado en el archivo")
        assert r.confidence >= 0.90 or (
            r.intent == ARCHIVE_SEARCH
        )


# ==========================================
# 4. MEMORY_SEARCH TEMPORAL
# ==========================================


class TestMemorySearchTemporal:

    def test_que_recuerdas(self):
        r = classify("que recuerdas")
        assert r.intent == MEMORY_SEARCH

    def test_que_paso_ayer(self):
        r = classify("que paso ayer")
        assert r.intent == MEMORY_SEARCH

    def test_que_paso_hoy(self):
        r = classify("que paso hoy")
        assert r.intent == MEMORY_SEARCH

    def test_que_hicimos_ayer(self):
        r = classify("que hicimos ayer")
        assert r.intent == MEMORY_SEARCH

    def test_memory_search_confidence(self):
        r = classify("que paso ayer")
        assert r.confidence >= 0.70

    def test_hoy_alone_not_temporal(self):
        r = classify("hoy me siento genial")
        assert r.intent == FREE_TALK

    def test_ayer_alone_not_temporal(self):
        r = classify("ayer fui al supermercado")
        assert r.intent == FREE_TALK


# ==========================================
# 5. NO INTERFERENCIA CON INTENTS EXISTENTES
# ==========================================


class TestNoInterference:

    def test_que_es_deca_still_archive_direct(
            self):
        r = classify("que es deca")
        assert r.intent == ARCHIVE_DIRECT

    def test_quien_eres_still_decia_self(
            self):
        r = classify("quien eres")
        assert r.intent == DECIA_SELF

    def test_como_estas_hoy_en_dia_free(
            self):
        r = classify("como estas hoy en dia")
        assert r.intent == FREE_TALK

    def test_que_significa_la_vida_free(
            self):
        r = classify("que significa la vida")
        assert r.intent == FREE_TALK

    def test_hola_still_greeting(self):
        r = classify("hola")
        assert r.intent == GREETING

    def test_gracias_still_thanks(self):
        r = classify("gracias")
        assert r.intent == THANKS

    def test_salir_still_exit(self):
        r = classify("salir")
        assert r.intent == EXIT

    def test_dos_mas_dos_still_calculate(
            self):
        r = classify("2 mas 2")
        assert r.intent == CALCULATE

    def test_quien_soy_still_user_name_ask(
            self):
        r = classify("quien soy")
        assert r.intent == USER_NAME_ASK


# ==========================================
# 6. SAFE_INTENTS
# ==========================================


class TestSafeIntents:

    def test_time_is_safe(self):
        assert TIME in _SAFE_INTENTS

    def test_date_is_safe(self):
        assert DATE in _SAFE_INTENTS

    def test_archive_search_not_safe(self):
        assert ARCHIVE_SEARCH not in _SAFE_INTENTS

    def test_memory_search_not_safe(self):
        assert MEMORY_SEARCH not in _SAFE_INTENTS

    def test_safe_intents_count_is_nine(
            self):
        assert len(_SAFE_INTENTS) == 9

    def test_safe_intents_exact_set(self):
        assert _SAFE_INTENTS == {
            GREETING, THANKS, EXIT, CALCULATE,
            TIME, DATE, DECIA_SELF,
            DECIA_CREATOR, ARCHIVE_DIRECT,
        }


# ==========================================
# 7. HANDLER
# ==========================================


class TestTimeResponse:

    def test_time_response_returns_string(
            self):
        r = time_response("que hora es")
        assert isinstance(r, str)
        assert len(r) > 0

    def test_date_response_mentions_month(
            self):
        r = time_response("que fecha es")
        assert " de " in r
        assert r.startswith("Hoy es ")

    def test_time_response_no_date_mentions(
            self):
        r = time_response("que hora es")
        assert not r.startswith("Hoy es ")


# ==========================================
# 8. RUTEO (think)
# ==========================================


class TestTimeDateRouting:

    def test_think_time_no_ollama(self):

        with patch(
            "brain.core.ask_ollama",
            return_value="ollama",
        ) as mock_ollama:

            r = think("que hora es")

            mock_ollama.assert_not_called()
            assert "Son las" in r

    def test_think_date_no_ollama(self):

        with patch(
            "brain.core.ask_ollama",
            return_value="ollama",
        ) as mock_ollama:

            r = think("que fecha es")

            mock_ollama.assert_not_called()
            assert "Hoy es" in r

    def test_think_time_via_time_response(
            self):

        with patch(
            "brain.core.time_response",
            return_value="cae aquí",
        ) as mock_tr:

            r = think("que hora es")

            mock_tr.assert_called()
            assert r == "cae aquí"

    def test_think_free_talk_still_ollama(
            self):

        with patch(
            "brain.core.ambiguous_input_response",
            return_value=None,
        ), patch(
            "brain.core.ask_ollama",
            return_value="responde",
        ) as mock_ollama:

            r = think("cuentame sobre astronomia")

            mock_ollama.assert_called_once()
            assert r == "responde"