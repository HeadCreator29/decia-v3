"""
DECIA v2 — Phase 3.2B: Natural Exit Boundary
=============================================

Objetivo: Mejorar despedidas y solicitudes naturales
de salida SIN introducir falsos positivos.

EXIT = intención de TERMINAR LA CONVERSACIÓN,
no simplemente el verbo "salir".
"""

import sys

from pathlib import Path

sys.path.insert(
    0,
    str(Path(__file__).resolve().parents[1] / "app"),
)

from brain.intent_layer import IntentLayer
from brain.intent_types import (
    EXIT,
    THANKS,
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
# POSITIVE CASES — SHOULD BE EXIT
# ==========================================


class TestExitPositive:

    def test_salir(self):
        """'salir' → EXIT. Existing pattern."""
        r = il.classify("salir")
        assert r.intent == EXIT

    def test_salir_confidence(self):
        r = il.classify("salir")
        assert r.confidence >= 0.90

    def test_salir_por_favor(self):
        """'salir por favor' → EXIT. Existing pattern."""
        r = il.classify("salir por favor")
        assert r.intent == EXIT

    def test_salir_por_favor_confidence(self):
        r = il.classify("salir por favor")
        assert r.confidence >= 0.90

    def test_quiero_salir(self):
        """'quiero salir' → EXIT. NEW pattern."""
        r = il.classify("quiero salir")
        assert r.intent == EXIT

    def test_quiero_salir_confidence(self):
        r = il.classify("quiero salir")
        assert r.confidence >= 0.90

    def test_hasta_luego(self):
        """'hasta luego' → EXIT. NEW pattern."""
        r = il.classify("hasta luego")
        assert r.intent == EXIT

    def test_hasta_luego_confidence(self):
        r = il.classify("hasta luego")
        assert r.confidence >= 0.90

    def test_nos_vemos(self):
        """'nos vemos' → EXIT. NEW pattern."""
        r = il.classify("nos vemos")
        assert r.intent == EXIT

    def test_nos_vemos_confidence(self):
        r = il.classify("nos vemos")
        assert r.confidence >= 0.90

    def test_adios(self):
        """'adios' → EXIT. NEW pattern."""
        r = il.classify("adios")
        assert r.intent == EXIT

    def test_adios_confidence(self):
        r = il.classify("adios")
        assert r.confidence >= 0.90


# ==========================================
# EXISTING PATTERNS STILL WORK
# ==========================================


class TestExitExistingStillWork:

    def test_exit_still_works(self):
        r = il.classify("exit")
        assert r.intent == EXIT

    def test_quit_still_works(self):
        r = il.classify("quit")
        assert r.intent == EXIT

    def test_salir_con_exclamation(self):
        r = il.classify("¡salir por favor!")
        assert r.intent == EXIT

    def test_salir_y_gracias(self):
        """'salir gracias' → THANKS or EXIT.
        EXIT EXACT 'salir' requires exact match,
        so THANKS PHRASE 'gracias' wins."""
        r = il.classify("salir gracias")
        assert r.intent in (EXIT, THANKS)


# ==========================================
# NEGATIVE CASES — SHOULD NOT BE EXIT
# ==========================================


class TestExitNegative:

    def test_no_quiero_salir(self):
        """'no quiero salir' → NOT EXIT.
        Negation present."""
        r = il.classify("no quiero salir")
        assert r.intent != EXIT

    def test_no_salir_por_favor(self):
        """'no salir por favor' → NOT EXIT.
        FALSE POSITIVE: PHRASE 'salir por favor'
        matches as substring."""
        r = il.classify("no salir por favor")
        assert r.intent != EXIT

    def test_no_voy_a_salir(self):
        """'no voy a salir' → NOT EXIT.
        Negation present."""
        r = il.classify("no voy a salir")
        assert r.intent != EXIT

    def test_quiero_salir_manana(self):
        """'quiero salir mañana' → NOT EXIT.
        Temporal context, not immediate exit."""
        r = il.classify("quiero salir mañana")
        assert r.intent != EXIT

    def test_puedo_salir(self):
        """'puedo salir?' → NOT EXIT.
        Question, not intent to exit."""
        r = il.classify("puedo salir?")
        assert r.intent != EXIT

    def test_si_quiero_salir(self):
        """'si quiero salir' → NOT EXIT.
        Affirmation with ambiguity."""
        r = il.classify("si quiero salir")
        assert r.intent != EXIT

    def test_salir_de_casa(self):
        """'salir de casa' → NOT EXIT.
        Physical departure, not conversational."""
        r = il.classify("salir de casa")
        assert r.intent != EXIT

    def test_quiero_salir_de_aqui_pero_no_ahora(self):
        """'quiero salir de aqui pero no ahora' → NOT EXIT.
        Explicit temporal negation."""
        r = il.classify(
            "quiero salir de aqui pero no ahora"
        )
        assert r.intent != EXIT


# ==========================================
# BOUNDARY CASES
# ==========================================


class TestExitBoundary:

    def test_hasta_luego_con_signos(self):
        """'¡Hasta luego!' → EXIT."""
        r = il.classify("¡Hasta luego!")
        assert r.intent == EXIT

    def test_adios_con_signos(self):
        """'¡Adiós!' → EXIT."""
        r = il.classify("¡Adiós!")
        assert r.intent == EXIT

    def test_nos_vemos_luego(self):
        """'nos vemos luego' → EXIT."""
        r = il.classify("nos vemos luego")
        assert r.intent == EXIT

    def test_hasta_luego_es_exit(self):
        """'hasta luego' -> EXIT."""
        r = il.classify("hasta luego")
        assert r.intent == EXIT

    def test_me_voy(self):
        """'me voy' → EXIT (natural farewell)."""
        r = il.classify("me voy")
        assert r.intent == EXIT
