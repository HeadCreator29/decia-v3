import sys, os, json
sys.path.insert(0, r"C:\Users\idelv\Desktop\DECIA_v2\app")
os.chdir(r"C:\Users\idelv\Desktop\DECIA_v2\app")

import pytest
from brain.intent_layer import IntentLayer
from brain.core import think
from services.archive import (
    search_archive, get_memories, save_memory, ARCHIVE_PATH
)

il = IntentLayer()


@pytest.fixture(autouse=True)
def setup_test_memories():
    """Save test memories and restore original after test."""
    original = get_memories()

    test_memories = [
        {"id": "test_001", "date": "2026-08-26", "time": "10:00",
         "description": "mi color favorito es azul"},
        {"id": "test_002", "date": "2026-08-26", "time": "10:01",
         "description": "quiero terminar DECIA"},
        {"id": "test_003", "date": "2026-08-26", "time": "10:02",
         "description": "mañana tengo clase"},
        {"id": "test_004", "date": "2026-08-26", "time": "10:03",
         "description": "mi perro se llama Max"},
        {"id": "test_005", "date": "2026-08-26", "time": "10:04",
         "description": "me gusta la música de Kanye"},
    ]

    for m in test_memories:
        save_memory(m)

    yield

    path = ARCHIVE_PATH / "memories.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(original, f, ensure_ascii=False, indent=2)


def _reaches_memory_search(query):
    """Check if query classifies as MEMORY_SEARCH."""
    r = il.classify(query)
    return r.intent == "MEMORY_SEARCH"


def _memory_search_returns_relevant(query, keyword):
    """Check if search_archive returns memory containing keyword."""
    results = search_archive(query)
    memory_results = [r for r in results if r["type"] == "memory"]
    if not memory_results:
        return False
    all_descs = " ".join(
        m["description"] for r in memory_results for m in r["data"]
    )
    return keyword in all_descs.lower()


# =========================================================
# TARGET CASES — should reach MEMORY_SEARCH
# =========================================================

class TestTargetNaturalQuestions:
    """Natural questions about user info should reach memory search."""

    def test_que_color_me_gusta(self):
        """FINDING: goes to FREE_TALK, should reach MEMORY_SEARCH."""
        assert _reaches_memory_search("que color me gusta")

    def test_de_que_color_me_gusta(self):
        """FINDING: goes to FREE_TALK, should reach MEMORY_SEARCH."""
        assert _reaches_memory_search("de que color me gusta")

    def test_que_proyecto_quiero_terminar(self):
        """FINDING: goes to FREE_TALK, should reach MEMORY_SEARCH."""
        assert _reaches_memory_search("que proyecto quiero terminar")

    def test_que_musica_me_gusta(self):
        """FINDING: goes to FREE_TALK, should reach MEMORY_SEARCH."""
        assert _reaches_memory_search("que musica me gusta")

    def test_como_se_llama_mi_perro(self):
        """FINDING: goes to FREE_TALK, should reach MEMORY_SEARCH."""
        assert _reaches_memory_search("como se llama mi perro")


# =========================================================
# NEGATIVE CASES — should NOT reach MEMORY_SEARCH
# =========================================================

class TestNegativeGeneralQuestions:
    """General knowledge questions should NOT reach memory search."""

    def test_que_es_un_perro(self):
        """PASS: goes to FREE_TALK correctly."""
        assert not _reaches_memory_search("que es un perro")

    def test_que_es_una_computadora(self):
        """PASS: goes to FREE_TALK correctly."""
        assert not _reaches_memory_search("que es una computadora")

    def test_que_musica_te_gusta(self):
        """PASS: goes to FREE_TALK correctly."""
        assert not _reaches_memory_search("que musica te gusta")

    def test_que_es_decia(self):
        """PASS: goes to DECIA_SELF correctly."""
        r = il.classify("que es decia")
        assert r.intent == "DECIA_SELF"

    def test_que_es_deca(self):
        """PASS: goes to ARCHIVE_DIRECT correctly."""
        r = il.classify("que es deca")
        assert r.intent == "ARCHIVE_DIRECT"


# =========================================================
# EXISTING MEMORY_SEARCH — must keep working
# =========================================================

class TestExistingMemorySearch:
    """Existing MEMORY_SEARCH patterns must keep working."""

    def test_que_recuerdas(self):
        """PASS: recuerdas triggers MEMORY_SEARCH."""
        assert _reaches_memory_search("que recuerdas")

    def test_que_recuerdas_de_mi_color(self):
        """PASS: recuerdas + color filters correctly."""
        assert _reaches_memory_search("que recuerdas de mi color favorito")
        assert _memory_search_returns_relevant(
            "que recuerdas de mi color favorito", "color"
        )

    def test_que_dije(self):
        """PASS: dije triggers MEMORY_SEARCH."""
        assert _reaches_memory_search("que dije")

    def test_que_hablamos(self):
        """PASS: hablamos triggers MEMORY_SEARCH."""
        assert _reaches_memory_search("que hablamos")

    def test_recuerdas_mi_perro(self):
        """PASS: recuerdas + perro filters correctly."""
        assert _reaches_memory_search("recuerdas como se llama mi perro")
        assert _memory_search_returns_relevant(
            "recuerdas como se llama mi perro", "perro"
        )
