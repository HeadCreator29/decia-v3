# Test for Task 1.3: PluginRegistry class
# Verifies that PluginRegistry works correctly with register/get operations

import sys
from pathlib import Path

# Add app directory to path
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "app"))

from brain.plugins.registry import PluginRegistry
from brain.plugins.base import IntentPlugin
from brain.intent_types import Pattern, EXACT


def test_registry_creation():
    """Verify PluginRegistry can be instantiated"""
    registry = PluginRegistry()
    assert registry is not None


def test_register_and_get_plugin():
    """Verify register() and get_plugin() work correctly"""
    registry = PluginRegistry()
    plugin = IntentPlugin(
        name="GREETING",
        category="SOCIAL",
        patterns=[
            Pattern(EXACT, "hola", 100, word_boundary=True),
        ],
    )
    registry.register(plugin)
    retrieved = registry.get_plugin("GREETING")
    assert retrieved is not None
    assert retrieved.name == "GREETING"


def test_get_all_patterns():
    """Verify get_all_patterns() returns all registered patterns"""
    registry = PluginRegistry()
    plugin1 = IntentPlugin(
        name="GREETING",
        category="SOCIAL",
        patterns=[
            Pattern(EXACT, "hola", 100, word_boundary=True),
        ],
    )
    plugin2 = IntentPlugin(
        name="THANKS",
        category="SOCIAL",
        patterns=[
            Pattern(EXACT, "gracias", 100),
        ],
    )
    registry.register(plugin1)
    registry.register(plugin2)
    all_patterns = registry.get_all_patterns()
    assert "GREETING" in all_patterns
    assert "THANKS" in all_patterns
    assert len(all_patterns["GREETING"]) == 1
    assert len(all_patterns["THANKS"]) == 1


def test_get_plugin_unknown():
    """Verify get_plugin() returns None for unknown intent"""
    registry = PluginRegistry()
    retrieved = registry.get_plugin("UNKNOWN_INTENT")
    assert retrieved is None


def test_validate_match_default():
    """Verify validate_match() returns True by default (no plugin registered)"""
    registry = PluginRegistry()
    result = registry.validate_match("GREETING", "hola", {})
    assert result is True


def test_validate_match_with_plugin():
    """Verify validate_match() delegates to plugin.validate()"""
    registry = PluginRegistry()
    plugin = IntentPlugin(
        name="GREETING",
        category="SOCIAL",
        patterns=[],
    )
    registry.register(plugin)
    result = registry.validate_match("GREETING", "hola", {})
    assert result is True