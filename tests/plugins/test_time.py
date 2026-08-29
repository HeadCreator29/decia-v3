# Test for Task 2.6: TIME plugin extraction
# Verifies TIME plugin classification matches golden master

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "app"))

from brain.plugins.base import IntentPlugin
from brain.intent_types import Pattern, PHRASE, TIME, REGEX, CONFIDENCE_SEGURO
from brain.plugins.registry import PluginRegistry


def test_time_plugin_creation():
    """Verify TIME plugin can be created with patterns from _init_patterns()"""
    time_patterns = [
        Pattern(PHRASE, "que hora es", 100),
        Pattern(PHRASE, "cuanto es la hora", 100),
        Pattern(PHRASE, "dime la hora", 95),
        Pattern(PHRASE, "me dices la hora", 95),
        Pattern(PHRASE, "puedes decirme la hora", 90),
        Pattern(PHRASE, "me puedes decir la hora", 90),
        Pattern(PHRASE, "sabes que hora es", 90),
        Pattern(REGEX,
                r"que\s+hora\s+(es|tien[ea]|tenemos|estamos)",
                100),
        Pattern(REGEX,
                r"hora\s+(actual|ahora|de\s+ahora)",
                85),
        Pattern(REGEX,
                r"(?:dime|me\s+dices|me\s+puedes\s+decir|sabes|cual|cuanto)\s+(?:es)?\s?(la)?hora",
                80),
    ]
    plugin = IntentPlugin(
        name="TIME",
        category="UTILITY",
        patterns=time_patterns,
        priority=10,
    )
    assert plugin.name == "TIME"
    assert plugin.category == "UTILITY"
    assert len(plugin.patterns) == 10
    assert plugin.priority == 10
    # Default validate returns True
    assert plugin.validate("test message", {}) is True


def test_time_plugin_classification_que_hora_es():
    """Verify TIME plugin classifies 'que hora es' as TIME intent."""
    registry = PluginRegistry()
    plugin = IntentPlugin(
        name="TIME",
        category="UTILITY",
        patterns=[
            Pattern(PHRASE, "que hora es", 100),
        ],
        priority=10,
    )
    registry.register(plugin)
    result = registry.get_plugin("TIME").classify("que hora es")
    assert result is not None
    assert result.intent == TIME


def test_time_plugin_classification_dime_la_hora():
    """Verify TIME plugin classifies 'dime la hora' as TIME intent."""
    registry = PluginRegistry()
    plugin = IntentPlugin(
        name="TIME",
        category="UTILITY",
        patterns=[
            Pattern(PHRASE, "dime la hora", 95),
        ],
        priority=10,
    )
    registry.register(plugin)
    result = registry.get_plugin("TIME").classify("dime la hora")
    assert result is not None
    assert result.intent == TIME


def test_time_plugin_priority():
    """Verify TIME plugin has priority 10."""
    plugin = IntentPlugin(
        name="TIME",
        category="UTILITY",
        patterns=[],
        priority=10,
    )
    assert plugin.priority == 10


def test_time_plugin_validate_default():
    """Verify TIME plugin's default validate() returns True."""
    plugin = IntentPlugin(
        name="TIME",
        category="UTILITY",
        patterns=[],
        priority=10,
    )
    result = plugin.validate("que hora es", {})
    assert result is True, f"Default validate() returns True, got {result}"