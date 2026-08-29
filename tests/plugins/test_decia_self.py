# test_decia_self.py - DECIA_SELF plugin contract test
# Verifies DECIA_SELF plugin classification matches golden master

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "app"))

from brain.plugins.base import IntentPlugin
from brain.intent_types import Pattern, EXACT, PHRASE, DECIA_SELF
from brain.plugins.registry import PluginRegistry


def test_decia_self_plugin_creation():
    """Verify DECIA_SELF plugin can be created with patterns from _init_patterns()."""
    plugin = IntentPlugin(
        name="DECIA_SELF",
        category="IDENTITY",
        patterns=[
            Pattern(EXACT, "quien eres", 100),
            Pattern(EXACT, "que eres", 100),
            Pattern(EXACT, "como te llamas", 100),
            Pattern(EXACT, "cual es tu nombre", 100),
            Pattern(PHRASE, "quien eres", 90),
            Pattern(PHRASE, "que eres", 90),
            Pattern(PHRASE, "como te llamas", 90),
            Pattern(PHRASE, "cual es tu nombre", 90),
            Pattern(PHRASE, "que es decia", 100),
            Pattern(PHRASE, "hablame de decia", 100),
            Pattern(PHRASE, "hablame sobre decia", 100),
            Pattern(PHRASE, "que significa decia", 100),
            Pattern(PHRASE, "quien es decia", 100),
            Pattern(PHRASE, "de donde vienes", 90),
            Pattern(PHRASE, "para que sirves", 90),
            Pattern(PHRASE, "cuales son tus funciones", 90),
            Pattern(PHRASE, "para que estas creada", 90),
        ],
        priority=5,
        entity_group=None,
    )
    assert plugin.name == DECIA_SELF
    assert len(plugin.patterns) == 17
    assert plugin.priority == 5
    assert plugin.entity_group is None


def test_decia_self_plugin_classification():
    """Verify DECIA_SELF plugin classification via IntentLayer golden master."""
    from brain.intent_layer import IntentLayer
    il = IntentLayer()
    r = il.classify("quien eres")
    assert r.intent == DECIA_SELF
    assert r.confidence >= 0.90


def test_decia_self_plugin_classification_que_eres():
    """Verify DECIA_SELF plugin classification for 'que eres'."""
    from brain.intent_layer import IntentLayer
    il = IntentLayer()
    r = il.classify("que eres")
    assert r.intent == DECIA_SELF
    assert r.confidence >= 0.90


def test_decia_self_plugin_classification_como_te_llamas():
    """Verify DECIA_SELF plugin classification for 'como te llamas'."""
    from brain.intent_layer import IntentLayer
    il = IntentLayer()
    r = il.classify("como te llamas")
    assert r.intent == DECIA_SELF
    assert r.confidence >= 0.90


def test_decia_self_plugin_classification_cual_es_tu_nombre():
    """Verify DECIA_SELF plugin classification for 'cual es tu nombre'."""
    from brain.intent_layer import IntentLayer
    il = IntentLayer()
    r = il.classify("cual es tu nombre")
    assert r.intent == DECIA_SELF
    assert r.confidence >= 0.90


def test_decia_self_classification_phrase_variants():
    """Verify DECIA_SELF plugin handles PHRASE pattern variants."""
    from brain.intent_layer import IntentLayer
    il = IntentLayer()

    # These should all classify as DECIA_SELF
    test_cases = [
        "hablame de decia",
        "hablame sobre decia",
        "que significa decia",
        "quien es decia",
        "de donde vienes",
        "para que sirves",
        "cuales son tus funciones",
        "para que estas creada",
    ]

    for message in test_cases:
        r = il.classify(message)
        assert r.intent == DECIA_SELF, f"Expected DECIA_SELF for '{message}', got {r.intent}"
        assert r.confidence >= 0.90, f"Expected high confidence for '{message}', got {r.confidence}"