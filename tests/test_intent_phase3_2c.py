import sys, os
import pytest

sys.path.insert(0, r"C:\Users\idelv\Desktop\DECIA_v2\app")
os.chdir(r"C:\Users\idelv\Desktop\DECIA_v2\app")

from brain.intent_layer import IntentLayer
from brain.handlers import ambiguous_input_response
from brain.intent_types import (
    AMBIGUOUS_INPUT, FREE_TALK,
)

il = IntentLayer()


class TestConversationalSocial:
    """Social conversation should reach Ollama,
    not return '¿Sí? ¿Qué necesitas?'."""

    def test_como_estas_classify(self):
        r = il.classify("como estas")
        assert r.intent == AMBIGUOUS_INPUT

    def test_como_estas_ambiguous_response(self):
        r = ambiguous_input_response("como estas")
        assert r is None

    def test_que_tal_classify(self):
        r = il.classify("que tal")
        assert r.intent == AMBIGUOUS_INPUT

    def test_que_tal_ambiguous_response(self):
        r = ambiguous_input_response("que tal")
        assert r is None


class TestOpenRequests:
    """Open-ended requests should reach Ollama."""

    def test_cuentame_algo_classify(self):
        r = il.classify("cuentame algo")
        assert r.intent == AMBIGUOUS_INPUT

    def test_cuentame_algo_ambiguous_response(self):
        r = ambiguous_input_response("cuentame algo")
        assert r is None


class TestUserState:
    """User emotional/physical state should reach
    Ollama."""

    def test_estoy_aburrido_classify(self):
        r = il.classify("estoy aburrido")
        assert r.intent == AMBIGUOUS_INPUT

    def test_estoy_aburrido_ambiguous_response(self):
        r = ambiguous_input_response("estoy aburrido")
        assert r is None

    def test_estoy_cansado_classify(self):
        r = il.classify("estoy cansado")
        assert r.intent == AMBIGUOUS_INPUT

    def test_estoy_cansado_ambiguous_response(self):
        r = ambiguous_input_response("estoy cansado")
        assert r is None


class TestStillAmbiguous:
    """Truly ambiguous inputs should still return
    the clarification response."""

    def test_algo_still_ambiguous(self):
        r = ambiguous_input_response("algo")
        assert r == "¿Sí? ¿Qué necesitas?"

    def test_algo_classify(self):
        r = il.classify("algo")
        assert r.intent == AMBIGUOUS_INPUT

    def test_bueno_still_ambiguous(self):
        r = ambiguous_input_response("bueno")
        assert r == "¿Sí? ¿Qué necesitas?"

    def test_pues_still_ambiguous(self):
        r = ambiguous_input_response("pues")
        assert r == "¿Sí? ¿Qué necesitas?"


class TestQuestionsStillPass:
    """Questions with '?' already pass to Ollama."""

    def test_como_estas_with_question_mark(self):
        r = ambiguous_input_response("¿cómo estás?")
        assert r is None

    def test_que_tal_with_question_mark(self):
        r = ambiguous_input_response("¿qué tal?")
        assert r is None


class TestRegressionProtection:
    """Verify existing handlers are unaffected."""

    def test_hola_still_greeting(self):
        r = il.classify("hola")
        assert r.intent == "GREETING"

    def test_gracias_still_thanks(self):
        r = il.classify("gracias")
        assert r.intent == "THANKS"

    def test_salir_still_exit(self):
        r = il.classify("salir")
        assert r.intent == "EXIT"

    def test_calculate_still_works(self):
        r = il.classify("2 + 2")
        assert r.intent == "CALCULATE"

    def test_guarda_que_still_memory(self):
        r = il.classify("guarda que tengo clase")
        assert r.intent == "MEMORY_CREATE"

    def test_deca_identity_still_works(self):
        r = il.classify("quien eres")
        assert r.intent == "DECIA_SELF"
