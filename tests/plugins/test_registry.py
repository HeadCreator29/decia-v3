# tests/plugins/test_registry.py
# Registration, discovery, priority ordering, validation hook default/override

import sys
from pathlib import Path

# Add app directory to path
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "app"))

from brain.plugins.registry import PluginRegistry
from brain.plugins.base import IntentPlugin
from brain.intent_types import Pattern, EXACT, KEYWORD, PHRASE


def test_registry_create():
    """PluginRegistry can be instantiated."""
    registry = PluginRegistry()
    assert registry is not None


def test_registry_register():
    """register() stores plugin and its patterns."""
    registry = PluginRegistry()
    plugin = IntentPlugin(
        name="GREETING",
        category="SOCIAL",
        patterns=[
            Pattern(EXACT, "hola", 100),
            Pattern(PHRASE, "buenos dias", 95),
        ],
    )
    registry.register(plugin)
    assert registry.get_plugin("GREETING") is plugin


def test_registry_get_patterns():
    """get_patterns() returns patterns for the given intent."""
    registry = PluginRegistry()
    plugin = IntentPlugin(
        name="GREETING",
        category="SOCIAL",
        patterns=[
            Pattern(EXACT, "hola", 100),
        ],
    )
    registry.register(plugin)
    patterns = registry.get_patterns("GREETING")
    assert len(patterns) == 1
    assert patterns[0].value == "hola"


def test_registry_get_all_patterns():
    """get_all_patterns() returns all patterns grouped by intent."""
    registry = PluginRegistry()
    plugin1 = IntentPlugin(
        name="GREETING",
        category="SOCIAL",
        patterns=[Pattern(EXACT, "hola", 100)],
    )
    plugin2 = IntentPlugin(
        name="THANKS",
        category="SOCIAL",
        patterns=[Pattern(EXACT, "gracias", 100)],
    )
    registry.register(plugin1)
    registry.register(plugin2)
    all_patterns = registry.get_all_patterns()
    assert "GREETING" in all_patterns
    assert "THANKS" in all_patterns


def test_registry_get_plugin_unknown():
    """get_plugin() returns None for unregistered intent."""
    registry = PluginRegistry()
    assert registry.get_plugin("UNKNOWN") is None


def test_registry_validate_match_default():
    """validate_match() returns True by default when no plugin registered."""
    registry = PluginRegistry()
    assert registry.validate_match("GREETING", "hola", {}) is True


def test_registry_validate_match_with_plugin():
    """validate_match() delegates to plugin.validate()."""
    registry = PluginRegistry()
    plugin = IntentPlugin(
        name="GREETING",
        category="SOCIAL",
        patterns=[],
    )
    registry.register(plugin)
    assert registry.validate_match("GREETING", "hola", {}) is True


def test_registry_validate_match_no_plugin():
    """validate_match() returns True when plugin not registered (fallback)."""
    registry = PluginRegistry()
    assert registry.validate_match("ANY_INTENT", "some message", {}) is True


def test_registry_priority_ordering():
    """Plugins should store priority for ordering purposes."""
    registry = PluginRegistry()
    plugin_low = IntentPlugin(
        name="LOW_PRIORITY",
        category="TEST",
        patterns=[],
        priority=1,
    )
    plugin_high = IntentPlugin(
        name="HIGH_PRIORITY",
        category="TEST",
        patterns=[],
        priority=10,
    )
    registry.register(plugin_low)
    registry.register(plugin_high)
    retrieved_low = registry.get_plugin("LOW_PRIORITY")
    retrieved_high = registry.get_plugin("HIGH_PRIORITY")
    assert retrieved_low.priority == 1
    assert retrieved_high.priority == 10