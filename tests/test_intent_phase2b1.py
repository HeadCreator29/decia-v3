"""
DECIA v2 — Phase 2B.1: Fix Validation Tests
============================================

Objetivo: Validar los fixes de:
1. GREETING compuesto (word boundary)
2. DECIMAL en CALCULATE (entity extraction)

NO modifica ningún archivo de producción.
"""

import sys

from pathlib import Path

sys.path.insert(
    0,
    str(Path(__file__).resolve().parents[1] / "app"),
)

from brain.intent_layer import IntentLayer
from brain.intent_types import (
    GREETING,
    THANKS,
    CALCULATE,
    AMBIGUOUS_INPUT,
    FREE_TALK,
)

layer = IntentLayer()


def analyze(text):
    r = layer.classify(text)
    return {
        "intent": r.intent,
        "confidence": r.confidence,
        "entities": r.entities,
        "matched_pattern": r.matched_pattern,
        "candidates": [
            {"intent": c.intent, "score": c.score}
            for c in r.candidates
        ],
    }


# ==========================================
# 1. GREETING COMPUESTO
# ==========================================


class TestGreetingCompuesto:

    def test_hola_decia(self):
        """PASS: 'hola' con word_boundary matchea
        en 'hola decia'. GREETING con conf >= 0.90."""
        a = analyze("hola decia")
        assert a["intent"] == GREETING
        assert a["confidence"] >= 0.90

    def test_hola_que_tal(self):
        """PASS: 'hola' con word_boundary matchea
        en 'hola que tal'."""
        a = analyze("hola que tal")
        assert a["intent"] == GREETING
        assert a["confidence"] >= 0.90

    def test_oye_hola(self):
        """PASS: 'hola' con word_boundary matchea
        al final de 'oye hola'."""
        a = analyze("oye hola")
        assert a["intent"] == GREETING
        assert a["confidence"] >= 0.90

    def test_hola_hola(self):
        """PASS: 'hola' con word_boundary matchea
        en 'hola hola'."""
        a = analyze("hola hola")
        assert a["intent"] == GREETING
        assert a["confidence"] >= 0.90

    def test_buenas_decia(self):
        """PASS: 'buenas' PHRASE matchea
        en 'buenas decia'."""
        a = analyze("buenas decia")
        assert a["intent"] == GREETING
        assert a["confidence"] >= 0.90

    def test_buenos_dias_decia(self):
        """PASS: 'buenos dias' PHRASE matchea
        en 'buenos dias decia'."""
        a = analyze("buenos dias decia")
        assert a["intent"] == GREETING
        assert a["confidence"] >= 0.90

    def test_buenas_tardes(self):
        """PASS: 'buenas tardes' PHRASE matchea
        en 'buenas tardes'."""
        a = analyze("buenas tardes")
        assert a["intent"] == GREETING
        assert a["confidence"] >= 0.90

    def test_buenas_noches(self):
        """PASS: 'buenas noches' PHRASE matchea
        en 'buenas noches'."""
        a = analyze("buenas noches")
        assert a["intent"] == GREETING
        assert a["confidence"] >= 0.90

    def test_hola_como_estas(self):
        """PASS: 'hola' con word_boundary matchea
        en 'hola, como estas'."""
        a = analyze("hola, como estas")
        assert a["intent"] == GREETING
        assert a["confidence"] >= 0.90


class TestGreetingCompuestoNoFalsePositives:

    def test_hola_es_un_buen_dia(self):
        """PASS: 'hola' con word_boundary no
        convierte frase larga en GREETING."""
        a = analyze("hola es un buen dia")
        assert a["intent"] == GREETING

    def test_hoy_hola_mundo(self):
        """PASS: 'hola' al medio de frase."""
        a = analyze("hoy hola mundo")
        assert a["intent"] == GREETING


# ==========================================
# 2. DECIMAL EN CALCULATE
# ==========================================


class TestDecimalCalculate:

    def test_decimal_multiply(self):
        """PASS: '2.5 * 4' preserva punto
        decimal en entity math."""
        a = analyze("2.5 * 4")
        assert a["intent"] == CALCULATE
        assert a["confidence"] >= 0.90
        assert a["entities"]["math"] == "2.5 * 4"

    def test_decimal_add(self):
        """PASS: '10.5 + 2' preserva decimal."""
        a = analyze("10.5 + 2")
        assert a["intent"] == CALCULATE
        assert a["confidence"] >= 0.90
        assert a["entities"]["math"] == "10.5 + 2"

    def test_decimal_complex(self):
        """PASS: '(2.5 * 4) / 2' preserva
        decimales."""
        a = analyze("(2.5 * 4) / 2")
        assert a["intent"] == CALCULATE
        assert a["confidence"] >= 0.90
        assert a["entities"]["math"] == \
            "(2.5 * 4) / 2"

    def test_decimal_small(self):
        """PASS: '0.5 + 0.25' preserva
        decimales."""
        a = analyze("0.5 + 0.25")
        assert a["intent"] == CALCULATE
        assert a["confidence"] >= 0.90
        assert a["entities"]["math"] == "0.5 + 0.25"

    def test_integer_still_works(self):
        """PASS: '2+2' sin decimal sigue
        funcionando."""
        a = analyze("2+2")
        assert a["intent"] == CALCULATE
        assert a["confidence"] >= 0.90
        assert a["entities"]["math"] == "2+2"

    def test_complex_integer(self):
        """PASS: '3*4+1' sin decimal sigue
        funcionando."""
        a = analyze("3*4+1")
        assert a["intent"] == CALCULATE
        assert a["confidence"] >= 0.90
        assert a["entities"]["math"] == "3*4+1"

    def test_division_with_spaces(self):
        """PASS: '10 / 2' con espacios sigue
        funcionando."""
        a = analyze("10 / 2")
        assert a["intent"] == CALCULATE
        assert a["confidence"] >= 0.90
        assert a["entities"]["math"] == "10 / 2"
