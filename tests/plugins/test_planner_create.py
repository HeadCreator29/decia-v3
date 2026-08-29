# Test for Task 2.3: PLANNER_CREATE plugin extraction
# Verifies PLANNER_CREATE plugin structure and recall-ban validation

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "app"))

from brain.plugins.base import IntentPlugin
from brain.intent_types import Pattern, REGEX
from brain.plugins.registry import PluginRegistry


def test_planner_create_plugin_creation():
    """Verify PLANNER_CREATE plugin can be created with patterns from _init_patterns()"""
    planner_create_patterns = [
        Pattern(REGEX,
                r"^(?!(?:que|y|quien|cual|cuales|"
                r"cuando|donde|como|por|para)\b)"
                r"(?:(?!\b(?:algo\s+de|sobre|lo\s+que"
                r"|lo\s+de|ayer|anteayer|hace|"
                r"que\s+(?:(?:te\s+)?dije"
                r"|(?:me\s+)?dijiste"
                r"|(?:hemos\s+)?habl(?:amos"
                r"|ado)|paso|hice|hubo"
                r"|sucedio|ocurrio|acontecio)\b)"
                r"|memoria|memorias|recuerdos)\b)*"
                r"a\s+las\s+\d{1,2}(?::\d{2})?\s*"
                r"(?:de\s+la\s+ma[n\u00f1]ana)\b.+",
                85),
        Pattern(REGEX,
                r"^(?:decia\s+)?recuerdame\s+"
                r"(?:(?!\b(?:algo\s+de|sobre|lo\s+que"
                r"|lo\s+de|ayer|anteayer|hace|"
                r"que\s+(?:(?:te\s+)?dije"
                r"|(?:me\s+)?dijiste"
                r"|(?:hemos\s+)?habl(?:amos"
                r"|ado)|paso|hice|hubo"
                r"|sucedio|ocurrio|acontecio)\b)"
                r"|memoria|memorias|recuerdos)\b)+$",
                80),
        Pattern(REGEX,
                r"^(?!(?:que|y|quien|cual|cuales|"
                r"cuando|donde|como|por|para)\b)"
                r"a\s+las\s+\d{1,2}(?::\d{2})?\s*"
                r"(?:de\s+la\s+ma[n\u00f1]ana)\b.+",
                80),
    ]
    plugin = IntentPlugin(
        name="PLANNER_CREATE",
        category="UTILITY",
        patterns=planner_create_patterns,
        priority=0,
    )
    assert plugin.name == "PLANNER_CREATE"
    assert plugin.category == "UTILITY"
    assert len(plugin.patterns) == 3
    assert plugin.priority == 0
    # Default validate returns True
    assert plugin.validate("test message", {}) is True


def test_planner_create_plugin_validate_recall_ban():
    """Verify PLANNER_CREATE plugin's validate() blocks MEMORY_SEARCH theft.
    
    The validate() hook should return False when the message attempts
    to extract memory content that would steal MEMORY_SEARCH intent.
    """
    from brain.plugins.planner_create import planner_create_plugin
    # "recuerdame lo que dije ayer" should be blocked by recall-ban
    result = planner_create_plugin.validate("recuerdame lo que dije ayer", {})
    # The plugin override should return False for recall-ban cases
    assert result is False, f"PLANNER_CREATE.validate() should return False for recall-ban, got {result}"


def test_planner_create_plugin_validate_no_recall_ban():
    """Verify PLANNER_CREATE validate() returns True for non-banned messages.
    
    Messages that don't match _PLANNER_RECALL_BANNED should pass validation.
    """
    from brain.plugins.planner_create import planner_create_plugin
    # "hola" has no banned phrases - should pass validation
    result = planner_create_plugin.validate("hola", {})
    assert result is True, f"PLANNER_CREATE.validate() should return True for non-banned, got {result}"


def test_planner_create_plugin_validate_algo_de_memoria():
    """Verify PLANNER_CREATE validate() blocks 'algo de memoria' phrase."""
    from brain.plugins.planner_create import planner_create_plugin
    # "algo de memoria" is in _PLANNER_RECALL_BANNED - should be blocked
    result = planner_create_plugin.validate("algo de memoria", {})
    assert result is False, f"PLANNER_CREATE.validate() should return False for 'algo de memoria', got {result}"


def test_planner_create_plugin_registration():
    """Verify PLANNER_CREATE plugin can be registered in the registry."""
    registry = PluginRegistry()
    plugin = IntentPlugin(
        name="PLANNER_CREATE",
        category="UTILITY",
        patterns=[],
        priority=0,
    )
    registry.register(plugin)
    assert registry.get_plugin("PLANNER_CREATE") is plugin
    patterns = registry.get_patterns("PLANNER_CREATE")
    assert len(patterns) == 0


def test_planner_create_plugin_priority():
    """Verify PLANNER_CREATE plugin has priority 0."""
    plugin = IntentPlugin(
        name="PLANNER_CREATE",
        category="UTILITY",
        patterns=[],
        priority=0,
    )
    assert plugin.priority == 0