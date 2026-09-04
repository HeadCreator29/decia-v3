# tests/services/test_history.py
# Contract assertions for HistoryPlugin: events + temporal query

import sys
from pathlib import Path

# Add app directory to path
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "app"))

from app.services.plugins.history import HistoryPlugin


def test_history_add_event():
    """HistoryPlugin.add must store event with timestamp."""
    plugin = HistoryPlugin()
    plugin.execute({"action": "add", "event": {"type": "message", "text": "hello"}})
    events = plugin.execute({"action": "query"})
    assert len(events) == 1
    assert events[0]["type"] == "message"
    assert events[0]["text"] == "hello"
    assert "timestamp" in events[0]


def test_history_query_all():
    """HistoryPlugin.query without filters must return all events."""
    plugin = HistoryPlugin()
    plugin.execute({"action": "add", "event": {"type": "a"}})
    plugin.execute({"action": "add", "event": {"type": "b"}})
    result = plugin.execute({"action": "query"})
    assert len(result) == 2


def test_history_temporal_filter():
    """HistoryPlugin.query with since/until must filter by timestamp."""
    import time
    plugin = HistoryPlugin()
    plugin.execute({"action": "add", "event": {"type": "old"}})
    time.sleep(0.01)
    plugin.execute({"action": "add", "event": {"type": "new"}})
    # Query since now should only get "new"
    since_ts = time.time() - 0.005
    result = plugin.execute({"action": "query", "since": since_ts})
    assert len(result) == 1
    assert result[0]["type"] == "new"


def test_history_limit():
    """HistoryPlugin.query with limit must cap results."""
    plugin = HistoryPlugin()
    for i in range(5):
        plugin.execute({"action": "add", "event": {"seq": i}})
    result = plugin.execute({"action": "query", "limit": 2})
    assert len(result) == 2


def test_history_clear():
    """HistoryPlugin.clear must remove all events."""
    plugin = HistoryPlugin()
    plugin.execute({"action": "add", "event": {"type": "test"}})
    plugin.execute({"action": "clear"})
    result = plugin.execute({"action": "query"})
    assert result == []