# test_preferred_name_set.py - PREFERRED_NAME_SET plugin contract test
# Verifies PREFERRED_NAME_SET plugin classification matches golden master

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "app"))

from brain.plugins.base import IntentPlugin
from brain.intent_types import Pattern, REGEX, PREFERRED_NAME_SET
from brain.plugins.registry import PluginRegistry


def test_preferred_name_set_plugin_creation():
    """Verify PREFERRED_NAME_SET plugin can be created with patterns from _init_patterns()."""
    plugin = IntentPlugin(
        name="PREFERRED_NAME_SET",
        category="IDENTITY",
        patterns=[
            Pattern(REGEX, r"puedes llamarme\s+(.+)", 100, entity_group="preferred_name"),
            Pattern(REGEX, r"quiero que me llames\s+(.+)", 100, entity_group="preferred_name"),
            Pattern(REGEX, r"me vas a llamar\s+(.+)", 95, entity_group="preferred_name"),
            Pattern(REGEX, r"vas a llamarme\s+(.+)", 95, entity_group="preferred_name"),
            Pattern(REGEX, r"desde ahora llamame\s+(.+)", 95, entity_group="preferred_name"),
            Pattern(REGEX, r"de ahora en adelante llamame\s+(.+)", 95, entity_group="preferred_name"),
            Pattern(REGEX, r"llamame\s+(.+)", 85, entity_group="preferred_name"),
        ],
        priority=5,
        entity_group="preferred_name",
    )
    assert plugin.name == PREFERRED_NAME_SET
    assert len(plugin.patterns) == 7
    assert plugin.priority == 5
    assert plugin.entity_group == "preferred_name"


def test_preferred_name_set_plugin_puedes_llamarme():
    """Verify PREFERRED_NAME_SET plugin classification via IntentLayer golden master."""
    from brain.intent_layer import IntentLayer
    il = IntentLayer()
    r = il.classify("puedes llamarme Juan")
    assert r.intent == PREFERRED_NAME_SET
    assert r.entities.get("preferred_name") == "Juan"
    assert r.confidence >= 0.90


def test_preferred_name_set_plugin_quiero_que_me_llames():
    """Verify PREFERRED_NAME_SET plugin classification for 'quiero que me llames ...'."""
    from brain.intent_layer import IntentLayer
    il = IntentLayer()
    r = il.classify("quiero que me llames Maria")
    assert r.intent == PREFERRED_NAME_SET
    assert r.entities.get("preferred_name") == "Maria"
    assert r.confidence >= 0.90


def test_preferred_name_set_plugin_desde_ahora():
    """Verify PREFERRED_NAME_SET plugin classification for 'de ahora en adelante llamame ...'."""
    from brain.intent_layer import IntentLayer
    il = IntentLayer()
    r = il.classify("de ahora en adelante llamame Carlos")
    assert r.intent == PREFERRED_NAME_SET
    assert r.entities.get("preferred_name") == "Carlos"
    assert r.confidence >= 0.90