# tests/services/test_memory.py
# Contract assertions for MemoryPlugin: CRUD, dedup, canonical forms

import sys
from pathlib import Path

# Add app directory to path
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "app"))

from app.services.plugins.memory import MemoryPlugin


def test_memory_crud():
    """MemoryPlugin must support create/read/update/delete."""
    plugin = MemoryPlugin()
    # Create
    plugin.execute({"action": "create", "key": "fact_1", "data": {"content": "User likes coffee"}})
    # Read - canonical form lowercases
    result = plugin.execute({"action": "read", "key": "fact_1"})
    assert result["content"] == "user likes coffee"
    # Update
    plugin.execute({"action": "update", "key": "fact_1", "data": {"content": "User loves coffee"}})
    result = plugin.execute({"action": "read", "key": "fact_1"})
    assert result["content"] == "user loves coffee"
    # Delete
    plugin.execute({"action": "delete", "key": "fact_1"})
    result = plugin.execute({"action": "read", "key": "fact_1"})
    assert result == {}


def test_memory_dedup_exact():
    """MemoryPlugin must deduplicate exact duplicate content."""
    plugin = MemoryPlugin()
    plugin.execute({"action": "create", "key": "a", "data": {"content": "same"}})
    plugin.execute({"action": "create", "key": "b", "data": {"content": "same"}})
    all_memories = plugin.execute({"action": "list"})
    # Should only have one entry for "same"
    contents = [m["content"] for m in all_memories.values()]
    assert contents.count("same") == 1


def test_memory_canonical_form():
    """MemoryPlugin must normalize to canonical form (lowercase, trimmed)."""
    plugin = MemoryPlugin()
    plugin.execute({"action": "create", "key": "k1", "data": {"content": "  Hello World  "}})
    result = plugin.execute({"action": "read", "key": "k1"})
    assert result["content"] == "hello world"


def test_memory_search():
    """MemoryPlugin.search must find by content substring."""
    plugin = MemoryPlugin()
    plugin.execute({"action": "create", "key": "k1", "data": {"content": "user likes pizza"}})
    plugin.execute({"action": "create", "key": "k2", "data": {"content": "user hates broccoli"}})
    results = plugin.execute({"action": "search", "query": "pizza"})
    assert len(results) == 1
    # results is a dict key->entry
    entry = next(iter(results.values()))
    assert "pizza" in entry["content"]


def test_memory_tags():
    """MemoryPlugin must support tagging and tag-based queries."""
    plugin = MemoryPlugin()
    plugin.execute({"action": "create", "key": "k1", "data": {"content": "fact", "tags": ["personal"]}})
    plugin.execute({"action": "create", "key": "k2", "data": {"content": "fact", "tags": ["work"]}})
    results = plugin.execute({"action": "query_by_tag", "tag": "personal"})
    assert len(results) == 1
    # results is a dict key->entry
    entry = next(iter(results.values()))
    assert "personal" in entry.get("tags", [])