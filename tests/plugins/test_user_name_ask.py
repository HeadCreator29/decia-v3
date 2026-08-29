# test_user_name_ask.py - USER_NAME_ASK plugin contract test
# Verifies USER_NAME_ASK plugin classification matches golden master

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "app"))

from brain.plugins.base import IntentPlugin
from brain.intent_types import Pattern, EXACT, PHRASE, USER_NAME_ASK
from brain.plugins.registry import PluginRegistry


def test_user_name_ask_plugin_creation():
    """Verify USER_NAME_ASK plugin can be created with patterns from _init_patterns()."""
    plugin = IntentPlugin(
        name="USER_NAME_ASK",
        category="IDENTITY",
        patterns=[
            Pattern(EXACT, "como me llamo", 100),
            Pattern(EXACT, "cual es mi nombre", 100),
            Pattern(EXACT, "cuales es mi nombre", 100),
            Pattern(EXACT, "que nombre tienes para mi", 100),
            Pattern(EXACT, "por que nombre me llamas", 100),
            Pattern(EXACT, "como me tengo guardado", 100),
            Pattern(EXACT, "quien soy", 90),
            Pattern(EXACT, "y quien soy", 90),
            Pattern(PHRASE, "como me llamo", 85),
            Pattern(PHRASE, "cual es mi nombre", 85),
            Pattern(PHRASE, "quien soy", 80),
        ],
        priority=5,
        entity_group=None,
    )
    assert plugin.name == USER_NAME_ASK
    assert len(plugin.patterns) == 11
    assert plugin.priority == 5
    assert plugin.entity_group is None


def test_user_name_ask_plugin_classification_como_me_llamo():
    """Verify USER_NAME_ASK plugin classification via IntentLayer golden master."""
    from brain.intent_layer import IntentLayer
    il = IntentLayer()
    r = il.classify("como me llamo")
    assert r.intent == USER_NAME_ASK
    assert r.confidence >= 0.90


def test_user_name_ask_plugin_cual_es_mi_nombre():
    """Verify USER_NAME_ASK plugin classification for 'cual es mi nombre'."""
    from brain.intent_layer import IntentLayer
    il = IntentLayer()
    r = il.classify("cual es mi nombre")
    assert r.intent == USER_NAME_ASK
    assert r.confidence >= 0.90


def test_user_name_ask_plugin_quien_soy():
    """Verify USER_NAME_ASK plugin classification for 'quién soy'."""
    from brain.intent_layer import IntentLayer
    il = IntentLayer()
    r = il.classify("quién soy")
    assert r.intent == USER_NAME_ASK
    assert r.confidence >= 0.70  # CONFIDENCE_PROBABLE


def test_user_name_ask_plugin_phrase_variants():
    """Verify USER_NAME_ASK plugin handles PHRASE pattern variants."""
    from brain.intent_layer import IntentLayer
    il = IntentLayer()

    test_cases = [
        "cuales es mi nombre",
        "que nombre tienes para mi",
    ]

    for message in test_cases:
        r = il.classify(message)
        assert r.intent == USER_NAME_ASK, f"Expected USER_NAME_ASK for '{message}', got {r.intent}"
        assert r.confidence >= 0.90, f"Expected high confidence for '{message}', got {r.confidence}"