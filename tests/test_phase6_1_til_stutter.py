"""
PHASE 6.1 — TIL / TRANSCRIPTION ROBUSTNESS
Conservative immediate-token stutter collapse in the
Transcription Interpretation Layer.

Only mechanical evidence (consecutive identical short
lowercase tokens, not in the protected-emphasis set)
is corrected. All other transcription is preserved.
"""
import pytest
import sys
from pathlib import Path

sys.path.insert(
    0,
    str(Path(__file__).resolve().parents[1] / "app"),
)

from utils.speech_corrections import (
    correct_transcription,
    collapse_repeated_tokens,
)

from brain.intent_layer import IntentLayer


# ==========================================
# CASOS OBSERVADOS (reproducción A-E)
# ==========================================


class TestObservedCases:

    def test_a_que_dia_dia_es(self):
        assert (
            correct_transcription("Que dia dia es")
            == "Que dia es"
        )

    def test_a_llega_a_date_no_a_ollama(self):
        result = correct_transcription(
            "que dia dia es"
        )
        intent = IntentLayer().classify(result)
        assert intent.intent == "DATE"
        assert intent.confidence >= 0.90

    def test_b_eco_multipalabra_intacto(self):
        original = (
            "Y es Rera. Rera. Rera. Vaya. Vamos."
        )
        assert (
            correct_transcription(original)
            == original
        )

    def test_c_sobreerrera_no_inventada(self):
        assert (
            correct_transcription("sobreerrera")
            == "sobreerrera"
        )

    def test_d_recuerda_desea_intacto(self):
        original = (
            "Recuerda que quiero terminar "
            "desea esta semana"
        )
        assert (
            correct_transcription(original)
            == original
        )

    def test_e_que_recuerdas_sobre_este_intacto(
        self,
    ):
        original = "Qué recuerdas sobre este"
        assert (
            correct_transcription(original)
            == original
        )


# ==========================================
# STUTTER (ejemplos de la propuesta)
# ==========================================


class TestStutterCollapse:

    def test_que_dia_dia_es(self):
        assert (
            collapse_repeated_tokens(
                "que dia dia es"
            )
            == "que dia es"
        )

    def test_yo_yo_quiero_terminar(self):
        assert (
            collapse_repeated_tokens(
                "yo yo quiero terminar"
            )
            == "yo quiero terminar"
        )

    def test_triple_colapsa_a_uno(self):
        assert (
            collapse_repeated_tokens(
                "dia dia dia es"
            )
            == "dia es"
        )

    def test_preserva_espacios_extremos(self):
        assert (
            collapse_repeated_tokens(
                "  que dia dia es  "
            )
            == "  que dia es  "
        )


# ==========================================
# REPETICIÓN LEGÍTIMA NO DESTRUIDA
# ==========================================


class TestLegitimateRepetitionPreserved:

    def test_muy_muy_bueno(self):
        original = "muy muy bueno"
        assert (
            collapse_repeated_tokens(original)
            == original
        )

    def test_si_si_no_colapsa(self):
        original = "si si claro"
        assert (
            collapse_repeated_tokens(original)
            == original
        )

    def test_no_no_no_colapsa(self):
        original = "no no lo hagas"
        assert (
            collapse_repeated_tokens(original)
            == original
        )

    def test_palabras_largas_no_colapsan(self):
        original = "cafe cafe"
        assert (
            collapse_repeated_tokens(original)
            == original
        )

    def test_nombre_propio_con_mayuscula(self):
        original = "hablo de De la Cruz"
        assert (
            collapse_repeated_tokens(original)
            == original
        )

    def test_token_con_puntuacion_no_colapsa(
        self,
    ):
        original = "Rera. Rera. Rera."
        assert (
            collapse_repeated_tokens(original)
            == original
        )


# ==========================================
# REGLAS EXISTENTES INTACTAS (las 5)
# ==========================================


class TestExistingFiveRulesIntact:

    def test_kien(self):
        assert (
            correct_transcription("kien eres")
            == "quien eres"
        )

    def test_ke(self):
        assert (
            correct_transcription("ke significa")
            == "que significa"
        )

    def test_grasias(self):
        assert (
            correct_transcription("grasias")
            == "gracias"
        )

    def test_planeta_martes(self):
        result = correct_transcription(
            "planeta martes"
        )
        assert "Marte" in result

    def test_planeta_mal(self):
        result = correct_transcription(
            "planeta mal"
        )
        assert "Marte" in result

    def test_planeta_marte_no_corregido(self):
        assert (
            correct_transcription(
                "planeta marte"
            )
            == "planeta Marte"
        )