# test_planner_query.py - PLANNER_QUERY plugin contract test
# Verifies PLANNER_QUERY plugin classification matches golden master

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "app"))

from brain.plugins.base import IntentPlugin
from brain.intent_types import Pattern, REGEX, PLANNER_QUERY
from brain.plugins.registry import PluginRegistry


def test_planner_query_plugin_creation():
    """Verify PLANNER_QUERY plugin can be created with patterns from _init_patterns()."""
    plugin = IntentPlugin(
        name="PLANNER_QUERY",
        category="PLANNING",
        patterns=[
            Pattern(REGEX, r"^que\s+tengo\s+pendiente\b", 90),
            Pattern(REGEX, r"^que\s+tengo\s+que\s+hacer", 90),
            Pattern(REGEX, r"^que\s+debo\s+hacer", 90),
            Pattern(REGEX, r"^que\s+(?:eventos|planes|recordatorios)", 90),
            Pattern(REGEX, r"^que\s+hay", 85),
            Pattern(REGEX, r"^que\s+tengo", 90),
        ],
        priority=5,
        entity_group=None,
    )
    assert plugin.name == PLANNER_QUERY
    assert len(plugin.patterns) == 6
    assert plugin.priority == 5
    assert plugin.entity_group is None


def test_planner_query_plugin_que_tengo_pendiente():
    """Verify PLANNER_QUERY plugin classification via IntentLayer golden master."""
    from brain.intent_layer import IntentLayer
    il = IntentLayer()
    r = il.classify("que tengo pendiente")
    assert r.intent == PLANNER_QUERY
    assert r.confidence >= 0.90