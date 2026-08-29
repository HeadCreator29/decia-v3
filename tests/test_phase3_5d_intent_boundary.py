"""
PHASE 3.5D — Intent Boundary Audit
Tests cross-intent contamination between intent pairs.
NOTE: Speech corrections (kien→quien, ke→que, grasias→gracias)
are applied BEFORE the intent layer in main.py's correct_transcription().
This tests the intent layer with CORRECTED text.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "app"))

from brain.intent_layer import IntentLayer
from brain.intent_types import (
    GREETING, THANKS, EXIT, CALCULATE,
    DECIA_SELF, DECIA_CREATOR, ARCHIVE_DIRECT,
    MEMORY_CREATE, MEMORY_SEARCH, FREE_TALK,
    AMBIGUOUS_INPUT, PLANNER_QUERY,
)

il = IntentLayer()


def analyze(text):
    return il.classify(text)


class TestMemorySearchVsFreeTalk:

    def test_que_color_me_gusta(self):
        r = analyze("que color me gusta")
        assert r.intent == MEMORY_SEARCH

    def test_de_que_color_me_gusta(self):
        r = analyze("de que color me gusta")
        assert r.intent == MEMORY_SEARCH

    def test_que_musica_te_gusta(self):
        r = analyze("que musica te gusta")
        assert r.intent == FREE_TALK

    def test_que_es_un_perro(self):
        r = analyze("que es un perro")
        assert r.intent == FREE_TALK

    def test_que_significa_amor(self):
        r = analyze("que significa amor")
        assert r.intent == FREE_TALK

    def test_habla_de_ciencia(self):
        r = analyze("habla de ciencia")
        assert r.intent == FREE_TALK

    def test_cuentame_un_cuento(self):
        r = analyze("cuentame un cuento")
        assert r.intent in (AMBIGUOUS_INPUT, FREE_TALK)

    def test_que_tengo_manana(self):
        # PHASE 9.6 (delta autorizada): consulta de
        # planes futuros. "que tengo manana" ahora
        # clasifica PLANNER_QUERY (antes habría sido
        # MEMORY_SEARCH/FREE_TALK).
        r = analyze("que tengo manana")
        assert r.intent in (
            MEMORY_SEARCH, FREE_TALK, PLANNER_QUERY,
        )

    def test_como_se_llama_mi_perro(self):
        r = analyze("como se llama mi perro")
        assert r.intent == MEMORY_SEARCH


class TestMemoryCreateVsFreeTalk:

    def test_guarda_que_mi_color_es_azul(self):
        r = analyze("guarda que mi color es azul")
        assert r.intent == MEMORY_CREATE

    def test_recuerda_que_tengo_clase(self):
        r = analyze("recuerda que tengo clase")
        assert r.intent == MEMORY_CREATE

    def test_anota_que_es_lunes(self):
        r = analyze("anota que es lunes")
        assert r.intent == MEMORY_CREATE

    def test_memoriza_que_debo_comprar(self):
        r = analyze("memoriza que debo comprar pan")
        assert r.intent == MEMORY_CREATE

    def test_quiero_que_recuerdes_reunion(self):
        r = analyze("quiero que recuerdes reunion")
        assert r.intent == MEMORY_CREATE

    def test_guarda_que_not_free_talk(self):
        r = analyze("guarda que mi perro se llama max")
        assert r.intent == MEMORY_CREATE

    def test_que_es_un_aute(self):
        r = analyze("que es un auto")
        assert r.intent == FREE_TALK

    def test_hablame_de_tecnologia(self):
        r = analyze("hablame de tecnologia")
        assert r.intent == FREE_TALK


class TestDeciaSelfVsArchiveDirect:

    def test_quien_eres(self):
        r = analyze("quien eres")
        assert r.intent == DECIA_SELF

    def test_que_es_decia(self):
        r = analyze("que es decia")
        assert r.intent == DECIA_SELF

    def test_quien_es_decia(self):
        r = analyze("quien es decia")
        assert r.intent == DECIA_SELF

    def test_que_significa_decia(self):
        r = analyze("que significa decia")
        assert r.intent == DECIA_SELF

    def test_hablame_de_decia(self):
        r = analyze("hablame de decia")
        assert r.intent == DECIA_SELF

    def test_que_es_deca(self):
        r = analyze("que es deca")
        assert r.intent == ARCHIVE_DIRECT

    def test_quien_creo_deca(self):
        r = analyze("quien creo deca")
        assert r.intent == ARCHIVE_DIRECT

    def test_que_significa_deca(self):
        r = analyze("que significa deca")
        assert r.intent == ARCHIVE_DIRECT

    def test_hablame_de_deca(self):
        r = analyze("hablame de deca")
        assert r.intent == ARCHIVE_DIRECT

    def test_origen_de_deca(self):
        r = analyze("origen de deca")
        assert r.intent == ARCHIVE_DIRECT

    def test_decia_not_deca(self):
        r1 = analyze("que es decia")
        r2 = analyze("que es deca")
        assert r1.intent == DECIA_SELF
        assert r2.intent == ARCHIVE_DIRECT
        assert r1.intent != r2.intent


class TestCalculateVsFreeTalk:

    def test_dos_mas_dos(self):
        r = analyze("2+2")
        assert r.intent == CALCULATE

    def test_cinco_por_cuatro(self):
        r = analyze("5 por 4")
        assert r.intent == CALCULATE

    def test_cuanto_es_veinte(self):
        r = analyze("cuanto es 20 mas 5")
        assert r.intent == CALCULATE

    def test_tengo_dos_perros(self):
        r = analyze("tengo 2 perros")
        assert r.intent == FREE_TALK

    def test_compre_5_cosas(self):
        r = analyze("compre 5 cosas")
        assert r.intent == FREE_TALK

    def test_hay_100_personas(self):
        r = analyze("hay 100 personas en la sala")
        assert r.intent == FREE_TALK

    def test_calcular_still_works(self):
        r = analyze("calcular 10 menos 3")
        assert r.intent in (CALCULATE, FREE_TALK)


class TestExitVsFreeTalk:

    def test_salir(self):
        r = analyze("salir")
        assert r.intent == EXIT

    def test_quiero_salir(self):
        r = analyze("quiero salir")
        assert r.intent == EXIT

    def test_hasta_luego(self):
        r = analyze("hasta luego")
        assert r.intent == EXIT

    def test_adios(self):
        r = analyze("adios")
        assert r.intent == EXIT

    def test_no_quiero_salir(self):
        r = analyze("no quiero salir")
        assert r.intent != EXIT

    def test_salir_de_casa(self):
        r = analyze("salir de casa")
        assert r.intent != EXIT

    def test_me_voy(self):
        r = analyze("me voy")
        assert r.intent in (EXIT, AMBIGUOUS_INPUT)

    def test_nos_vemos(self):
        r = analyze("nos vemos")
        assert r.intent == EXIT


class TestGreetingVsFreeTalk:

    def test_hola(self):
        r = analyze("hola")
        assert r.intent == GREETING

    def test_buenos_dias(self):
        r = analyze("buenos dias")
        assert r.intent == GREETING

    def test_buenas_tardes(self):
        r = analyze("buenas tardes")
        assert r.intent == GREETING

    def test_oye_hola(self):
        r = analyze("oye hola")
        assert r.intent == GREETING

    def test_hola_decia(self):
        r = analyze("hola decia")
        assert r.intent == GREETING

    def test_como_estas(self):
        r = analyze("como estas")
        assert r.intent == AMBIGUOUS_INPUT

    def test_que_tal(self):
        r = analyze("que tal")
        assert r.intent == AMBIGUOUS_INPUT


class TestDeciaCreatorVsArchiveDirect:

    def test_quien_te_creo(self):
        r = analyze("quien te creo")
        assert r.intent == DECIA_CREATOR

    def test_quien_te_creo_decia(self):
        r = analyze("quien te creo decia")
        assert r.intent == DECIA_CREATOR

    def test_quien_fundo_deca(self):
        r = analyze("quien fundo deca")
        assert r.intent in (DECIA_CREATOR, ARCHIVE_DIRECT)

    def test_quien_creo_deca(self):
        r = analyze("quien creo deca")
        assert r.intent == ARCHIVE_DIRECT

    def test_creator_not_archive(self):
        r1 = analyze("quien te creo")
        r2 = analyze("quien creo deca")
        assert r1.intent == DECIA_CREATOR
        assert r2.intent == ARCHIVE_DIRECT


class TestWhisperCorrectedInputs:
    """Whisper corrections are applied BEFORE the intent layer.
    These tests verify the corrected text classifies correctly."""

    def test_quien_eres(self):
        r = analyze("quien eres")
        assert r.intent == DECIA_SELF

    def test_que_es_deca(self):
        r = analyze("que es deca")
        assert r.intent == ARCHIVE_DIRECT

    def test_gracias(self):
        r = analyze("gracias")
        assert r.intent == THANKS

    def test_quien_te_creo(self):
        r = analyze("quien te creo")
        assert r.intent == DECIA_CREATOR

    def test_que_significa_deca(self):
        r = analyze("que significa deca")
        assert r.intent == ARCHIVE_DIRECT

    def test_raw_whisper_misspelled_not_at_intent_level(self):
        """Raw misspelled text does NOT match at intent layer.
        Corrections must be applied upstream."""
        r = analyze("kien eres")
        assert r.intent != DECIA_SELF

    def test_raw_ke_not_at_intent_level(self):
        r = analyze("ke es deca")
        assert r.intent != ARCHIVE_DIRECT


class TestNaturalSpanishVariations:

    def test_hablame_sobre_decia(self):
        r = analyze("hablame sobre decia")
        assert r.intent == DECIA_SELF

    def test_cuentame_de_deca(self):
        r = analyze("cuentame de deca")
        assert r.intent == ARCHIVE_DIRECT

    def test_dime_quien_eres(self):
        r = analyze("dime quien eres")
        assert r.intent == DECIA_SELF

    def test_como_te_llamas(self):
        r = analyze("como te llamas")
        assert r.intent == DECIA_SELF

    def test_cual_es_tu_nombre(self):
        r = analyze("cual es tu nombre")
        assert r.intent == DECIA_SELF

    def test_de_donde_vienes(self):
        r = analyze("de donde vienes")
        assert r.intent == DECIA_SELF

    def test_para_que_sirves(self):
        r = analyze("para que sirves")
        assert r.intent in (DECIA_SELF, FREE_TALK)

    def test_que_puedes_hacer(self):
        r = analyze("que puedes hacer")
        assert r.intent in (DECIA_SELF, FREE_TALK)
