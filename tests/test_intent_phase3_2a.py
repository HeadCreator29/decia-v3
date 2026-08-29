"""
DECIA v2 — Phase 3.2A: DECA Identity Boundary
==============================================

Objetivo: Mejorar el reconocimiento de consultas
naturales sobre DECA sin crear falsos positivos.

Nuevos patrones:
- "qué es deca" → ARCHIVE_DIRECT
- "cuéntame sobre deca" → ARCHIVE_DIRECT
- "háblame sobre deca" → ARCHIVE_DIRECT

DECA debe estar explícitamente presente para
activar ARCHIVE_DIRECT en estas nuevas construcciones.
"""

import sys

from pathlib import Path

sys.path.insert(
    0,
    str(Path(__file__).resolve().parents[1] / "app"),
)

from brain.intent_layer import IntentLayer
from brain.intent_types import (
    ARCHIVE_DIRECT,
    ARCHIVE_SEARCH,
    DECIA_CREATOR,
    DECIA_SELF,
    AMBIGUOUS_INPUT,
    FREE_TALK,
)

il = IntentLayer()

_SAFE_INTENTS = {
    "GREETING", "THANKS", "EXIT", "CALCULATE",
    "DECIA_SELF", "DECIA_CREATOR", "ARCHIVE_DIRECT",
}


def analyze(text):
    r = il.classify(text)
    return {
        "intent": r.intent,
        "score": r.candidates[0].score
        if r.candidates else 0,
        "confidence": r.confidence,
        "would_auto_route": (
            r.confidence >= 0.90
            and r.intent in _SAFE_INTENTS
        ),
        "matched_pattern": (
            r.candidates[0].matched_pattern
            if r.candidates else None
        ),
    }


# ==========================================
# POSITIVE CASES — NEW PATTERNS
# ==========================================


class TestQueEsDeca:

    def test_que_es_deca(self):
        """'qué es deca' → ARCHIVE_DIRECT."""
        r = il.classify("qué es deca")
        assert r.intent == ARCHIVE_DIRECT

    def test_que_es_deca_confidence(self):
        r = il.classify("qué es deca")
        assert r.confidence >= 0.90

    def test_que_es_deca_auto_route(self):
        a = analyze("qué es deca")
        assert a["would_auto_route"]

    def test_que_es_deca_sin_acento(self):
        """'que es deca' → ARCHIVE_DIRECT."""
        r = il.classify("que es deca")
        assert r.intent == ARCHIVE_DIRECT

    def test_que_es_deca_con_signos(self):
        """'¿Qué es DECA?' → ARCHIVE_DIRECT."""
        r = il.classify("¿Qué es DECA?")
        assert r.intent == ARCHIVE_DIRECT


class TestCuentameSobreDeca:

    def test_cuentame_sobre_deca(self):
        """'cuéntame sobre deca' → ARCHIVE_DIRECT."""
        r = il.classify("cuéntame sobre deca")
        assert r.intent == ARCHIVE_DIRECT

    def test_cuentame_sobre_deca_confidence(self):
        r = il.classify("cuéntame sobre deca")
        assert r.confidence >= 0.90

    def test_cuentame_sobre_deca_auto_route(self):
        a = analyze("cuéntame sobre deca")
        assert a["would_auto_route"]

    def test_cuentame_sobre_deca_sin_acento(self):
        """'cuentame sobre deca' → ARCHIVE_DIRECT."""
        r = il.classify("cuentame sobre deca")
        assert r.intent == ARCHIVE_DIRECT

    def test_cuentame_sobre_deca_con_signos(self):
        """'¿Cuéntame sobre DECA?' → ARCHIVE_DIRECT."""
        r = il.classify("¿Cuéntame sobre DECA?")
        assert r.intent == ARCHIVE_DIRECT


class TestHablameSobreDeca:

    def test_hablame_sobre_deca(self):
        """'háblame sobre deca' → ARCHIVE_DIRECT."""
        r = il.classify("háblame sobre deca")
        assert r.intent == ARCHIVE_DIRECT

    def test_hablame_sobre_deca_confidence(self):
        r = il.classify("háblame sobre deca")
        assert r.confidence >= 0.90

    def test_hablame_sobre_deca_auto_route(self):
        a = analyze("háblame sobre deca")
        assert a["would_auto_route"]

    def test_hablame_sobre_deca_sin_acento(self):
        """'hablame sobre deca' → ARCHIVE_DIRECT."""
        r = il.classify("hablame sobre deca")
        assert r.intent == ARCHIVE_DIRECT

    def test_hablame_sobre_deca_con_signos(self):
        """'¿Háblame sobre DECA?' → ARCHIVE_DIRECT."""
        r = il.classify("¿Háblame sobre DECA?")
        assert r.intent == ARCHIVE_DIRECT


# ==========================================
# EXISTING PATTERNS STILL WORK
# ==========================================


class TestExistingPatternsStillWork:

    def test_que_significa_deca(self):
        r = il.classify("qué significa deca")
        assert r.intent == ARCHIVE_DIRECT
        assert r.confidence >= 0.90

    def test_hablame_de_deca(self):
        r = il.classify("háblame de deca")
        assert r.intent == ARCHIVE_DIRECT
        assert r.confidence >= 0.90

    def test_cuentame_de_deca(self):
        r = il.classify("cuéntame de deca")
        assert r.intent == ARCHIVE_DIRECT
        assert r.confidence >= 0.90

    def test_cuentame_un_poco_sobre_deca(self):
        r = il.classify("cuéntame un poco sobre deca")
        assert r.intent == ARCHIVE_DIRECT
        assert r.confidence >= 0.90


# ==========================================
# NEGATIVE CASES — NO FALSE POSITIVES
# ==========================================


class TestNegativeCases:

    def test_que_es_esto(self):
        """'qué es esto' → NOT ARCHIVE_DIRECT
        (no DECA keyword)."""
        r = il.classify("qué es esto")
        assert r.intent != ARCHIVE_DIRECT

    def test_que_significa_esto(self):
        """'qué significa esto' → NOT ARCHIVE_DIRECT."""
        r = il.classify("qué significa esto")
        assert r.intent != ARCHIVE_DIRECT

    def test_cuentame_sobre_esto(self):
        """'cuéntame sobre esto' → NOT ARCHIVE_DIRECT."""
        r = il.classify("cuéntame sobre esto")
        assert r.intent != ARCHIVE_DIRECT

    def test_hablame_sobre_mi(self):
        """'háblame sobre mí' → NOT ARCHIVE_DIRECT."""
        r = il.classify("háblame sobre mí")
        assert r.intent != ARCHIVE_DIRECT

    def test_que_es_decia(self):
        """'qué es decia' → NOT ARCHIVE_DIRECT
        (DECIA, not DECA)."""
        r = il.classify("qué es decia")
        assert r.intent != ARCHIVE_DIRECT

    def test_quien_eres(self):
        """'quién eres' → NOT ARCHIVE_DIRECT."""
        r = il.classify("quién eres")
        assert r.intent != ARCHIVE_DIRECT

    def test_cuentame_algo(self):
        """'cuéntame algo' → NOT ARCHIVE_DIRECT."""
        r = il.classify("cuéntame algo")
        assert r.intent != ARCHIVE_DIRECT

    def test_hablame_algo(self):
        """'háblame algo' → NOT ARCHIVE_DIRECT."""
        r = il.classify("háblame algo")
        assert r.intent != ARCHIVE_DIRECT

    def test_que_es_la_vida(self):
        """'qué es la vida' → NOT ARCHIVE_DIRECT."""
        r = il.classify("qué es la vida")
        assert r.intent != ARCHIVE_DIRECT

    def test_cuentame_sobre_ciencia(self):
        """'cuéntame sobre ciencia' → NOT ARCHIVE_DIRECT."""
        r = il.classify("cuéntame sobre ciencia")
        assert r.intent != ARCHIVE_DIRECT
