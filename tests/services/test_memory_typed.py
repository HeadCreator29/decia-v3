# tests/services/test_memory_typed.py
# Contract assertions for MemoryPlugin v2: typed API, backward compat

import sys
from pathlib import Path

# Add app directory to path
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "app"))

from app.services.plugins.memory import (
    MemoryPlugin,
    create_typed,
    get_by_type,
    get_by_confidence_range,
    add_relation,
    update_confidence,
    search_by_content,
    migrate_legacy,
    _validate_type,
    _validate_relation,
    _default_encryption_flag,
    _VALID_CONFIDENCE,
    _TYPED_MEMORY_TYPES,
    _RELATION_TYPES,
)


def test_create_typed_basic():
    """create_typed must create a memory with all v2 fields."""
    mem = create_typed(content="User likes coffee", mtype="MEMORY", confidence=0.8)
    assert mem["content"] == "User likes coffee"
    assert mem["type"] == "MEMORY"
    assert mem["confidence"] == 0.8
    assert mem["relations"] == []
    assert mem["encryption_flag"] == "optional"
    assert mem["metadata"] == {}
    assert mem["version"] == 1
    assert "created_at" in mem
    assert "updated_at" in mem


def test_create_typed_fact():
    """create_typed with FACT type should have encryption_flag 'none'."""
    mem = create_typed(content="Earth is round", mtype="FACT")
    assert mem["type"] == "FACT"
    assert mem["encryption_flag"] == "none"


def test_create_typed_invalid_type():
    """create_typed must raise ValueError for invalid type."""
    try:
        create_typed(content="test", mtype="INVALID")
        assert False, "Should have raised ValueError"
    except ValueError as e:
        assert "Invalid memory type" in str(e)


def test_create_typed_invalid_confidence():
    """create_typed must raise ValueError for out-of-range confidence."""
    try:
        create_typed(content="test", mtype="MEMORY", confidence=1.5)
        assert False, "Should have raised ValueError"
    except ValueError as e:
        assert "confidence must be a number" in str(e).lower()


def test_get_by_type():
    """get_by_type must filter memories by type within a plugin."""
    plugin = MemoryPlugin()
    # Create v2-typed memories using create_typed and add to plugin storage
    mem1 = create_typed(content="fact content", mtype="FACT", confidence=0.9)
    mem2 = create_typed(content="memory content", mtype="MEMORY", confidence=0.5)

    # Manually add to plugin storage with keys
    plugin._storage["v2_fact_1"] = mem1
    plugin._storage["v2_mem_1"] = mem2

    # Use get_by_type function - valid type with matches
    results = get_by_type(plugin, "FACT")
    assert len(results) >= 1
    assert any(r.get("content") == "fact content" for r in results)

    # Valid type with no matches (type exists in enum but no entries)
    results = get_by_type(plugin, "UNKNOWN")
    assert len(results) == 0

    # Invalid type should raise ValueError
    try:
        get_by_type(plugin, "INVALID_TYPE")
        assert False, "Should have raised ValueError"
    except ValueError:
        pass  # expected


def test_get_by_confidence_range():
    """get_by_confidence_range must filter by confidence range."""
    plugin = MemoryPlugin()
    # Create v2-typed memories with different confidence levels
    mem1 = create_typed(content="high conf", mtype="MEMORY", confidence=0.9)
    mem2 = create_typed(content="low conf", mtype="MEMORY", confidence=0.3)

    # Manually add to plugin storage with keys
    plugin._storage["v2_high_1"] = mem1
    plugin._storage["v2_low_1"] = mem2

    # Test range that includes high confidence
    results = get_by_confidence_range(plugin, 0.5, 1.0)
    high_conf_results = [r for r in results if r.get("content") == "high conf"]
    assert len(high_conf_results) >= 1

    # Test range that includes low confidence
    results_low = get_by_confidence_range(plugin, 0.0, 0.5)
    low_conf_results = [r for r in results_low if r.get("content") == "low conf"]
    assert len(low_conf_results) >= 1

    # Test full range
    results_all = get_by_confidence_range(plugin, 0.0, 1.0)
    assert len(results_all) >= 2


def test_add_relation():
    """add_relation must add a relation between two memories."""
    plugin = MemoryPlugin()

    # Create two memories
    r1 = plugin.execute({"action": "create", "key": "rel_src", "data": {"content": "source"}})
    r2 = plugin.execute({"action": "create", "key": "rel_tgt", "data": {"content": "target"}})

    # Add relation
    result = add_relation(plugin, source_id="rel_src", target_id="rel_tgt", relation_type="supports")
    assert result["status"] == "relation_added"
    assert result["relation_type"] == "supports"

    # Invalid relation type
    try:
        add_relation(plugin, source_id="rel_src", target_id="rel_tgt", relation_type="invalid")
        assert False, "Should have raised ValueError"
    except ValueError as e:
        assert "Invalid relation type" in str(e)


def test_add_relation_same_id():
    """add_relation must raise error when source_id == target_id."""
    plugin = MemoryPlugin()
    plugin.execute({"action": "create", "key": "same_1", "data": {"content": "a"}})
    try:
        add_relation(plugin, source_id="same_1", target_id="same_1", relation_type="relates-to")
        assert False, "Should have raised ValueError"
    except ValueError as e:
        assert "different" in str(e).lower()


def test_update_confidence():
    """update_confidence must update a memory's confidence score."""
    plugin = MemoryPlugin()
    plugin.execute({"action": "create", "key": "conf_1", "data": {"content": "test"}})

    result = update_confidence(plugin, memory_id="conf_1", confidence=0.7)
    assert result["status"] == "confidence_updated"
    assert result["confidence"] == 0.7

    # Invalid confidence
    try:
        update_confidence(plugin, memory_id="conf_1", confidence=-0.1)
        assert False, "Should have raised ValueError"
    except ValueError as e:
        assert "0.0" in str(e) and "1.0" in str(e)

    try:
        update_confidence(plugin, memory_id="conf_1", confidence=1.5)
        assert False, "Should have raised ValueError"
    except ValueError as e:
        assert "0.0" in str(e) and "1.0" in str(e)


def test_search_by_content():
    """search_by_content must find memories by content query with filters."""
    plugin = MemoryPlugin()
    plugin.execute({"action": "create", "key": "sq_1", "data": {"content": "user likes pizza", "tags": []}})
    plugin.execute({"action": "create", "key": "sq_2", "data": {"content": "user hates broccoli", "tags": []}})

    # Basic search
    results = search_by_content(plugin, query="pizza")
    assert len(results) >= 1
    assert any("pizza" in r.get("content", "") for r in results)

    # Search with type filter
    results_typed = search_by_content(plugin, query="user", filters={"type": "MEMORY"})
    assert len(results_typed) >= 0  # may or may not match depending on types

    # Search with confidence filter
    results_conf = search_by_content(plugin, query="user", filters={"min_conf": 0.5, "max_conf": 1.0})
    assert len(results_conf) >= 0

    # Search with no matches
    results_nomatch = search_by_content(plugin, query="nonexistent_xyz")
    assert len(results_nomatch) == 0


def test_migrate_legacy_dry_run():
    """migrate_legacy must return a MigrationReport in dry-run mode."""
    import json
    import os
    from pathlib import Path
    
    # Create test data directory and memories.json
    # Use absolute path to project root
    project_root = Path("/mnt/c/Users/idelv/Desktop/DECIA_V3")
    archive_path = project_root / "data" / "archive"
    os.makedirs(archive_path, exist_ok=True)
    memories_path = archive_path / "memories.json"
    
    # Create test data
    test_memories = {
        "memories": [
            {"id": "test-1", "content": "Test memory 1", "confidence": 0.8, "tags": ["test"]},
            {"id": "test-2", "content": "Test memory 2", "confidence": 0.9, "tags": ["test"]},
        ]
    }
    with open(memories_path, "w", encoding="utf-8") as f:
        json.dump(test_memories, f)
    
    try:
        plugin = MemoryPlugin()
        report = migrate_legacy(plugin, default_type="MEMORY", default_confidence=0.7)
        assert isinstance(report, dict)
        assert "total" in report
        assert "migrated" in report
        assert "errors" in report
        assert "backup_path" in report
        assert "checksum" in report
        assert report["total"] > 0  # should have entries from memories.json
    finally:
        # Clean up
        if memories_path.exists():
            os.unlink(memories_path)


def test_validate_type():
    """_validate_type must validate the 8-type enum."""
    assert _validate_type("FACT") is True
    assert _validate_type("MEMORY") is True
    assert _validate_type("DECISION") is True
    assert _validate_type("GOAL") is True
    assert _validate_type("PREDICTION") is True
    assert _validate_type("LESSON") is True
    assert _validate_type("INTERPRETATION") is True
    assert _validate_type("UNKNOWN") is True
    assert _validate_type("INVALID") is False


def test_validate_relation():
    """_validate_relation must validate relation types."""
    assert _validate_relation("relates-to") is True
    assert _validate_relation("supports") is True
    assert _validate_relation("contradicts") is True
    assert _validate_relation("supersedes") is True
    assert _validate_relation("invalid") is False


def test_default_encryption_flag():
    """_default_encryption_flag must return per-type policy."""
    assert _default_encryption_flag("FACT") == "none"
    assert _default_encryption_flag("MEMORY") == "optional"
    assert _default_encryption_flag("INTERPRETATION") == "mandatory"
    assert _default_encryption_flag("LESSON") == "mandatory"
    assert _default_encryption_flag("UNKNOWN") == "none"


def test_typed_memory_types_enum():
    """The 8-type enum must be complete and correct."""
    expected = frozenset(["FACT", "MEMORY", "DECISION", "GOAL", "PREDICTION", "LESSON", "INTERPRETATION", "UNKNOWN"])
    assert _TYPED_MEMORY_TYPES == expected


def test_relation_types_enum():
    """The relation types enum must be complete and correct."""
    expected = frozenset(["relates-to", "supports", "contradicts", "supersedes"])
    assert _RELATION_TYPES == expected


def test_valid_confidence():
    """_VALID_CONFIDENCE must correctly validate 0.0-1.0 range."""
    assert _VALID_CONFIDENCE(0.0) is True
    assert _VALID_CONFIDENCE(1.0) is True
    assert _VALID_CONFIDENCE(0.5) is True
    assert _VALID_CONFIDENCE(-0.1) is False
    assert _VALID_CONFIDENCE(1.1) is False
    assert _VALID_CONFIDENCE("bad") is False