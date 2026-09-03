# tests/services/test_search.py - SearchPlugin Tests
# Golden master: all 546 existing tests must pass unchanged

import os
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "app"))

from app.services.plugins.search import SearchPlugin


def _make_test_plugin():
    """Create a SearchPlugin with a temporary database for test isolation."""
    tmp = tempfile.NamedTemporaryFile(mode='w', suffix='.db', delete=False)
    tmp.close()
    return SearchPlugin(db_path=tmp.name), tmp.name


def _cleanup_test_file(path):
    """Clean up temporary test file."""
    try:
        os.unlink(path)
    except Exception:
        pass


def test_search_plugin_creation():
    """SearchPlugin must initialize with default DB path."""
    plugin, tmp_path = _make_test_plugin()
    try:
        assert plugin.name == "SEARCH"
        assert plugin.category == "ARCHIVE"
    finally:
        plugin.close()
        _cleanup_test_file(tmp_path)


def test_search_plugin_custom_db_path():
    """SearchPlugin must accept custom DB path."""
    tmp = tempfile.NamedTemporaryFile(mode='w', suffix='.db', delete=False)
    tmp.close()
    try:
        plugin = SearchPlugin(db_path=tmp.name)
        assert plugin.db_path == tmp.name
    finally:
        plugin.close()
        os.unlink(tmp.name)


def test_search_basic_query():
    """Test basic FTS5 search."""
    plugin, tmp_path = _make_test_plugin()
    try:
        # Insert test data directly
        conn = plugin._get_connection()
        conn.execute("""
            INSERT INTO memories (id, type, content, date, confidence, source)
            VALUES (?, ?, ?, ?, ?, ?)
        """, ("test-1", "FACT", "DECIA is an AI assistant", "2026-01-01T00:00:00", 0.9, "system"))
        conn.execute("""
            INSERT INTO memories (id, type, content, date, confidence, source)
            VALUES (?, ?, ?, ?, ?, ?)
        """, ("test-2", "MEMORY", "User likes coffee", "2026-01-02T00:00:00", 0.8, "user"))
        conn.commit()
        
        # Search for "DECIA"
        result = plugin.query("DECIA")
        assert result["total"] == 1
        assert result["results"][0]["id"] == "test-1"
        assert "DECIA" in result["results"][0]["content"]
    finally:
        plugin.close()
        _cleanup_test_file(tmp_path)


def test_search_filter_by_type():
    """Test filtering by memory type."""
    plugin, tmp_path = _make_test_plugin()
    try:
        conn = plugin._get_connection()
        conn.execute("""
            INSERT INTO memories (id, type, content, date, confidence, source)
            VALUES (?, ?, ?, ?, ?, ?)
        """, ("fact-1", "FACT", "DECIA fact", "2026-01-01T00:00:00", 0.9, "system"))
        conn.execute("""
            INSERT INTO memories (id, type, content, date, confidence, source)
            VALUES (?, ?, ?, ?, ?, ?)
        """, ("mem-1", "MEMORY", "user memory", "2026-01-02T00:00:00", 0.8, "user"))
        conn.commit()
        
        # Filter by FACT type
        result = plugin.filter_by_type("FACT")
        assert result["total"] == 1
        assert result["results"][0]["type"] == "FACT"
        
        # Filter by MEMORY type
        result = plugin.filter_by_type("MEMORY")
        assert result["total"] == 1
        assert result["results"][0]["type"] == "MEMORY"
    finally:
        plugin.close()
        _cleanup_test_file(tmp_path)


def test_search_filter_by_date_range():
    """Test filtering by date range."""
    plugin, tmp_path = _make_test_plugin()
    try:
        conn = plugin._get_connection()
        conn.execute("""
            INSERT INTO memories (id, type, content, date, confidence, source)
            VALUES (?, ?, ?, ?, ?, ?)
        """, ("old-1", "FACT", "old fact", "2025-01-01T00:00:00", 0.9, "system"))
        conn.execute("""
            INSERT INTO memories (id, type, content, date, confidence, source)
            VALUES (?, ?, ?, ?, ?, ?)
        """, ("new-1", "FACT", "new fact", "2026-06-01T00:00:00", 0.9, "system"))
        conn.commit()
        
        # Filter for 2026 only
        result = plugin.filter_by_date_range("2026-01-01T00:00:00", "2026-12-31T23:59:59")
        assert result["total"] == 1
        assert result["results"][0]["id"] == "new-1"
    finally:
        plugin.close()
        _cleanup_test_file(tmp_path)


def test_search_filter_by_confidence():
    """Test filtering by confidence range."""
    plugin, tmp_path = _make_test_plugin()
    try:
        conn = plugin._get_connection()
        conn.execute("""
            INSERT INTO memories (id, type, content, date, confidence, source)
            VALUES (?, ?, ?, ?, ?, ?)
        """, ("low-1", "FACT", "low confidence", "2026-01-01T00:00:00", 0.3, "system"))
        conn.execute("""
            INSERT INTO memories (id, type, content, date, confidence, source)
            VALUES (?, ?, ?, ?, ?, ?)
        """, ("high-1", "FACT", "high confidence", "2026-01-02T00:00:00", 0.9, "system"))
        conn.commit()
        
        # Filter for high confidence only
        result = plugin.filter_by_confidence(0.7, 1.0)
        assert result["total"] == 1
        assert result["results"][0]["id"] == "high-1"
    finally:
        plugin.close()
        _cleanup_test_file(tmp_path)


def test_search_get_by_id():
    """Test getting item by ID."""
    plugin, tmp_path = _make_test_plugin()
    try:
        conn = plugin._get_connection()
        conn.execute("""
            INSERT INTO memories (id, type, content, date, confidence, source)
            VALUES (?, ?, ?, ?, ?, ?)
        """, ("test-id-123", "FACT", "test content", "2026-01-01T00:00:00", 0.9, "system"))
        conn.commit()
        
        item = plugin.get_by_id("test-id-123")
        assert item is not None
        assert item["id"] == "test-id-123"
        assert item["content"] == "test content"
        
        # Non-existent ID
        none_item = plugin.get_by_id("nonexistent")
        assert none_item is None
    finally:
        plugin.close()
        _cleanup_test_file(tmp_path)


def test_search_list_all():
    """Test listing all memories."""
    plugin, tmp_path = _make_test_plugin()
    try:
        conn = plugin._get_connection()
        conn.execute("""
            INSERT INTO memories (id, type, content, date, confidence, source)
            VALUES (?, ?, ?, ?, ?, ?)
        """, ("item-1", "FACT", "item 1", "2026-01-01T00:00:00", 0.9, "system"))
        conn.execute("""
            INSERT INTO memories (id, type, content, date, confidence, source)
            VALUES (?, ?, ?, ?, ?, ?)
        """, ("item-2", "MEMORY", "item 2", "2026-01-02T00:00:00", 0.8, "user"))
        conn.commit()
        
        all_items = plugin.list_all()
        assert len(all_items) == 2
        # Should be ordered by date DESC (newest first)
        assert all_items[0]["id"] == "item-2"
        assert all_items[1]["id"] == "item-1"
    finally:
        plugin.close()
        _cleanup_test_file(tmp_path)


def test_search_pagination():
    """Test pagination with limit and offset."""
    plugin, tmp_path = _make_test_plugin()
    try:
        conn = plugin._get_connection()
        for i in range(5):
            conn.execute("""
                INSERT INTO memories (id, type, content, date, confidence, source)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (f"item-{i}", "FACT", f"item {i}", f"2026-01-{i+1:02d}T00:00:00", 0.9, "system"))
        conn.commit()
        
        # First page (limit 2)
        result = plugin.query("", {"limit": 2, "offset": 0})
        assert result["total"] == 5
        assert len(result["results"]) == 2
        
        # Second page
        result = plugin.query("", {"limit": 2, "offset": 2})
        assert result["total"] == 5
        assert len(result["results"]) == 2
    finally:
        plugin.close()
        _cleanup_test_file(tmp_path)


def test_search_combined_filters():
    """Test combining multiple filters."""
    plugin, tmp_path = _make_test_plugin()
    try:
        conn = plugin._get_connection()
        conn.execute("""
            INSERT INTO memories (id, type, content, date, confidence, source)
            VALUES (?, ?, ?, ?, ?, ?)
        """, ("fact-high", "FACT", "high confidence fact", "2026-06-01T00:00:00", 0.95, "system"))
        conn.execute("""
            INSERT INTO memories (id, type, content, date, confidence, source)
            VALUES (?, ?, ?, ?, ?, ?)
        """, ("mem-low", "MEMORY", "low confidence memory", "2026-06-01T00:00:00", 0.3, "user"))
        conn.commit()
        
        # Filter: FACT type + high confidence
        result = plugin.query("", {
            "type": "FACT",
            "confidence_range": (0.8, 1.0),
        })
        assert result["total"] == 1
        assert result["results"][0]["id"] == "fact-high"
    finally:
        plugin.close()
        _cleanup_test_file(tmp_path)
