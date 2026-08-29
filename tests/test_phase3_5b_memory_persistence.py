"""
PHASE 3.5B — Memory Persistence Audit
Tests memory save/load under edge cases.
"""
import sys
import json
import os
import shutil
import pytest
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "app"))

from services.archive import (
    load_archive,
    get_memories,
    save_memory,
    ARCHIVE_PATH,
)
from brain.handlers import create_memory, memory_request

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


class TestLoadArchiveEdgeCases:

    def test_valid_json(self, tmp_path):
        f = tmp_path / "test.json"
        f.write_text('{"key": "value"}', encoding="utf-8")
        result = json.loads(f.read_text(encoding="utf-8"))
        assert result == {"key": "value"}

    def test_empty_file(self, tmp_path):
        f = tmp_path / "empty.json"
        f.write_text("", encoding="utf-8")
        try:
            json.loads(f.read_text(encoding="utf-8"))
            assert False, "Should have raised"
        except json.JSONDecodeError:
            pass

    def test_malformed_json(self, tmp_path):
        f = tmp_path / "bad.json"
        f.write_text("{invalid json", encoding="utf-8")
        try:
            json.loads(f.read_text(encoding="utf-8"))
            assert False, "Should have raised"
        except json.JSONDecodeError:
            pass

    def test_missing_file(self):
        result = load_archive("nonexistent_file_xyz.json")
        assert result == {}

    def test_array_instead_of_object(self, tmp_path):
        f = tmp_path / "arr.json"
        f.write_text('[1, 2, 3]', encoding="utf-8")
        result = json.loads(f.read_text(encoding="utf-8"))
        assert result == [1, 2, 3]

    def test_nested_json(self, tmp_path):
        f = tmp_path / "nested.json"
        f.write_text('{"a": {"b": {"c": 1}}}', encoding="utf-8")
        result = json.loads(f.read_text(encoding="utf-8"))
        assert result["a"]["b"]["c"] == 1


class TestGetMemories:

    def test_valid_memories(self, tmp_path):
        data = {"memories": [{"id": "m1", "content": "test"}]}
        path = tmp_path / "memories.json"
        path.write_text(json.dumps(data), encoding="utf-8")
        result = json.loads(path.read_text(encoding="utf-8"))
        assert len(result["memories"]) == 1

    def test_empty_memories_list(self, tmp_path):
        data = {"memories": []}
        path = tmp_path / "memories.json"
        path.write_text(json.dumps(data), encoding="utf-8")
        result = json.loads(path.read_text(encoding="utf-8"))
        assert result["memories"] == []

    def test_missing_memories_key(self, tmp_path):
        data = {"other": "data"}
        path = tmp_path / "memories.json"
        path.write_text(json.dumps(data), encoding="utf-8")
        result = json.loads(path.read_text(encoding="utf-8"))
        assert "memories" not in result


class TestSaveMemory:

    def test_save_and_retrieve(self, backup_memories):
        memory = {
            "id": "mem_test_001",
            "content": "test memory persistence",
            "timestamp": datetime.now().isoformat(),
            "type": "actividad",
        }
        result = save_memory(memory)
        assert result is True

        loaded = get_memories()
        assert "memories" in loaded
        found = any(
            m["id"] == "mem_test_001"
            for m in loaded["memories"]
        )
        assert found

    def test_multiple_saves(self, backup_memories):
        for i in range(3):
            memory = {
                "id": f"mem_multi_{i}",
                "content": f"memory {i}",
                "timestamp": datetime.now().isoformat(),
                "type": "actividad",
            }
            assert save_memory(memory) is True

        loaded = get_memories()
        count = sum(
            1 for m in loaded["memories"]
            if m["id"].startswith("mem_multi_")
        )
        assert count == 3

    def test_save_with_special_characters(self, backup_memories):
        memory = {
            "id": "mem_special_001",
            "content": "特殊字符测试 ñáéíóú @#$%",
            "timestamp": datetime.now().isoformat(),
            "type": "actividad",
        }
        assert save_memory(memory) is True
        loaded = get_memories()
        found = any(
            m["id"] == "mem_special_001"
            for m in loaded["memories"]
        )
        assert found

    def test_save_empty_content(self, backup_memories):
        memory = {
            "id": "mem_empty_001",
            "content": "",
            "timestamp": datetime.now().isoformat(),
            "type": "actividad",
        }
        assert save_memory(memory) is True

    def test_save_very_long_content(self, backup_memories):
        long_content = "a" * 10000
        memory = {
            "id": "mem_long_001",
            "content": long_content,
            "timestamp": datetime.now().isoformat(),
            "type": "actividad",
        }
        assert save_memory(memory) is True
        loaded = get_memories()
        found = next(
            m for m in loaded["memories"]
            if m["id"] == "mem_long_001"
        )
        assert len(found["content"]) == 10000

    def test_save_unicode_emoji(self, backup_memories):
        memory = {
            "id": "mem_emoji_001",
            "content": "me gusta el café ☕",
            "timestamp": datetime.now().isoformat(),
            "type": "actividad",
        }
        assert save_memory(memory) is True
        loaded = get_memories()
        found = next(
            m for m in loaded["memories"]
            if m["id"] == "mem_emoji_001"
        )
        assert "☕" in found["content"]

    def test_save_returns_true_on_success(self, backup_memories):
        memory = {
            "id": "mem_true_001",
            "content": "test",
            "timestamp": datetime.now().isoformat(),
            "type": "actividad",
        }
        assert save_memory(memory) is True

    def test_create_memory_saved_field(self, backup_memories):
        result = create_memory("test saved field")
        assert "saved" in result
        assert result["saved"] is True

    def test_create_memory_duplicate_field(
        self, backup_memories
    ):
        create_memory("test duplicate detection")
        result = create_memory(
            "test duplicate detection"
        )
        assert result["duplicate"] is True
        assert result["saved"] is False

    def test_duplicate_normalized_returns_duplicate(
        self, backup_memories
    ):
        save_memory({
            "id": "mem_norm_1",
            "description": "mi color favorito es azul",
            "date": "2026-08-27",
            "type": "actividad",
        })
        result = save_memory({
            "id": "mem_norm_2",
            "description": "MI COLOR FAVORITO ES AZUL",
            "date": "2026-08-27",
            "type": "actividad",
        })
        assert result == "duplicate"

    def test_same_desc_different_date_kept(
        self, backup_memories
    ):
        r1 = save_memory({
            "id": "mem_date_1",
            "description": "quiero terminar DECIA",
            "date": "2026-08-26",
            "type": "actividad",
        })
        r2 = save_memory({
            "id": "mem_date_2",
            "description": "quiero terminar DECIA",
            "date": "2026-08-27",
            "type": "actividad",
        })
        assert r1 is True
        assert r2 is True
        loaded = get_memories()
        matches = [
            m for m in loaded["memories"]
            if m.get("description") == "quiero terminar DECIA"
        ]
        assert len(matches) == 2

    def test_same_desc_same_date_duplicate(
        self, backup_memories
    ):
        r1 = save_memory({
            "id": "mem_samedate_1",
            "description": "quiero terminar DECIA",
            "date": "2026-08-27",
            "type": "actividad",
        })
        r2 = save_memory({
            "id": "mem_samedate_2",
            "description": "quiero terminar DECIA",
            "date": "2026-08-27",
            "type": "actividad",
        })
        assert r1 is True
        assert r2 == "duplicate"
        loaded = get_memories()
        matches = [
            m for m in loaded["memories"]
            if m.get("description") == "quiero terminar DECIA"
        ]
        assert len(matches) == 1

    def test_different_content_not_duplicate(
        self, backup_memories
    ):
        save_memory({
            "id": "mem_diff_1",
            "description": "mi color favorito es azul",
            "date": "2026-08-27",
            "type": "actividad",
        })
        result = save_memory({
            "id": "mem_diff_2",
            "description": "me gusta la musica",
            "date": "2026-08-27",
            "type": "actividad",
        })
        assert result is True

    def test_empty_description_not_duplicate(
        self, backup_memories
    ):
        r1 = save_memory({
            "id": "mem_empty_1",
            "content": "memory alpha",
            "date": "2026-08-27",
            "type": "actividad",
        })
        r2 = save_memory({
            "id": "mem_empty_2",
            "content": "memory beta",
            "date": "2026-08-27",
            "type": "actividad",
        })
        assert r1 is True
        assert r2 is True


class TestCreateMemory:

    def test_creates_valid_structure(self, backup_memories):
        result = create_memory("mi color favorito es azul")
        assert "id" in result
        assert "timestamp" in result
        assert "description" in result
        assert result["description"] == "mi color favorito es azul"

    def test_always_returns_memory(self, backup_memories):
        result = create_memory("test content")
        assert result is not None
        assert isinstance(result, dict)

    def test_id_format(self, backup_memories):
        result = create_memory("test id format")
        assert result["id"].startswith("mem_")


class TestDuplicateMemory:

    def test_duplicate_content_allowed(self, backup_memories):
        mem1 = create_memory("mi color favorito es azul")
        mem2 = create_memory("quiero un cafe")
        loaded = get_memories()
        count = sum(
            1 for m in loaded["memories"]
            if m.get("description") in (
                "mi color favorito es azul",
                "quiero un cafe",
            )
        )
        assert count == 2

    def test_same_second_id_collision(self, backup_memories):
        mem1 = create_memory("test collision 1")
        mem2 = create_memory("test collision 2")
        assert mem1["id"] != mem2["id"]

    def test_id_has_microseconds(self, backup_memories):
        result = create_memory("test id microseconds")
        assert result["id"].startswith("mem_")
        assert len(result["id"].split("_")) == 4


class TestMemoryRequest:

    def test_guarda_que(self):
        result = memory_request("guarda que mi color favorito es azul")
        assert result == "mi color favorito es azul"

    def test_recuerda_que(self):
        result = memory_request("recuerda que tengo clase manana")
        assert result == "tengo clase manana"

    def test_anota_que(self):
        result = memory_request("anota que es lunes")
        assert result == "es lunes"

    def test_empty_content(self):
        result = memory_request("guarda que")
        assert result is None

    def test_no_trigger(self):
        result = memory_request("hola como estas")
        assert result is None

    def test_decia_prefix(self):
        result = memory_request("decia guarda que tengo reunion")
        assert result == "tengo reunion"


class TestCorruptedMemoryRecovery:

    def test_corrupted_json_creates_backup(
        self, backup_memories
    ):
        from services.archive import (
            backup_corrupted_memories,
        )

        original = MEMORIES_PATH.read_text(
            encoding="utf-8"
        )

        MEMORIES_PATH.write_text(
            "{invalid json", encoding="utf-8"
        )

        result = backup_corrupted_memories()
        assert result is True

        backup = ARCHIVE_PATH / (
            "memories.corrupt.backup.json"
        )
        assert backup.exists()
        content = backup.read_text(encoding="utf-8")
        assert "invalid json" in content

        MEMORIES_PATH.write_text(
            original, encoding="utf-8"
        )
        backup.unlink(missing_ok=True)

    def test_corrupted_memories_returns_empty(
        self, backup_memories
    ):
        MEMORIES_PATH.write_text(
            "NOT JSON AT ALL", encoding="utf-8"
        )

        result = get_memories()
        assert result == {}

    def test_empty_file_returns_empty(
        self, backup_memories
    ):
        MEMORIES_PATH.write_text(
            "", encoding="utf-8"
        )

        result = get_memories()
        assert result == {}

    def test_array_root_returns_empty(
        self, backup_memories
    ):
        MEMORIES_PATH.write_text(
            json.dumps([1, 2, 3]), encoding="utf-8"
        )

        result = get_memories()
        assert result == {}
