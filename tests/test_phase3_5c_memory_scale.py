"""
PHASE 3.5C — Memory Scale & Relevance Audit
Tests memory search with controlled datasets at various scales.
"""
import sys
import json
import shutil
import pytest
from pathlib import Path
from datetime import datetime, timedelta

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "app"))

from services.archive import (
    search_archive,
    save_memory,
    get_memories,
    ARCHIVE_PATH,
)

MEMORIES_PATH = ARCHIVE_PATH / "memories.json"
BACKUP_PATH = ARCHIVE_PATH / "memories.json.bak"


@pytest.fixture
def backup_memories():
    if MEMORIES_PATH.exists():
        shutil.copy2(MEMORIES_PATH, BACKUP_PATH)
    MEMORIES_PATH.write_text(
        json.dumps({"memories": []}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    yield
    if BACKUP_PATH.exists():
        shutil.copy2(BACKUP_PATH, MEMORIES_PATH)
        BACKUP_PATH.unlink()
    elif MEMORIES_PATH.exists():
        MEMORIES_PATH.unlink()


def create_memories(count, prefix="mem", template="memory {idx} about topic {idx}"):
    for i in range(count):
        save_memory({
            "id": f"mem_{prefix}_{i:04d}",
            "content": template.format(idx=i),
            "description": template.format(idx=i),
            "timestamp": datetime.now().isoformat(),
            "date": datetime.now().strftime("%Y-%m-%d"),
            "time": datetime.now().strftime("%H:%M:%S"),
            "type": "actividad",
        })


class TestScale10:

    def test_exact_match(self, backup_memories):
        create_memories(10, template="mi color favorito es azul numero {idx}")
        memories_data = get_memories()
        memories = memories_data.get("memories", [])
        assert len(memories) == 10

    def test_general_recall(self, backup_memories):
        create_memories(10)
        results = search_archive("que recuerdas")
        assert len(results) > 0

    def test_no_match_returns_empty(self, backup_memories):
        create_memories(10, template="tengo un perro llamado max numero {idx}")
        results = search_archive("color favorito")
        memory_results = [r for r in results if r["type"] == "memory"]
        if memory_results:
            assert memory_results[0]["data"] == []


class TestScale50:

    def test_performance(self, backup_memories):
        create_memories(50, template="actividad {idx} del proyecto")
        results = search_archive("que recuerdas")
        assert len(results) > 0

    def test_specific_query(self, backup_memories):
        create_memories(50, template="tengo una recuerda sobre el proyecto {idx}")
        results = search_archive("que recuerdas proyecto")
        memory_results = [r for r in results if r["type"] == "memory"]
        assert len(memory_results) > 0

    def test_unrelated_query(self, backup_memories):
        for i in range(25):
            save_memory({
                "id": f"mem_food_{i:03d}",
                "content": f"compre pan en la tienda numero {i}",
                "description": f"compre pan en la tienda numero {i}",
                "timestamp": datetime.now().isoformat(),
                "date": datetime.now().strftime("%Y-%m-%d"),
                "type": "actividad",
            })
        for i in range(25):
            save_memory({
                "id": f"mem_work_{i:03d}",
                "content": f"mi color favorito es azul numero {i}",
                "description": f"mi color favorito es azul numero {i}",
                "timestamp": datetime.now().isoformat(),
                "date": datetime.now().strftime("%Y-%m-%d"),
                "type": "actividad",
            })
        results = search_archive("que recuerdas color azul")
        memory_results = [r for r in results if r["type"] == "memory"]
        assert len(memory_results) > 0
        assert len(memory_results[0]["data"]) < 50


class TestScale100:

    def test_performance(self, backup_memories):
        create_memories(100, template="tarea {idx} completada")
        results = search_archive("que recuerdas")
        assert len(results) > 0

    def test_word_match_quality(self, backup_memories):
        for i in range(100):
            save_memory({
                "id": f"mem_quality_{i:04d}",
                "content": f"mi color favorito es azul {i}",
                "description": f"mi color favorito es azul {i}",
                "timestamp": datetime.now().isoformat(),
                "date": datetime.now().strftime("%Y-%m-%d"),
                "type": "actividad",
            })
        results = search_archive("que color me gusta")
        memory_results = [r for r in results if r["type"] == "memory"]
        assert len(memory_results) > 0
        assert len(memory_results[0]["data"]) <= 100


class TestScale500:

    def test_performance(self, backup_memories):
        create_memories(500, template="evento {idx} del ano")
        results = search_archive("que recuerdas")
        assert len(results) > 0


class TestScale1000:

    def test_performance(self, backup_memories):
        create_memories(1000, template="registro {idx} del sistema")
        results = search_archive("que recuerdas")
        assert len(results) > 0


class TestRelevanceQuality:

    def test_exact_relevant_memory_ranked_first(self, backup_memories):
        save_memory({
            "id": "mem_target_001",
            "content": "mi color favorito es azul",
            "description": "mi color favorito es azul",
            "timestamp": datetime.now().isoformat(),
            "date": "2026-08-27",
            "type": "actividad",
        })
        for i in range(20):
            save_memory({
                "id": f"mem_unrelated_{i:03d}",
                "content": f"compre pan en la tienda {i}",
                "description": f"compre pan en la tienda {i}",
                "timestamp": datetime.now().isoformat(),
                "date": "2026-08-27",
                "type": "actividad",
            })
        results = search_archive("que color me gusta")
        memory_results = [r for r in results if r["type"] == "memory"]
        assert len(memory_results) > 0
        first_memory = memory_results[0]["data"][0]
        assert "azul" in first_memory.get("description", "")

    def test_unrelated_memories_filtered(self, backup_memories):
        save_memory({
            "id": "mem_color_001",
            "content": "mi color favorito es azul",
            "description": "mi color favorito es azul",
            "timestamp": datetime.now().isoformat(),
            "date": "2026-08-27",
            "type": "actividad",
        })
        save_memory({
            "id": "mem_music_001",
            "content": "me gusta la musica de Kanye",
            "description": "me gusta la musica de Kanye",
            "timestamp": datetime.now().isoformat(),
            "date": "2026-08-27",
            "type": "actividad",
        })
        for i in range(10):
            save_memory({
                "id": f"mem_food_{i:03d}",
                "content": f"mi comida favorita es pizza {i}",
                "description": f"mi comida favorita es pizza {i}",
                "timestamp": datetime.now().isoformat(),
                "date": "2026-08-27",
                "type": "actividad",
            })
        results = search_archive("que color me gusta")
        memory_results = [r for r in results if r["type"] == "memory"]
        assert len(memory_results) > 0
        descriptions = [
            m.get("description", "")
            for m in memory_results[0]["data"]
        ]
        has_color = any("color" in d for d in descriptions)
        has_gusta = any("gusta" in d for d in descriptions)
        assert has_color or has_gusta

    def test_date_sorting_newest_first(self, backup_memories):
        save_memory({
            "id": "mem_old_001",
            "content": "reunion vieja recuerda",
            "description": "reunion vieja recuerda",
            "timestamp": "2026-01-01T10:00:00",
            "date": "2026-01-01",
            "type": "actividad",
        })
        save_memory({
            "id": "mem_new_001",
            "content": "reunion nueva recuerda",
            "description": "reunion nueva recuerda",
            "timestamp": "2026-08-27T10:00:00",
            "date": "2026-08-27",
            "type": "actividad",
        })
        results = search_archive("que recuerdas reunion")
        memory_results = [r for r in results if r["type"] == "memory"]
        assert len(memory_results) > 0
        dates = [m.get("date", "") for m in memory_results[0]["data"]]
        assert dates == sorted(dates, reverse=True)


class TestDuplicateMemories:

    def test_duplicate_memories_returned(self, backup_memories):
        for _ in range(5):
            save_memory({
                "id": f"mem_dup_{datetime.now().timestamp()}",
                "content": "mi color favorito es azul",
                "description": "mi color favorito es azul",
                "timestamp": datetime.now().isoformat(),
                "date": "2026-08-27",
                "type": "actividad",
            })
        results = search_archive("que color me gusta")
        memory_results = [r for r in results if r["type"] == "memory"]
        assert len(memory_results) > 0
        assert len(memory_results[0]["data"]) == 1


class TestDateQueries:

    def test_hoy_filter(self, backup_memories):
        today = datetime.now().strftime("%Y-%m-%d")
        save_memory({
            "id": "mem_today_001",
            "content": "reunion de hoy",
            "description": "reunion de hoy",
            "timestamp": datetime.now().isoformat(),
            "date": today,
            "type": "actividad",
        })
        save_memory({
            "id": "mem_old_001",
            "content": "reunion vieja",
            "description": "reunion vieja",
            "timestamp": "2026-01-01T10:00:00",
            "date": "2026-01-01",
            "type": "actividad",
        })
        results = search_archive("que recuerdo hoy")
        memory_results = [r for r in results if r["type"] == "memory"]
        assert len(memory_results) > 0
        dates = [m.get("date", "") for m in memory_results[0]["data"]]
        assert all(d == today for d in dates)

    def test_ayer_filter(self, backup_memories):
        yesterday = (
            datetime.now().astimezone() - timedelta(days=1)
        ).strftime("%Y-%m-%d")
        save_memory({
            "id": "mem_yesterday_001",
            "content": "reunion de ayer",
            "description": "reunion de ayer",
            "timestamp": datetime.now().isoformat(),
            "date": yesterday,
            "type": "actividad",
        })
        save_memory({
            "id": "mem_old_001",
            "content": "reunion vieja",
            "description": "reunion vieja",
            "timestamp": "2026-01-01T10:00:00",
            "date": "2026-01-01",
            "type": "actividad",
        })
        results = search_archive("que recuerdo ayer")
        memory_results = [r for r in results if r["type"] == "memory"]
        assert len(memory_results) > 0
        dates = [m.get("date", "") for m in memory_results[0]["data"]]
        assert all(d == yesterday for d in dates)


class TestGeneralRecall:

    def test_que_recuerdas_all_memories(self, backup_memories):
        for i in range(10):
            save_memory({
                "id": f"mem_general_{i:03d}",
                "content": f"memoria general {i}",
                "description": f"memoria general {i}",
                "timestamp": datetime.now().isoformat(),
                "date": datetime.now().strftime("%Y-%m-%d"),
                "type": "actividad",
            })
        results = search_archive("que recuerdas")
        memory_results = [r for r in results if r["type"] == "memory"]
        assert len(memory_results) > 0
        assert len(memory_results[0]["data"]) == 10

    def test_result_limit_capped_at_20(
        self, backup_memories
    ):
        for i in range(50):
            save_memory({
                "id": f"mem_limit_{i:03d}",
                "content": f"memoria limite {i}",
                "description": f"memoria limite {i}",
                "timestamp": datetime.now().isoformat(),
                "date": datetime.now().strftime("%Y-%m-%d"),
                "type": "actividad",
            })
        results = search_archive("que recuerdas")
        memory_results = [
            r for r in results if r["type"] == "memory"
        ]
        assert len(memory_results) > 0
        assert len(memory_results[0]["data"]) <= 20

    def test_result_limit_at_1000(
        self, backup_memories
    ):
        for i in range(100):
            save_memory({
                "id": f"mem_1k_{i:03d}",
                "content": f"memoria 1k {i}",
                "description": f"memoria 1k {i}",
                "timestamp": datetime.now().isoformat(),
                "date": datetime.now().strftime("%Y-%m-%d"),
                "type": "actividad",
            })
        results = search_archive("que recuerdas")
        memory_results = [
            r for r in results if r["type"] == "memory"
        ]
        assert len(memory_results) > 0
        assert len(memory_results[0]["data"]) <= 20

    def test_under_limit_returns_all(
        self, backup_memories
    ):
        for i in range(5):
            save_memory({
                "id": f"mem_under_{i:03d}",
                "content": f"memoria under {i}",
                "description": f"memoria under {i}",
                "timestamp": datetime.now().isoformat(),
                "date": datetime.now().strftime("%Y-%m-%d"),
                "type": "actividad",
            })
        results = search_archive("que recuerdas")
        memory_results = [
            r for r in results if r["type"] == "memory"
        ]
        assert len(memory_results) > 0
        assert len(memory_results[0]["data"]) == 5

    def test_empty_memories_returns_empty(self, backup_memories):
        results = search_archive("que recuerdas")
        memory_results = [r for r in results if r["type"] == "memory"]
        if memory_results:
            assert memory_results[0]["data"] == []


class TestMemoryRelevanceScoring:

    COMPETING = [
        {
            "id": "mem_color_001",
            "content": "mi color favorito es azul",
            "description": "mi color favorito es azul",
            "timestamp": datetime.now().isoformat(),
            "date": "2026-08-20",
            "time": "10:00:00",
            "type": "actividad",
        },
        {
            "id": "mem_music_001",
            "content": "me gusta la musica de Kanye",
            "description": "me gusta la musica de Kanye",
            "timestamp": datetime.now().isoformat(),
            "date": "2026-08-21",
            "time": "11:00:00",
            "type": "actividad",
        },
        {
            "id": "mem_project_001",
            "content": "quiero terminar DECIA",
            "description": "quiero terminar DECIA",
            "timestamp": datetime.now().isoformat(),
            "date": "2026-08-22",
            "time": "12:00:00",
            "type": "actividad",
        },
        {
            "id": "mem_pet_001",
            "content": "mi perro se llama Max",
            "description": "mi perro se llama Max",
            "timestamp": datetime.now().isoformat(),
            "date": "2026-08-23",
            "time": "13:00:00",
            "type": "actividad",
        },
    ]

    def _setup_memories(self, backup_memories):
        for m in self.COMPETING:
            save_memory(m)

    def test_color_query_ranks_color_first(
        self, backup_memories
    ):
        self._setup_memories(backup_memories)
        results = search_archive("que color me gusta")
        mr = [r for r in results if r["type"] == "memory"]
        assert len(mr) > 0
        assert mr[0]["data"][0]["id"] == "mem_color_001"

    def test_music_query_ranks_music_first(
        self, backup_memories
    ):
        self._setup_memories(backup_memories)
        results = search_archive("que musica me gusta")
        mr = [r for r in results if r["type"] == "memory"]
        assert len(mr) > 0
        assert mr[0]["data"][0]["id"] == "mem_music_001"

    def test_project_query_ranks_project_first(
        self, backup_memories
    ):
        self._setup_memories(backup_memories)
        results = search_archive(
            "que proyecto quiero terminar"
        )
        mr = [r for r in results if r["type"] == "memory"]
        assert len(mr) > 0
        assert mr[0]["data"][0]["id"] == "mem_project_001"

    def test_pet_query_ranks_pet_first(
        self, backup_memories
    ):
        self._setup_memories(backup_memories)
        results = search_archive("como se llama mi perro")
        mr = [r for r in results if r["type"] == "memory"]
        assert len(mr) > 0
        assert mr[0]["data"][0]["id"] == "mem_pet_001"

    def test_color_favorito_query(
        self, backup_memories
    ):
        self._setup_memories(backup_memories)
        results = search_archive(
            "cual es mi color favorito"
        )
        mr = [r for r in results if r["type"] == "memory"]
        assert len(mr) > 0
        assert mr[0]["data"][0]["id"] == "mem_color_001"

    def test_generic_verb_lower_weight(
        self, backup_memories
    ):
        self._setup_memories(backup_memories)
        results = search_archive("que color me gusta")
        mr = [r for r in results if r["type"] == "memory"]
        top = mr[0]["data"][0]
        assert top["id"] == "mem_color_001"
