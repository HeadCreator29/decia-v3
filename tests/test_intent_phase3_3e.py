import sys, os
sys.path.insert(0, r"C:\Users\idelv\Desktop\DECIA_v2\app")
os.chdir(r"C:\Users\idelv\Desktop\DECIA_v2\app")

import pytest
from brain.handlers import calculate
from brain.intent_layer import IntentLayer

il = IntentLayer()


# =========================================================
# A) Natural language "cuanto es"
# =========================================================

class TestCuantoEs:
    """'cuanto es X op Y' must calculate deterministically."""

    def test_cuanto_es_25_mas_17(self):
        assert calculate("cuanto es 25 mas 17") == "42"

    def test_cuanto_es_100_menos_35(self):
        assert calculate("cuanto es 100 menos 35") == "65"

    def test_cuanto_es_5_por_6(self):
        assert calculate("cuanto es 5 por 6") == "30"

    def test_cuanto_es_20_entre_4(self):
        assert calculate("cuanto es 20 entre 4") == "5"

    def test_cuanto_es_intent(self):
        r = il.classify("cuanto es 25 mas 17")
        assert r.intent == "CALCULATE"


# =========================================================
# B) Parentheses
# =========================================================

class TestParentheses:
    """Parentheses with Spanish operators."""

    def test_10mas5_por_2(self):
        assert calculate("(10 mas 5) por 2") == "30"

    def test_10menos4_por_3(self):
        assert calculate("(10 menos 4) por 3") == "18"

    def test_2mas3_por_4mas1(self):
        assert calculate("(2 mas 3) por (4 mas 1)") == "25"

    def test_pure_math_parens(self):
        assert calculate("(10+5)*2") == "30"


# =========================================================
# C) Existing cases - regression protection
# =========================================================

class TestExistingCases:
    """Verify existing CALCULATE cases still work."""

    def test_2mas2(self):
        assert calculate("2 mas 2") == "4"

    def test_10menos3(self):
        assert calculate("10 menos 3") == "7"

    def test_5por4(self):
        assert calculate("5 por 4") == "20"

    def test_20entre5(self):
        assert calculate("20 entre 5") == "4"

    def test_2point5por4(self):
        assert calculate("2.5 por 4") == "10"

    def test_10point5mas2point5(self):
        assert calculate("10.5 mas 2.5") == "13"

    def test_pure_2plus2(self):
        assert calculate("2+2") == "4"

    def test_pure_100div4(self):
        assert calculate("100/4") == "25"


# =========================================================
# D) Boundary / no false positives
# =========================================================

class TestNoFalsePositives:
    """Phrases with numbers that are NOT calculations."""

    def test_tengo_25_perros(self):
        assert calculate("tengo 25 perros") is None

    def test_tengo_2_cosas(self):
        assert calculate("tengo 2 cosas") is None

    def test_compre_5_cosas(self):
        assert calculate("compre 5 cosas por 4 dias") is None
