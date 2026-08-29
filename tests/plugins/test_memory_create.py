# test_memory_create.py - MEMORY_CREATE plugin contract test
# Verifies MEMORY_CREATE plugin classification matches golden master

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "app"))

from brain.plugins.base import IntentPlugin
from brain.intent_types import Pattern, PHRASE, MEMORY_CREATE
from brain.plugins.registry import PluginRegistry


def test_memory_create_plugin_creation():
    """Verify MEMORY_CREATE plugin can be created with patterns from _init_patterns()."""
    plugin = IntentPlugin(
        name="MEMORY_CREATE",
        category="MEMORY",
        patterns=[
            Pattern(PHRASE, "guarda que", 100, entity_group="memory"),
            Pattern(PHRASE, "guarda esto", 100, entity_group="memory"),
            Pattern(PHRASE, "recuerda que", 100, entity_group="memory"),
            Pattern(PHRASE, "recuerda esto", 100, entity_group="memory"),
            Pattern(PHRASE, "anota que", 100, entity_group="memory"),
            Pattern(PHRASE, "anota esto", 100, entity_group="memory"),
            Pattern(PHRASE, "memoriza que", 100, entity_group="memory"),
            Pattern(PHRASE, "quiero que recuerdes", 95, entity_group="memory"),
            Pattern(PHRASE, "quiero que guardes", 95, entity_group="memory"),
        ],
        priority=5,
        entity_group="memory",
    )
    assert plugin.name == MEMORY_CREATE
    assert len(plugin.patterns) == 9
    assert plugin.priority == 5
    assert plugin.entity_group == "memory"


def test_memory_create_plugin_guarda_que():
    """Verify MEMORY_CREATE plugin classification via IntentLayer golden master."""
    from brain.intent_layer import IntentLayer
    il = IntentLayer()
    r = il.classify("guarda que esto")
    assert r.intent == MEMORY_CREATE
    assert r.entities.get("memory") is not None
    assert r.confidence >= 0.90


def test_memory_create_plugin_quiero_que_recuerdes():
    """Verify MEMORY_CREATE plugin classification for 'quiero que recuerdes mi cumpleaños'."""
    from brain.intent_layer import IntentLayer
    il = IntentLayer()
    r = il.classify("quiero que recuerdes mi cumpleaños")
    assert r.intent == MEMORY_CREATE
    assert r.confidence >= 0.90