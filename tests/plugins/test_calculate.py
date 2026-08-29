# Test for Task 2.5: CALCULATE plugin extraction
# Verifies CALCULATE plugin classification matches golden master

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "app"))

from brain.plugins.base import IntentPlugin
from brain.intent_types import Pattern, REGEX, CALCULATE, CONFIDENCE_SEGURO
from brain.plugins.registry import PluginRegistry


def test_calculate_plugin_creation():
    """Verify CALCULATE plugin can be created with patterns from _init_patterns()"""
    calculate_patterns = [
        Pattern(REGEX,
                r"^[\d\s\+\-\*\/\(\)\.]+$",
                100, entity_group="math"),
        Pattern(REGEX,
                r"^\d+\s*(mas|menos|por|entre|x|×)\s*\d+",
                95, entity_group="math"),
        Pattern(REGEX,
                r"^cuanto\s+es\s+\d+\s*(mas|menos|por|entre|x|×)\s+\d+",
                90, entity_group="math"),
        Pattern(REGEX,
                r"^que\s+es\s+\d+\s*(mas|menos|por|entre|x|×)\s+\d+",
                90, entity_group="math"),
        Pattern(REGEX,
                r"^calcular\s+\d+\s*(mas|menos|por|entre|x|×)\s*\d+",
                90, entity_group="math"),
    ]
    plugin = IntentPlugin(
        name="CALCULATE",
        category="UTILITY",
        patterns=calculate_patterns,
        priority=5,
        entity_group="math",
    )
    assert plugin.name == "CALCULATE"
    assert plugin.category == "UTILITY"
    assert len(plugin.patterns) == 5
    assert plugin.priority == 5
    assert plugin.entity_group == "math"
    # Default validate returns True
    assert plugin.validate("test message", {}) is True


def test_calculate_plugin_classification_simple():
    """Verify CALCULATE plugin classifies '2+2' as CALCULATE intent."""
    registry = PluginRegistry()
    plugin = IntentPlugin(
        name="CALCULATE",
        category="UTILITY",
        patterns=[
            Pattern(REGEX,
                    r"^[\d\s\+\-\*\/\(\)\.]+$",
                    100, entity_group="math"),
        ],
        priority=5,
        entity_group="math",
    )
    registry.register(plugin)
    result = registry.get_plugin("CALCULATE").classify("2+2")
    assert result is not None
    assert result.intent == CALCULATE


def test_calculate_plugin_classification_expression():
    """Verify CALCULATE plugin classifies '(3+5)*2' as CALCULATE intent."""
    registry = PluginRegistry()
    plugin = IntentPlugin(
        name="CALCULATE",
        category="UTILITY",
        patterns=[
            Pattern(REGEX,
                    r"^[\d\s\+\-\*\/\(\)\.]+$",
                    100, entity_group="math"),
            Pattern(REGEX,
                    r"^\d+\s*(mas|menos|por|entre|x|×)\s*\d+",
                    95, entity_group="math"),
        ],
        priority=5,
        entity_group="math",
    )
    registry.register(plugin)
    result = registry.get_plugin("CALCULATE").classify("(3+5)*2")
    assert result is not None
    assert result.intent == CALCULATE


def test_calculate_plugin_validate_default():
    """Verify CALCULATE plugin's default validate() returns True."""
    plugin = IntentPlugin(
        name="CALCULATE",
        category="UTILITY",
        patterns=[],
        priority=5,
        entity_group="math",
    )
    result = plugin.validate("2+2", {})
    assert result is True, f"Default validate() returns True, got {result}"