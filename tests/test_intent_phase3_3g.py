import sys, os, json
sys.path.insert(0, r"C:\Users\idelv\Desktop\DECIA_v2\app")
os.chdir(r"C:\Users\idelv\Desktop\DECIA_v2\app")

import pytest
from services.archive import search_archive, get_memories, save_memory, ARCHIVE_PATH


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


class TestSpecificRecall:
    """Specific queries with memory_words should prioritize relevant memories."""

    def test_color_favorito(self):
        results = search_archive("que recuerdas de mi color favorito")
        memory_results = [r for r in results if r["type"] == "memory"]
        assert len(memory_results) > 0
        all_descs = " ".join(
            m["description"] for r in memory_results for m in r["data"]
        )
        assert "color" in all_descs

    def test_perro_with_recuerdas(self):
        results = search_archive("recuerdas como se llama mi perro")
        memory_results = [r for r in results if r["type"] == "memory"]
        assert len(memory_results) > 0
        all_descs = " ".join(
            m["description"] for r in memory_results for m in r["data"]
        )
        assert "perro" in all_descs or "max" in all_descs.lower()

    def test_musica_with_recuerdas(self):
        results = search_archive("recuerdas que música me gusta")
        memory_results = [r for r in results if r["type"] == "memory"]
        assert len(memory_results) > 0
        all_descs = " ".join(
            m["description"] for r in memory_results for m in r["data"]
        )
        assert "música" in all_descs or "kanye" in all_descs.lower()

    def test_proyecto_with_recuerdas(self):
        results = search_archive("recuerdas que proyecto quiero terminar")
        memory_results = [r for r in results if r["type"] == "memory"]
        assert len(memory_results) > 0
        all_descs = " ".join(
            m["description"] for r in memory_results for m in r["data"]
        )
        assert "decia" in all_descs.lower()


class TestGeneralRecall:
    """General queries should return all memories."""

    def test_que_recuerdas(self):
        results = search_archive("que recuerdas")
        memory_results = [r for r in results if r["type"] == "memory"]
        assert len(memory_results) > 0
        assert len(memory_results[0]["data"]) >= 5


class TestMemoryCreateStillWorks:
    """MEMORY_CREATE patterns must not be affected."""

    def test_guarda_que(self):
        from brain.handlers import memory_request
        result = memory_request("guarda que mi color favorito es rojo")
        assert result is not None
        assert "color favorito es rojo" in result

    def test_recuerda_que(self):
        from brain.handlers import memory_request
        result = memory_request("recuerda que mañana tengo reunion")
        assert result is not None
        assert "reunion" in result
