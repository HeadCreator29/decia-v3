# Test for Task 2.1: GREETING plugin extraction
# Verifies GREETING plugin classification matches golden master

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "app"))

from brain.plugins.base import IntentPlugin
from brain.intent_types import Pattern, EXACT, PHRASE, GREETING, THANKS, CONFIDENCE_SEGURO
from brain.plugins.registry import PluginRegistry


def test_greeting_plugin_creation():
    """Verify GREETING plugin can be created with patterns from _init_patterns()"""
    plugin = IntentPlugin(
        name="GREETING",
        category="SOCIAL",
        patterns=[
            Pattern(EXACT, "hola", 100, word_boundary=True),
            Pattern(PHRASE, "buenos dias", 95, {"buenos": 5}),
            Pattern(PHRASE, "buenas tardes", 95, {"buenas": 5}),
            Pattern(PHRASE, "buenas noches", 95, {"buenas": 5}),
            Pattern(PHRASE, "buenas", 90),
        ],
        priority=10,
    )
    assert plugin.name == "GREETING"
    assert plugin.category == "SOCIAL"
    assert len(plugin.patterns) == 5
    assert plugin.priority == 10
    # Default validate returns True
    assert plugin.validate("hola", {}) is True


def test_greeting_plugin_classification_hola():
    """Verify GREETING plugin classifies 'hola' as GREETING intent."""
    registry = PluginRegistry()
    plugin = IntentPlugin(
        name="GREETING",
        category="SOCIAL",
        patterns=[
            Pattern(EXACT, "hola", 100, word_boundary=True),
        ],
        priority=10,
    )
    registry.register(plugin)
    # Plugin should classify "hola" as GREETING
    result = registry.get_plugin("GREETING").classify("hola")
    assert result is not None
    assert result.intent == GREETING


def test_greeting_plugin_classification_buenos_dias():
    """Verify GREETING plugin classifies 'buenos dias' as GREETING intent."""
    registry = PluginRegistry()
    plugin = IntentPlugin(
        name="GREETING",
        category="SOCIAL",
        patterns=[
            Pattern(PHRASE, "buenos dias", 95, {"buenos": 5}),
        ],
        priority=10,
    )
    registry.register(plugin)
    result = registry.get_plugin("GREETING").classify("buenos dias")
    assert result is not None
    assert result.intent == GREETING


def test_greeting_plugin_classification_buenas_tardes():
    """Verify GREETING plugin classifies 'buenas tardes' as GREETING intent."""
    registry = PluginRegistry()
    plugin = IntentPlugin(
        name="GREETING",
        category="SOCIAL",
        patterns=[
            Pattern(PHRASE, "buenas tardes", 95, {"buenas": 5}),
        ],
        priority=10,
    )
    registry.register(plugin)
    result = registry.get_plugin("GREETING").classify("buenas tardes")
    assert result is not None
    assert result.intent == GREETING


def test_greeting_plugin_classification_buenas_noches():
    """Verify GREETING plugin classifies 'buenas noches' as GREETING intent."""
    registry = PluginRegistry()
    plugin = IntentPlugin(
        name="GREETING",
        category="SOCIAL",
        patterns=[
            Pattern(PHRASE, "buenas noches", 95, {"buenas": 5}),
        ],
        priority=10,
    )
    registry.register(plugin)
    result = registry.get_plugin("GREETING").classify("buenas noches")
    assert result is not None
    assert result.intent == GREETING


def test_greeting_plugin_classification_buenas():
    """Verify GREETING plugin classifies 'buenas' as GREETING intent."""
    registry = PluginRegistry()
    plugin = IntentPlugin(
        name="GREETING",
        category="SOCIAL",
        patterns=[
            Pattern(PHRASE, "buenas", 90),
        ],
        priority=10,
    )
    registry.register(plugin)
    result = registry.get_plugin("GREETING").classify("buenas")
    assert result is not None
    assert result.intent == GREETING


def test_greeting_plugin_classification_hola_upper():
    """Verify GREETING plugin normalizes uppercase 'HOLA'."""
    registry = PluginRegistry()
    plugin = IntentPlugin(
        name="GREETING",
        category="SOCIAL",
        patterns=[
            Pattern(EXACT, "hola", 100, word_boundary=True),
        ],
        priority=10,
    )
    registry.register(plugin)
    result = registry.get_plugin("GREETING").classify("HOLA")
    assert result is not None
    assert result.intent == GREETING


def test_greeting_plugin_classification_hola_punct():
    """Verify GREETING plugin handles 'hola?' with punctuation."""
    registry = PluginRegistry()
    plugin = IntentPlugin(
        name="GREETING",
        category="SOCIAL",
        patterns=[
            Pattern(EXACT, "hola", 100, word_boundary=True),
        ],
        priority=10,
    )
    registry.register(plugin)
    result = registry.get_plugin("GREETING").classify("hola?")
    assert result is not None
    assert result.intent == GREETING


def test_greeting_plugin_classification_exclam_hola():
    """Verify GREETING plugin handles '¡Hola!' with inverted exclamation."""
    registry = PluginRegistry()
    plugin = IntentPlugin(
        name="GREETING",
        category="SOCIAL",
        patterns=[
            Pattern(EXACT, "hola", 100, word_boundary=True),
        ],
        priority=10,
    )
    registry.register(plugin)
    result = registry.get_plugin("GREETING").classify("¡Hola!")
    assert result is not None
    assert result.intent == GREETING


def test_greeting_plugin_validate_default():
    """Verify GREETING plugin's default validate() returns True."""
    plugin = IntentPlugin(
        name="GREETING",
        category="SOCIAL",
        patterns=[],
    )
    result = plugin.validate("hola", {})
    assert result is True, f"Default validate() should return True, got {result}"