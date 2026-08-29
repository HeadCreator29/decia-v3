"""
DECIA v2 — Phase 2E: Natural Language Boundary Hardening
=========================================================

Objetivo: Hacer cambios mínimos y deterministas para
cerrar las brechas naturales descubiertas en Phase 2D.

Prioridades:
P1 — Frases naturales (THANKS, EXIT, CALCULATE)
P2 — ARCHIVE_DIRECT natural ("háblame/cuéntame de DECA")
P3 — DECIA_CREATOR auditoría (sin cambios)
P4 — Whisper-like auditoría (sin cambios en Intent Layer)
P5 — AMBIGUOUS confidence auditoría (sin cambios)

Crear tests ANTES de modificar producción.
Ejecutar baseline → clasificar PASS/FINDING/REGRESSION.
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
    EXIT,
    CALCULATE,
    DECIA_SELF,
    DECIA_CREATOR,
    ARCHIVE_DIRECT,
    ARCHIVE_SEARCH,
    USER_NAME_ASK,
    MEMORY_CREATE,
    MEMORY_SEARCH,
    AMBIGUOUS_INPUT,
    FREE_TALK,
)

il = IntentLayer()

_SAFE_INTENTS = {
    GREETING,
    THANKS,
    EXIT,
    CALCULATE,
    DECIA_SELF,
    DECIA_CREATOR,
    ARCHIVE_DIRECT,
}


def analyze(text):
    r = il.classify(text)
    return {
        "intent": r.intent,
        "score": r.candidates[0].score if r.candidates else 0,
        "confidence": r.confidence,
        "would_auto_route": (
            r.confidence >= 0.90
            and r.intent in _SAFE_INTENTS
        ),
        "matched_pattern": (
            r.candidates[0].matched_pattern
            if r.candidates else None
        ),
        "num_candidates": len(r.candidates),
    }


# ==========================================
# P1 — NATURAL PHRASES: THANKS
# ==========================================


class TestNaturalThanks:

    def test_gracias_por_ayudarme(self):
        """'gracias por ayudarme' → THANKS.
        PHRASE 'gracias' matches substring."""
        r = il.classify("gracias por ayudarme")
        assert r.intent == THANKS

    def test_gracias_por_ayudarme_confidence(self):
        """THANKS PHRASE 'gracias' score 90,
        no second candidate → conf >= 0.90."""
        r = il.classify("gracias por ayudarme")
        assert r.confidence >= 0.90

    def test_te_doy_las_gracias(self):
        """'te doy las gracias' → THANKS."""
        r = il.classify("te doy las gracias")
        assert r.intent == THANKS

    def test_gracias_de_verdad(self):
        """'gracias de verdad' → THANKS."""
        r = il.classify("gracias de verdad")
        assert r.intent == THANKS

    def test_graciasporayudarme(self):
        """'graciasporayudarme' (no spaces) → THANKS.
        PHRASE substring match."""
        r = il.classify("graciasporayudarme")
        assert r.intent == THANKS

    def test_gracias_exact_still_works(self):
        """'gracias' exact still → THANKS."""
        r = il.classify("gracias")
        assert r.intent == THANKS
        assert r.confidence >= 0.90

    def test_muchas_gracias_still_works(self):
        """'muchas gracias' still → THANKS."""
        r = il.classify("muchas gracias")
        assert r.intent == THANKS

    def test_no_gracias_not_thanks(self):
        """'no gracias' should still be THANKS
        (polite refusal, but 'gracias' present)."""
        r = il.classify("no gracias")
        assert r.intent == THANKS

    def test_gracias_a_todos(self):
        """'gracias a todos' → THANKS."""
        r = il.classify("gracias a todos")
        assert r.intent == THANKS

    def test_gracias_por_todo(self):
        """'gracias por todo' → THANKS."""
        r = il.classify("gracias por todo")
        assert r.intent == THANKS


# ==========================================
# P1 — NATURAL PHRASES: EXIT
# ==========================================


class TestNaturalExit:

    def test_salir_por_favor(self):
        """'salir por favor' → EXIT.
        PHRASE 'salir por favor' matches."""
        r = il.classify("salir por favor")
        assert r.intent == EXIT

    def test_salir_por_favor_confidence(self):
        """EXIT PHRASE score 90, no second → conf >= 0.90."""
        r = il.classify("salir por favor")
        assert r.confidence >= 0.90

    def test_quiero_salir(self):
        """'quiero salir' → EXIT (Phase 3.2B: added as exact pattern).
        Negation check prevents 'no quiero salir' false positive."""
        r = il.classify("quiero salir")
        assert r.intent == EXIT
        assert r.confidence >= 0.90

    def test_salir_exact_still_works(self):
        """'salir' exact still → EXIT."""
        r = il.classify("salir")
        assert r.intent == EXIT
        assert r.confidence >= 0.90

    def test_exit_still_works(self):
        r = il.classify("exit")
        assert r.intent == EXIT

    def test_salir_con_exclamation(self):
        r = il.classify("¡salir por favor!")
        assert r.intent == EXIT

    def test_no_quiero_salir_not_exit(self):
        """'no quiero salir' should NOT be EXIT.
        PHRASE 'quiero salir' would match substring
        but context is negative."""
        a = analyze("no quiero salir")
        assert a["intent"] != EXIT


# ==========================================
# P1 — NATURAL PHRASES: CALCULATE
# ==========================================


class TestNaturalCalculate:

    def test_dos_mas_dos(self):
        """'2 más 2' → CALCULATE.
        After normalize: '2 mas 2'. REGEX matches."""
        r = il.classify("2 más 2")
        assert r.intent == CALCULATE

    def test_dos_mas_dos_confidence(self):
        r = il.classify("2 más 2")
        assert r.confidence >= 0.90

    def test_dos_menos_uno(self):
        """'2 menos 1' → CALCULATE."""
        r = il.classify("2 menos 1")
        assert r.intent == CALCULATE

    def test_cinco_por_cuatro(self):
        """'5 por 4' → CALCULATE."""
        r = il.classify("5 por 4")
        assert r.intent == CALCULATE

    def test_veinte_entre_cinco(self):
        """'20 entre 5' → CALCULATE."""
        r = il.classify("20 entre 5")
        assert r.intent == CALCULATE

    def test_symbol_form_still_works(self):
        """'2+2' still → CALCULATE."""
        r = il.classify("2+2")
        assert r.intent == CALCULATE
        assert r.confidence >= 0.90

    def test_complex_symbol_still_works(self):
        """'(3+5)*2' still → CALCULATE."""
        r = il.classify("(3+5)*2")
        assert r.intent == CALCULATE

    def test_diez_mas_tres_menos_uno(self):
        """'10 más 3 menos 1' → CALCULATE."""
        r = il.classify("10 más 3 menos 1")
        assert r.intent == CALCULATE


# ==========================================
# P2 — ARCHIVE_DIRECT NATURAL PHRASES
# ==========================================


class TestNaturalArchiveDirect:

    def test_hablame_de_deca(self):
        """'háblame de DECA' → ARCHIVE_DIRECT.
        PHRASE 'hablame de deca' matches."""
        r = il.classify("háblame de DECA")
        assert r.intent == ARCHIVE_DIRECT

    def test_hablame_de_deca_confidence(self):
        r = il.classify("háblame de DECA")
        assert r.confidence >= 0.90

    def test_cuentame_de_deca(self):
        """'cuéntame de DECA' → ARCHIVE_DIRECT.
        PHRASE 'cuentame de deca' matches."""
        r = il.classify("cuéntame de DECA")
        assert r.intent == ARCHIVE_DIRECT

    def test_cuentame_de_deca_confidence(self):
        r = il.classify("cuéntame de DECA")
        assert r.confidence >= 0.90

    def test_cuentame_un_poco_sobre_deca(self):
        """'cuéntame un poco sobre DECA' → ARCHIVE_DIRECT.
        PHRASE 'cuentame un poco sobre deca' matches."""
        r = il.classify(
            "cuéntame un poco sobre DECA"
        )
        assert r.intent == ARCHIVE_DIRECT

    def test_cuentame_un_poco_confidence(self):
        r = il.classify(
            "cuéntame un poco sobre DECA"
        )
        assert r.confidence >= 0.90

    def test_hablame_de_deca_with_marks(self):
        r = il.classify("¿háblame de DECA?")
        assert r.intent == ARCHIVE_DIRECT

    def test_cuentame_de_deca_with_marks(self):
        r = il.classify("¿cuéntame de DECA?")
        assert r.intent == ARCHIVE_DIRECT

    def test_hablame_de_otro_tema_not_archive(self):
        """'háblame de historia' → not ARCHIVE_DIRECT
        (no DECA keyword)."""
        r = il.classify("háblame de historia")
        assert r.intent != ARCHIVE_DIRECT

    def test_cuentame_de_otro_tema_not_archive(self):
        """'cuéntame de ciencia' → not ARCHIVE_DIRECT."""
        r = il.classify("cuéntame de ciencia")
        assert r.intent != ARCHIVE_DIRECT

    def test_hablame_de_deca_auto_routes(self):
        """ARCHIVE_DIRECT + conf >= 0.90 → auto-route."""
        a = analyze("háblame de DECA")
        assert a["would_auto_route"]

    def test_cuentame_de_deca_auto_routes(self):
        a = analyze("cuéntame de DECA")
        assert a["would_auto_route"]


# ==========================================
# P3 — DECIA_CREATOR AUDIT (sin cambios)
# ==========================================


class TestCreatorAudit:

    def test_quien_creo_esto_stays_creator(self):
        """'quién creó esto' → DECIA_CREATOR.
        By design: 'quién creó' is DECIA_CREATOR."""
        r = il.classify("quién creó esto")
        assert r.intent == DECIA_CREATOR

    def test_quien_creo_el_proyecto_stays_creator(self):
        """'quién creó el proyecto' → DECIA_CREATOR.
        By design."""
        r = il.classify("quién creó el proyecto")
        assert r.intent == DECIA_CREATOR

    def test_creador_single_word_stays_creator(self):
        """'creador' → DECIA_CREATOR (keyword).
        By design."""
        r = il.classify("creador")
        assert r.intent == DECIA_CREATOR

    def test_quien_creo_deca_stays_archive(self):
        """'quién creó DECA' → ARCHIVE_DIRECT.
        DECA keyword overrides creator."""
        r = il.classify("quién creó DECA")
        assert r.intent == ARCHIVE_DIRECT

    def test_quien_te_creo_stays_creator(self):
        """'quién te creó' → DECIA_CREATOR.
        Strong phrase match."""
        r = il.classify("quién te creó")
        assert r.intent == DECIA_CREATOR
        assert r.confidence >= 0.90


# ==========================================
# P4 — WHISPER-LIKE AUDIT (sin cambios)
# ==========================================


class TestWhisperAudit:

    def test_kien_eres_stays_ambiguous(self):
        """'kien eres' → AMBIGUOUS_INPUT.
        FINDING: 'kien' not normalized.
        Fix belongs in speech_corrections.py."""
        a = analyze("kien eres")
        assert a["intent"] == AMBIGUOUS_INPUT

    def test_kien_te_creo_classification(self):
        """'kien te creo' → FREE_TALK (ya no
        ARCHIVE). Phase 6.6: keyword 'creo'
        retirada de ARCHIVE_SEARCH (FP auditado).
        Misspelling sin match → OLLAMA."""
        a = analyze("kien te creo")
        assert a["intent"] in (
            DECIA_CREATOR, FREE_TALK,
        )

    def test_ke_significa_deca_classification(self):
        """'ke significa deca' → FREE_TALK or
        ARCHIVE_DIRECT. FINDING: 'ke' not normalized."""
        a = analyze("ke significa deca")
        assert a["intent"] in (
            FREE_TALK, ARCHIVE_DIRECT,
        )

    def test_grasias_classification(self):
        """'grasias' → AMBIGUOUS_INPUT or THANKS.
        FINDING: misspelling not normalized."""
        r = il.classify("grasias")
        assert r.intent in (
            THANKS, AMBIGUOUS_INPUT,
        )


# ==========================================
# P5 — AMBIGUOUS CONFIDENCE AUDIT
# ==========================================


class TestAmbiguousAudit:

    def test_algo_confidence_is_one(self):
        """'algo' → AMBIGUOUS_INPUT conf=1.0.
        By design: no candidates, <=2 words."""
        r = il.classify("algo")
        assert r.intent == AMBIGUOUS_INPUT
        assert r.confidence == 1.0

    def test_mira_confidence_is_one(self):
        r = il.classify("mira")
        assert r.intent == AMBIGUOUS_INPUT
        assert r.confidence == 1.0

    def test_ambigous_not_in_safe_intents(self):
        """AMBIGUOUS_INPUT is NOT in _SAFE_INTENTS.
        Confidence=1.0 doesn't cause auto-route."""
        assert AMBIGUOUS_INPUT not in _SAFE_INTENTS

    def test_ambigous_confidence_no_auto_route(self):
        """Even with conf=1.0, AMBIGUOUS_INPUT
        does NOT auto-route."""
        a = analyze("algo")
        assert not a["would_auto_route"]
