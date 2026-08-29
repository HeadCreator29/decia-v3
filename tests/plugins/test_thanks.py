# Test for Task 2.2: THANKS plugin extraction
# Verifies THANKS plugin classification matches golden master

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "app"))

from brain.plugins.base import IntentPlugin
from brain.intent_types import Pattern, EXACT, PHRASE, THANKS, CONFIDENCE_SEGURO
from brain.plugins.registry import PluginRegistry


def test_thanks_plugin_creation():
    """Verify THANKS plugin can be created with patterns from _init_patterns()"""
    plugin = IntentPlugin(
        name="THANKS",
        category="SOCIAL",
        patterns=[
            Pattern(EXACT, "gracias", 100),
            Pattern(EXACT, "muchas gracias", 100),
            Pattern(PHRASE, "muchas gracias", 95),
            Pattern(PHRASE, "gracias", 90),
        ],
        priority=5,
    )
    assert plugin.name == "THANKS"
    assert plugin.category == "SOCIAL"
    assert len(plugin.patterns) == 4
    assert plugin.priority == 5
    # Default validate returns True
    assert plugin.validate("gracias", {}) is True


def test_thanks_plugin_classification_gracias():
    """Verify THANKS plugin classifies 'gracias' as THANKS intent."""
    registry = PluginRegistry()
    plugin = IntentPlugin(
        name="THANKS",
        category="SOCIAL",
        patterns=[
            Pattern(EXACT, "gracias", 100),
        ],
        priority=5,
    )
    registry.register(plugin)
    # Plugin should classify "gracias" as THANKS
    result = registry.get_plugin("THANKS").classify("gracias")
    assert result is not None
    assert result.intent == THANKS


def test_thanks_plugin_classification_muchas_gracias():
    """Verify THANKS plugin classifies 'muchas gracias' as THANKS intent."""
    registry = PluginRegistry()
    plugin = IntentPlugin(
        name="THANKS",
        category="SOCIAL",
        patterns=[
            Pattern(EXACT, "muchas gracias", 100),
        ],
        priority=5,
    )
    registry.register(plugin)
    result = registry.get_plugin("THANKS").classify("muchas gracias")
    assert result is not None
    assert result.intent == THANKS


def test_thanks_plugin_classification_normalization():
    """Verify THANKS plugin normalizes case for 'GRACIAS'."""
    registry = PluginRegistry()
    plugin = IntentPlugin(
        name="THANKS",
        category="SOCIAL",
        patterns=[
            Pattern(EXACT, "gracias", 100),
        ],
        priority=5,
    )
    registry.register(plugin)
    result = registry.get_plugin("THANKS").classify("GRACIAS")
    assert result is not None
    assert result.intent == THANKS


def test_thanks_plugin_validate_default():
    """Verify THANKS plugin's default validate() returns True."""
    plugin = IntentPlugin(
        name="THANKS",
        category="SOCIAL",
        patterns=[],
    )
    result = plugin.validate("gracias", {})
    assert result is True, f"Default validate() should return True, got {result}"