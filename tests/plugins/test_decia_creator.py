# test_decia_creator.py - DECIA_CREATOR plugin contract test
# Verifies DECIA_CREATOR plugin classification matches golden master

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "app"))

from brain.plugins.base import IntentPlugin
from brain.intent_types import Pattern, EXACT, PHRASE, KEYWORD, DECIA_CREATOR
from brain.plugins.registry import PluginRegistry


def test_decia_creator_plugin_creation():
    """Verify DECIA_CREATOR plugin can be created with patterns from _init_patterns()."""
    plugin = IntentPlugin(
        name="DECIA_CREATOR",
        category="IDENTITY",
        patterns=[
            Pattern(PHRASE, "quien te creo", 100),
            Pattern(PHRASE, "quien te creÃ³", 100),
            Pattern(PHRASE, "quien es tu creador", 100),
            Pattern(PHRASE, "quien es tu creadora", 100),
            Pattern(PHRASE, "quien hizo", 95),
            Pattern(PHRASE, "quien te hizo", 95),
            Pattern(PHRASE, "como te crearon", 95),
            Pattern(PHRASE, "como naciste", 95),
            Pattern(KEYWORD, "quien", 65, {"creo": 15, "hizo": 15}),
            Pattern(KEYWORD, "quiÃ©n", 65, {"creo": 15, "hizo": 15}),
            Pattern(KEYWORD, "creador", 70, {"quien": 10, "quiÃ©n": 10}),
            Pattern(KEYWORD, "creadora", 70, {"quien": 10, "quiÃ©n": 10}),
        ],
        priority=5,
        entity_group=None,
    )
    assert plugin.name == DECIA_CREATOR
    assert len(plugin.patterns) == 12
    assert plugin.priority == 5
    assert plugin.entity_group is None


def test_decia_creator_plugin_classification_quien_te_creo():
    """Verify DECIA_CREATOR plugin classification for 'quién te creo'."""
    from brain.intent_layer import IntentLayer
    il = IntentLayer()
    r = il.classify("quién te creo")
    assert r.intent == DECIA_CREATOR
    assert r.confidence >= 0.90


def test_decia_creator_plugin_classification_quien_es_tu_creador():
    """Verify DECIA_CREATOR plugin classification for 'quién es tu creador'."""
    from brain.intent_layer import IntentLayer
    il = IntentLayer()
    r = il.classify("quién es tu creador")
    assert r.intent == DECIA_CREATOR
    assert r.confidence >= 0.90


def test_decia_creator_plugin_classification_como_naciste():
    """Verify DECIA_CREATOR plugin classification for 'como naciste'."""
    from brain.intent_layer import IntentLayer
    il = IntentLayer()
    r = il.classify("como naciste")
    assert r.intent == DECIA_CREATOR
    assert r.confidence >= 0.90


def test_decia_creator_plugin_classification_quien_te_hizo():
    """Verify DECIA_CREATOR plugin classification for 'quién te hizo'."""
    from brain.intent_layer import IntentLayer
    il = IntentLayer()
    r = il.classify("quién te hizo")
    assert r.intent == DECIA_CREATOR
    assert r.confidence >= 0.90