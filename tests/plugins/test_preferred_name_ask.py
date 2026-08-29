# test_preferred_name_ask.py - PREFERRED_NAME_ASK plugin contract test
# Verifies PREFERRED_NAME_ASK plugin classification matches golden master

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "app"))

from brain.plugins.base import IntentPlugin
from brain.intent_types import Pattern, EXACT, PHRASE, PREFERRED_NAME_ASK
from brain.plugins.registry import PluginRegistry


def test_preferred_name_ask_plugin_creation():
    """Verify PREFERRED_NAME_ASK plugin can be created with patterns from _init_patterns()."""
    plugin = IntentPlugin(
        name="PREFERRED_NAME_ASK",
        category="IDENTITY",
        patterns=[
            Pattern(EXACT, "como quieres llamarme", 100),
            Pattern(PHRASE, "como quieres llamarme", 90),
            Pattern(PHRASE, "como me llama", 85),
            Pattern(EXACT, "como me llama", 95),
        ],
        priority=5,
        entity_group=None,
    )
    assert plugin.name == PREFERRED_NAME_ASK
    assert len(plugin.patterns) == 4
    assert plugin.priority == 5
    assert plugin.entity_group is None


def test_preferred_name_ask_plugin_como_quieres_llamarme():
    """Verify PREFERRED_NAME_ASK plugin classification via IntentLayer golden master."""
    from brain.intent_layer import IntentLayer
    il = IntentLayer()
    r = il.classify("como quieres llamarme")
    assert r.intent == PREFERRED_NAME_ASK
    assert r.confidence >= 0.90


def test_preferred_name_ask_plugin_como_me_llama():
    """Verify PREFERRED_NAME_ASK plugin classification for 'como me llama'."""
    from brain.intent_layer import IntentLayer
    il = IntentLayer()
    r = il.classify("como me llama")
    assert r.intent == PREFERRED_NAME_ASK
    assert r.confidence >= 0.90


def test_preferred_name_ask_plugin_como_quieres():
    """Verify PREFERRED_NAME_ASK plugin classification for 'como quieres llamarme'."""
    from brain.intent_layer import IntentLayer
    il = IntentLayer()
    r = il.classify("como quieres llamarme")
    assert r.intent == PREFERRED_NAME_ASK
    assert r.confidence >= 0.90