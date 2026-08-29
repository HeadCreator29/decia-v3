import sys, os
import pytest

sys.path.insert(0, r"C:\Users\idelv\Desktop\DECIA_v2\app")
os.chdir(r"C:\Users\idelv\Desktop\DECIA_v2\app")

from brain.intent_layer import IntentLayer
from brain.intent_types import (
    MEMORY_SEARCH, MEMORY_CREATE, FREE_TALK,
    AMBIGUOUS_INPUT, DECIA_SELF, ARCHIVE_DIRECT,
    CONFIDENCE_SEGURO, CONFIDENCE_PROBABLE,
    CONFIDENCE_AMBIGUO,
)
from brain.handlers import (
    ambiguous_input_response, memory_request,
)

il = IntentLayer()


class TestMemoryRecallPatterns:
    """Natural recall questions should classify as
    MEMORY_SEARCH."""

    def test_que_recuerdas(self):
        r = il.classify("que recuerdas")
        assert r.intent == MEMORY_SEARCH

    def test_que_recuerdas_confidence(self):
        r = il.classify("que recuerdas")
        assert r.confidence >= CONFIDENCE_AMBIGUO

    def test_que_te_dije(self):
        r = il.classify("que te dije")
        assert r.intent == MEMORY_SEARCH

    def test_que_te_dije_confidence(self):
        r = il.classify("que te dije")
        assert r.confidence >= CONFIDENCE_AMBIGUO

    def test_que_recuerdas_de_mi_color(self):
        r = il.classify(
            "que recuerdas de mi color favorito"
        )
        assert r.intent == MEMORY_SEARCH

    def test_que_te_dije_que_tengo_manana(self):
        r = il.classify(
            "que te dije que tengo manana"
        )
        assert r.intent == MEMORY_SEARCH

    def test_recuerdame_lo_que_hablamos_hoy(self):
        r = il.classify(
            "recuerdame lo que hablamos hoy"
        )
        assert r.intent == MEMORY_SEARCH

    def test_que_hemos_hablado_hoy(self):
        r = il.classify("que hemos hablado hoy")
        assert r.intent == MEMORY_SEARCH

    def test_que_cosas_recuerdas_de_mi(self):
        r = il.classify(
            "que cosas recuerdas de mi"
        )
        assert r.intent == MEMORY_SEARCH


class TestMemoryCreateStillWorks:
    """Memory creation patterns must not be affected."""

    def test_recuerda_que_tengo_clase(self):
        r = il.classify(
            "recuerda que tengo clase manana"
        )
        assert r.intent == MEMORY_CREATE
        assert r.confidence >= CONFIDENCE_SEGURO

    def test_guarda_que_me_gusta_el_cafe(self):
        r = il.classify(
            "guarda que me gusta el cafe"
        )
        assert r.intent == MEMORY_CREATE
        assert r.confidence >= CONFIDENCE_SEGURO

    def test_anota_que_es_lunes(self):
        r = il.classify("anota que es lunes")
        assert r.intent == MEMORY_CREATE


class TestNegativeCases:
    """Non-memory questions must not become
    MEMORY_SEARCH."""

    def test_quien_soy_is_not_memory(self):
        r = il.classify("quien soy")
        assert r.intent != MEMORY_SEARCH

    def test_que_es_deca_is_archive(self):
        r = il.classify("que es deca")
        assert r.intent == ARCHIVE_DIRECT

    def test_cuentame_algo_is_not_memory(self):
        r = il.classify("cuentame algo")
        assert r.intent != MEMORY_SEARCH

    def test_hola_is_greeting(self):
        r = il.classify("hola")
        assert r.intent == "GREETING"

    def test_algo_is_ambiguous(self):
        r = il.classify("algo")
        assert r.intent == AMBIGUOUS_INPUT


class TestBoundaryProtection:
    """Ensure MEMORY_CREATE vs MEMORY_SEARCH
    separation is preserved."""

    def test_recuerda_que_vs_que_recuerdas(self):
        create = il.classify(
            "recuerda que tengo clase"
        )
        search = il.classify("que recuerdas")
        assert create.intent == MEMORY_CREATE
        assert search.intent == MEMORY_SEARCH

    def test_recuerdame_not_create(self):
        r = il.classify(
            "recuerdame lo que hablamos"
        )
        assert r.intent != MEMORY_CREATE

    def test_dije_not_create(self):
        r = il.classify("que te dije")
        assert r.intent != MEMORY_CREATE
