"""
PHASE 3.5E — Input Boundary Audit
Tests edge cases in user input handling.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "app"))

from brain.intent_layer import IntentLayer
from brain.intent_types import (
    GREETING, THANKS, EXIT, CALCULATE,
    DECIA_SELF, DECIA_CREATOR, ARCHIVE_DIRECT,
    MEMORY_CREATE, MEMORY_SEARCH, FREE_TALK,
    AMBIGUOUS_INPUT,
)
from brain.handlers import (
    quick_response,
    identity_response,
    calculate,
    ambiguous_input_response,
    memory_request,
    create_memory,
)
from brain.core import think

il = IntentLayer()


def analyze(text):
    return il.classify(text)


class TestEmptyInput:

    def test_empty_string(self):
        r = analyze("")
        assert r.intent in (AMBIGUOUS_INPUT, FREE_TALK)

    def test_empty_string_confidence(self):
        r = analyze("")
        assert r.confidence >= 0.50


class TestWhitespaceInput:

    def test_single_space(self):
        r = analyze(" ")
        assert r.intent in (AMBIGUOUS_INPUT, FREE_TALK)

    def test_multiple_spaces(self):
        r = analyze("     ")
        assert r.intent in (AMBIGUOUS_INPUT, FREE_TALK)

    def test_tabs(self):
        r = analyze("\t\t")
        assert r.intent in (AMBIGUOUS_INPUT, FREE_TALK)

    def test_newlines(self):
        r = analyze("\n\n\n")
        assert r.intent in (AMBIGUOUS_INPUT, FREE_TALK)

    def test_mixed_whitespace(self):
        r = analyze(" \t\n ")
        assert r.intent in (AMBIGUOUS_INPUT, FREE_TALK)


class TestPunctuationOnly:

    def test_question_marks(self):
        r = analyze("???")
        assert r.intent in (AMBIGUOUS_INPUT, FREE_TALK)

    def test_exclamation_marks(self):
        r = analyze("!!!")
        assert r.intent in (AMBIGUOUS_INPUT, FREE_TALK)

    def test_periods(self):
        r = analyze("...")
        assert r.intent in (AMBIGUOUS_INPUT, FREE_TALK)

    def test_commas(self):
        r = analyze(",,,")
        assert r.intent in (AMBIGUOUS_INPUT, FREE_TALK)

    def test_mixed_punctuation(self):
        r = analyze("?!.?,")
        assert r.intent in (AMBIGUOUS_INPUT, FREE_TALK)


class TestShortInput:

    def test_one_char_a(self):
        r = analyze("a")
        assert r.intent in (AMBIGUOUS_INPUT, FREE_TALK)

    def test_one_char_h(self):
        r = analyze("h")
        assert r.intent in (AMBIGUOUS_INPUT, FREE_TALK)

    def test_two_chars(self):
        r = analyze("no")
        assert r.intent in (AMBIGUOUS_INPUT, FREE_TALK)

    def test_single_number(self):
        r = analyze("5")
        assert r.intent in (CALCULATE, AMBIGUOUS_INPUT, FREE_TALK)


class TestLongInput:

    def test_1000_chars(self):
        long_text = "quiero saber " * 100
        r = analyze(long_text)
        assert r.intent is not None

    def test_5000_chars(self):
        long_text = "hablame de ciencia " * 500
        r = analyze(long_text)
        assert r.intent is not None

    def test_very_long_single_word(self):
        r = analyze("a" * 1000)
        assert r.intent is not None


class TestRepeatedWords:

    def test_hola_hola_hola(self):
        r = analyze("hola hola hola")
        assert r.intent == GREETING

    def test_gracias_gracias(self):
        r = analyze("gracias gracias gracias")
        assert r.intent == THANKS

    def test_salir_salir(self):
        r = analyze("salir salir salir")
        assert r.intent in (EXIT, FREE_TALK)

    def test_que_que_que(self):
        r = analyze("que que que")
        assert r.intent in (AMBIGUOUS_INPUT, FREE_TALK)


class TestAccents:

    def test_accented_hola(self):
        r = analyze("hola")
        assert r.intent == GREETING

    def test_accented_gracias(self):
        r = analyze("gracias")
        assert r.intent == THANKS

    def test_accented_calcular(self):
        r = analyze("5 por 4")
        assert r.intent == CALCULATE


class TestCaseVariations:

    def test_uppercase_hola(self):
        r = analyze("HOLA")
        assert r.intent == GREETING

    def test_mixed_case_hola(self):
        r = analyze("HoLa")
        assert r.intent == GREETING

    def test_uppercase_salir(self):
        r = analyze("SALIR")
        assert r.intent == EXIT

    def test_uppercase_gracias(self):
        r = analyze("GRACIAS")
        assert r.intent == THANKS

    def test_mixed_case_quien_eres(self):
        r = analyze("QuIeN eReS")
        assert r.intent == DECIA_SELF


class TestSpecialCharacters:

    def test_emojis(self):
        r = analyze("👋 hola")
        assert r.intent == GREETING

    def test_emojis_only(self):
        r = analyze("😀😀😀")
        assert r.intent in (AMBIGUOUS_INPUT, FREE_TALK)

    def test_unicode_symbols(self):
        r = analyze("★☆★ hola")
        assert r.intent == GREETING

    def test_numbers_and_text(self):
        r = analyze("hola 123 mundo")
        assert r.intent == GREETING


class TestMalformedWhisperLike:

    def test_garbled_text(self):
        r = analyze("xkzqwerty")
        assert r.intent in (AMBIGUOUS_INPUT, FREE_TALK)

    def test_partial_words(self):
        r = analyze("hol mund")
        assert r.intent in (GREETING, AMBIGUOUS_INPUT, FREE_TALK)

    def test_whitespace_between_letters(self):
        r = analyze("h o l a")
        assert r.intent in (GREETING, AMBIGUOUS_INPUT, FREE_TALK)

    def test_repeated_consonants(self):
        r = analyze("hooooolaaaa")
        assert r.intent in (GREETING, AMBIGUOUS_INPUT, FREE_TALK)


class TestNoCrashes:

    def test_think_empty(self):
        result = think("")
        assert isinstance(result, str)
        assert len(result) > 0

    def test_think_whitespace(self):
        result = think("   ")
        assert isinstance(result, str)
        assert len(result) > 0

    def test_think_special_chars(self):
        result = think("?!.?,")
        assert isinstance(result, str)
        assert len(result) > 0

    def test_think_very_long(self):
        result = think("a " * 500)
        assert isinstance(result, str)
        assert len(result) > 0

    def test_think_emojis(self):
        result = think("😀🎯🔥")
        assert isinstance(result, str)
        assert len(result) > 0

    def test_quick_response_empty(self):
        result = quick_response("")
        assert result is None or isinstance(result, str)

    def test_identity_response_empty(self):
        result = identity_response("")
        assert result is None or isinstance(result, str)

    def test_calculate_empty(self):
        result = calculate("")
        assert result is None

    def test_ambiguous_input_empty(self):
        result = ambiguous_input_response("")
        assert result is None or isinstance(result, str)

    def test_memory_request_empty(self):
        result = memory_request("")
        assert result is None
