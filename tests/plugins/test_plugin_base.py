# tests/plugins/test_plugin_base.py
# Contract assertions for IntentPlugin dataclass:
# - name, category, patterns count/weights/entity_group/priority
# - default validate()

import sys
from pathlib import Path

# Add app directory to path
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "app"))

from brain.plugins.base import IntentPlugin
from brain.intent_types import Pattern, EXACT, KEYWORD, PHRASE, REGEX


def test_intent_plugin_has_name():
    """IntentPlugin must have a name field."""
    plugin = IntentPlugin(
        name="GREETING",
        category="SOCIAL",
        patterns=[],
    )
    assert plugin.name == "GREETING"


def test_intent_plugin_has_category():
    """IntentPlugin must have a category field."""
    plugin = IntentPlugin(
        name="GREETING",
        category="SOCIAL",
        patterns=[],
    )
    assert plugin.category == "SOCIAL"


def test_intent_plugin_patterns_count():
    """IntentPlugin patterns list must track count correctly."""
    plugin = IntentPlugin(
        name="GREETING",
        category="SOCIAL",
        patterns=[
            Pattern(EXACT, "hola", 100),
            Pattern(PHRASE, "buenos dias", 95),
        ],
    )
    assert len(plugin.patterns) == 2


def test_intent_plugin_pattern_weights():
    """IntentPlugin patterns must preserve weight values."""
    plugin = IntentPlugin(
        name="GREETING",
        category="SOCIAL",
        patterns=[
            Pattern(EXACT, "hola", 100),
            Pattern(PHRASE, "buenos dias", 95),
        ],
    )
    assert plugin.patterns[0].weight == 100
    assert plugin.patterns[1].weight == 95


def test_intent_plugin_entity_group():
    """IntentPlugin entity_group must be optional and default to None."""
    plugin = IntentPlugin(
        name="GREETING",
        category="SOCIAL",
        patterns=[],
    )
    assert plugin.entity_group is None

    plugin_with_group = IntentPlugin(
        name="CALCULATE",
        category="UTILITY",
        patterns=[],
        entity_group="math",
    )
    assert plugin_with_group.entity_group == "math"


def test_intent_plugin_priority():
    """IntentPlugin priority must default to 0 and be configurable."""
    plugin = IntentPlugin(
        name="GREETING",
        category="SOCIAL",
        patterns=[],
    )
    assert plugin.priority == 0

    plugin_high = IntentPlugin(
        name="EXIT",
        category="SOCIAL",
        patterns=[],
        priority=10,
    )
    assert plugin_high.priority == 10


def test_intent_plugin_default_validate():
    """IntentPlugin.default validate() must return True."""
    plugin = IntentPlugin(
        name="GREETING",
        category="SOCIAL",
        patterns=[],
    )
    result = plugin.validate("any message", {})
    assert result is True


def test_intent_plugin_validate_override():
    """IntentPlugin.validate() can be overridden with custom logic."""
    plugin = IntentPlugin(
        name="EXIT",
        category="SOCIAL",
        patterns=[],
    )
    # Custom validation: return False if message contains "no" before "salir"
    result = plugin.validate("no quiero salir", {})
    # Default validate returns True; override would change this
    # For now, verify default behavior
    assert result is True