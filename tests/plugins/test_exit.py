# Test for Task 2.4: EXIT plugin extraction
# Verifies EXIT plugin structure and negation validation

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "app"))

from brain.plugins.base import IntentPlugin
from brain.intent_types import Pattern, EXACT, PHRASE, EXIT, REGEX, CONFIDENCE_SEGURO
from brain.plugins.registry import PluginRegistry


def test_exit_plugin_creation():
    """Verify EXIT plugin can be created with patterns from _init_patterns()"""
    exit_patterns = [
        Pattern(EXACT, "salir", 100),
        Pattern(EXACT, "exit", 100),
        Pattern(EXACT, "quit", 100),
        Pattern(EXACT, "adios", 100,
                word_boundary=True),
        Pattern(PHRASE, "salir por favor", 90),
        Pattern(EXACT, "quiero salir", 90),
        Pattern(PHRASE, "hasta luego", 90),
        Pattern(PHRASE, "nos vemos", 90),
        Pattern(PHRASE, "hasta manana", 90),
        Pattern(PHRASE, "me voy a dormir", 85),
        Pattern(REGEX,
                r"^(?:ya\s+)?me\s+voy"
                r"\s*[.!?]*$",
                90),
    ]
    plugin = IntentPlugin(
        name="EXIT",
        category="SOCIAL",
        patterns=exit_patterns,
        priority=10,
    )
    assert plugin.name == "EXIT"
    assert plugin.category == "SOCIAL"
    assert len(plugin.patterns) == 11
    assert plugin.priority == 10
    # Default validate returns True
    assert plugin.validate("test message", {}) is True


def test_exit_plugin_validate_negation():
    """Verify EXIT plugin's validate() blocks no+salir cases.
    
    The design specifies EXIT.validate() returns False for negation cases
    like "no quiero salir". The plugin override comes after the default.
    """
    from brain.plugins.exit import exit_plugin
    # "no quiero salir" should be blocked by exit negation
    result = exit_plugin.validate("no quiero salir", {})
    # The plugin override should return False for negation cases
    assert result is False, f"EXIT.validate() should return False for 'no salir', got {result}"


def test_exit_plugin_validate_no_negation():
    """Verify EXIT validate() returns True when no negation is present.
    
    Plain "salir" without "no" should pass validation.
    """
    from brain.plugins.exit import exit_plugin
    # "salir" alone - no negation
    result = exit_plugin.validate("salir", {})
    assert result is True, f"EXIT.validate() should return True for 'salir' without negation, got {result}"


def test_exit_plugin_validate_no_salir():
    """Verify EXIT validate() returns True when 'salir' is absent."""
    from brain.plugins.exit import exit_plugin
    # "no hola" - has "no" but no "salir"
    result = exit_plugin.validate("no hola", {})
    assert result is True, f"EXIT.validate() should return True when 'salir' is absent, got {result}"


def test_exit_plugin_registration():
    """Verify EXIT plugin can be registered in the registry."""
    registry = PluginRegistry()
    plugin = IntentPlugin(
        name="EXIT",
        category="SOCIAL",
        patterns=[],
        priority=10,
    )
    registry.register(plugin)
    assert registry.get_plugin("EXIT") is plugin
    patterns = registry.get_patterns("EXIT")
    assert len(patterns) == 0


def test_exit_plugin_priority():
    """Verify EXIT plugin has priority 10."""
    plugin = IntentPlugin(
        name="EXIT",
        category="SOCIAL",
        patterns=[],
        priority=10,
    )
    assert plugin.priority == 10