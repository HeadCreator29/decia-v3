# test_user_name_set.py - USER_NAME_SET plugin contract test
# Verifies USER_NAME_SET plugin classification matches golden master

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "app"))

from brain.plugins.base import IntentPlugin
from brain.intent_types import Pattern, REGEX, USER_NAME_SET
from brain.plugins.registry import PluginRegistry


def test_user_name_set_plugin_creation():
    """Verify USER_NAME_SET plugin can be created with patterns from _init_patterns()."""
    plugin = IntentPlugin(
        name="USER_NAME_SET",
        category="IDENTITY",
        patterns=[
            Pattern(REGEX, r"mi nombre es\s+(.+)", 100, entity_group="user_name"),
            Pattern(REGEX, r"el nombre mio es\s+(.+)", 95, entity_group="user_name"),
            Pattern(REGEX, r"nombre mio es\s+(.+)", 95, entity_group="user_name"),
            Pattern(REGEX, r"me llamo\s+(.+)", 90, entity_group="user_name"),
            Pattern(REGEX, r"yo me llamo\s+(.+)", 90, entity_group="user_name"),
            Pattern(REGEX, r"el mio es\s+(.+)", 85, entity_group="user_name"),
            Pattern(REGEX, r"ese es mi nombre\s+(.+)", 85, entity_group="user_name"),
        ],
        priority=5,
        entity_group="user_name",
    )
    assert plugin.name == USER_NAME_SET
    assert len(plugin.patterns) == 7
    assert plugin.priority == 5
    assert plugin.entity_group == "user_name"


def test_user_name_set_plugin_mi_nombre_es():
    """Verify USER_NAME_SET plugin classification via IntentLayer golden master."""
    from brain.intent_layer import IntentLayer
    il = IntentLayer()
    r = il.classify("mi nombre es Juan")
    assert r.intent == USER_NAME_SET
    assert r.entities.get("user_name") == "Juan"
    assert r.confidence >= 0.90


def test_user_name_set_plugin_el_nombre_mio_es():
    """Verify USER_NAME_SET plugin classification for 'el nombre mio es ...'."""
    from brain.intent_layer import IntentLayer
    il = IntentLayer()
    r = il.classify("el nombre mio es Maria")
    assert r.intent == USER_NAME_SET
    assert r.entities.get("user_name") == "Maria"
    assert r.confidence >= 0.90


def test_user_name_set_plugin_me_llamo():
    """Verify USER_NAME_SET plugin classification for 'me llamo ...'."""
    from brain.intent_layer import IntentLayer
    il = IntentLayer()
    r = il.classify("me llamo Pedro")
    assert r.intent == USER_NAME_SET
    assert r.entities.get("user_name") == "Pedro"
    assert r.confidence >= 0.90