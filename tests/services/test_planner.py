# tests/services/test_planner.py
# Contract assertions for PlannerPlugin: load/save/query/update parity

import sys
from pathlib import Path

# Add app directory to path
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "app"))

from app.services.plugins.planner import PlannerPlugin


def test_planner_create_and_get():
    """PlannerPlugin must create and retrieve plans."""
    plugin = PlannerPlugin()
    plan = {"id": "plan_1", "title": "Test Plan", "steps": ["step1", "step2"]}
    plugin.execute({"action": "create", "key": "plan_1", "data": plan})
    result = plugin.execute({"action": "get", "key": "plan_1"})
    assert result == plan


def test_planner_update():
    """PlannerPlugin must update existing plan."""
    plugin = PlannerPlugin()
    plugin.execute({"action": "create", "key": "p1", "data": {"title": "Old", "steps": []}})
    plugin.execute({"action": "update", "key": "p1", "data": {"title": "New", "steps": ["a"]}})
    result = plugin.execute({"action": "get", "key": "p1"})
    assert result["title"] == "New"
    assert result["steps"] == ["a"]


def test_planner_query():
    """PlannerPlugin.query must filter by status or tag."""
    plugin = PlannerPlugin()
    plugin.execute({"action": "create", "key": "p1", "data": {"title": "A", "status": "active", "tags": ["work"]}})
    plugin.execute({"action": "create", "key": "p2", "data": {"title": "B", "status": "done", "tags": ["personal"]}})
    results = plugin.execute({"action": "query", "status": "active"})
    assert len(results) == 1
    assert results[0]["title"] == "A"


def test_planner_delete():
    """PlannerPlugin.delete must remove plan."""
    plugin = PlannerPlugin()
    plugin.execute({"action": "create", "key": "p1", "data": {"title": "Test"}})
    plugin.execute({"action": "delete", "key": "p1"})
    result = plugin.execute({"action": "get", "key": "p1"})
    assert result == {}


def test_planner_list():
    """PlannerPlugin.list must return all plan keys."""
    plugin = PlannerPlugin()
    plugin.execute({"action": "create", "key": "a", "data": {}})
    plugin.execute({"action": "create", "key": "b", "data": {}})
    result = plugin.execute({"action": "list"})
    assert set(result) == {"a", "b"}