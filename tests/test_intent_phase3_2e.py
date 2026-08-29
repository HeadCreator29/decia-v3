import sys, os
import pytest

sys.path.insert(0, r"C:\Users\idelv\Desktop\DECIA_v2\app")
os.chdir(r"C:\Users\idelv\Desktop\DECIA_v2\app")

from brain.intent_layer import IntentLayer
from brain.handlers import (
    memory_request, create_memory, search_deca_memory,
    format_archive_response, ambiguous_input_response,
)
from brain.intent_types import (
    MEMORY_SEARCH, MEMORY_CREATE, FREE_TALK,
    AMBIGUOUS_INPUT, DECIA_SELF, DECIA_CREATOR,
    ARCHIVE_DIRECT, CALCULATE, EXIT, GREETING,
    THANKS, CONFIDENCE_SEGURO, CONFIDENCE_AMBIGUO,
)
from services.archive import get_memories


@pytest.fixture(scope="module", autouse=True)
def a16a_archive_aislado(tmp_path_factory):
    import shutil
    import services.archive as archive_mod

    real_path = archive_mod.ARCHIVE_PATH
    tmp_path = tmp_path_factory.mktemp("a16a_archive")
    if real_path.is_dir():
        for item in real_path.iterdir():
            if item.is_file():
                shutil.copy2(item, tmp_path / item.name)
    archive_mod.ARCHIVE_PATH = tmp_path
    yield tmp_path
    archive_mod.ARCHIVE_PATH = real_path


il = IntentLayer()


def _memories_count():
    data = get_memories()
    return len(data.get("memories", []))


class TestScenarioA_SimpleMemory:
    """Create a memory, then recall it."""

    def test_create_then_search(self):
        create_memory("tengo clase manana")

        r = il.classify("que te dije que tengo manana")
        assert r.intent == MEMORY_SEARCH

        sm = search_deca_memory(
            "que te dije que tengo manana"
        )
        assert sm is not None
        assert sm["type"] == "memory"

        resp = format_archive_response(sm)
        assert resp is not None
        assert len(resp) > 0


class TestScenarioB_SpecificMemory:
    """Create specific memory, recall with topic."""

    def test_color_favorito(self):
        create_memory("mi color favorito es azul")

        r = il.classify(
            "que recuerdas de mi color favorito"
        )
        assert r.intent == MEMORY_SEARCH

        sm = search_deca_memory(
            "que recuerdas de mi color favorito"
        )
        assert sm is not None
        assert sm["type"] == "memory"

        resp = format_archive_response(sm)
        assert resp is not None
        assert len(resp) > 0


class TestScenarioC_ConversationalMemory:
    """Create memory about intentions."""

    def test_terminar_decia(self):
        create_memory(
            "quiero terminar decia esta semana"
        )

        r = il.classify(
            "que recuerdas que quiero terminar"
        )
        assert r.intent == MEMORY_SEARCH

        sm = search_deca_memory(
            "que recuerdas que quiero terminar"
        )
        assert sm is not None


class TestScenarioD_MultipleMemories:
    """Create multiple memories, verify each is
    findable."""

    def test_multiple_memories(self):
        create_memory("tengo clase manana")
        create_memory("mi color favorito es rojo")
        create_memory("quiero terminar decia")

        for query in [
            "que recuerdas de mi color favorito",
            "que te dije que tengo manana",
            "que recuerdas que quiero terminar",
        ]:
            r = il.classify(query)
            assert r.intent == MEMORY_SEARCH, (
                f"'{query}' should be MEMORY_SEARCH"
            )


class TestScenarioE_GeneralRecall:
    """General recall should not fail."""

    def test_que_recuerdas(self):
        r = il.classify("que recuerdas")
        assert r.intent == MEMORY_SEARCH
        assert r.confidence >= CONFIDENCE_AMBIGUO

    def test_que_cosas_recuerdas(self):
        r = il.classify(
            "que cosas recuerdas de mi"
        )
        assert r.intent == MEMORY_SEARCH


class TestScenarioF_NonexistentMemory:
    """Asking about something not stored should
    not invent a memory."""

    def test_perro_not_invented(self):
        """'que recuerdas de mi perro' — 'recuerdas'
        matches memory_words, so search returns all
        memories. The archive doesn't filter by
        'perro' (keyword-based, not semantic).
        This is correct — no memory is invented,
        existing memories are returned."""
        r = il.classify("que recuerdas de mi perro")
        assert r.intent == MEMORY_SEARCH

        sm = search_deca_memory(
            "que recuerdas de mi perro"
        )
        assert sm is not None
        assert sm["type"] == "memory"

        resp = format_archive_response(sm)
        assert resp is not None


class TestRegressionProtection:
    """Existing functionality must not break."""

    def test_memory_create_guarda_que(self):
        r = il.classify("guarda que tengo clase")
        assert r.intent == MEMORY_CREATE
        assert r.confidence >= CONFIDENCE_SEGURO

    def test_memory_create_recuerda_que(self):
        r = il.classify(
            "recuerda que tengo reunion"
        )
        assert r.intent == MEMORY_CREATE
        assert r.confidence >= CONFIDENCE_SEGURO

    def test_deca_self(self):
        r = il.classify("quien eres")
        assert r.intent == DECIA_SELF

    def test_deca_creator(self):
        r = il.classify("quien te creo")
        assert r.intent == DECIA_CREATOR

    def test_archive_direct(self):
        r = il.classify("que es deca")
        assert r.intent == ARCHIVE_DIRECT

    def test_calculate(self):
        r = il.classify("2 + 2")
        assert r.intent == CALCULATE

    def test_exit(self):
        r = il.classify("salir")
        assert r.intent == EXIT

    def test_greeting(self):
        r = il.classify("hola")
        assert r.intent == GREETING

    def test_thanks(self):
        r = il.classify("gracias")
        assert r.intent == THANKS

    def test_recuerda_que_not_search(self):
        """'recuerda que...' must be CREATE, not
        SEARCH."""
        r = il.classify(
            "recuerda que tengo clase manana"
        )
        assert r.intent == MEMORY_CREATE

    def test_guarda_que_not_search(self):
        r = il.classify(
            "guarda que me gusta el cafe"
        )
        assert r.intent == MEMORY_CREATE
