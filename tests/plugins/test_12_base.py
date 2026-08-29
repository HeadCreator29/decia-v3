# Test for Task 1.2: IntentPlugin dataclass
# Verifies that IntentPlugin can be instantiated with the expected fields

import sys
from pathlib import Path

# Add app directory to path
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "app"))

from brain.plugins.base import IntentPlugin
from brain.intent_types import Pattern, EXACT

def test_intent_plugin_creation():
    """Verify IntentPlugin can be created with required fields"""
    plugin = IntentPlugin(
        name="GREETING",
        category="SOCIAL",
        patterns=[
            Pattern(EXACT, "hola", 100, word_boundary=True),
        ],
    )
    assert plugin.name == "GREETING"
    assert plugin.category == "SOCIAL"
    assert len(plugin.patterns) == 1
    assert plugin.priority == 0  # default
    assert plugin.validate is not None  # default validate method exists


def test_intent_plugin_default_validate():
    """Verify default validate() returns True"""
    plugin = IntentPlugin(
        name="TEST",
        category="TEST",
        patterns=[],
    )
    result = plugin.validate("test message", {})
    assert result is True, f"Default validate() should return True, got {result}"


def test_intent_plugin_optional_fields():
    """Verify optional entity_group and priority fields"""
    plugin = IntentPlugin(
        name="CALCULATE",
        category="UTILITY",
        patterns=[],
        entity_group="math",
        priority=5,
    )
    assert plugin.entity_group == "math"
    assert plugin.priority == 5