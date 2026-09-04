# tests/services/test_discovery.py
# Contract assertions for pkgutil auto-discovery + fallback

import sys
from pathlib import Path

# Add app directory to path
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "app"))

from app.services.plugins import discover_plugins, _FALLBACK_PLUGINS


def test_discover_plugins_returns_registry():
    """discover_plugins must return a populated ServiceRegistry."""
    registry = discover_plugins()
    assert registry is not None
    # Should have at least the fallback plugins
    assert len(registry) >= len(_FALLBACK_PLUGINS)


def test_fallback_plugins_exist():
    """_FALLBACK_PLUGINS must define all 8 core plugins."""
    expected = {
        "IDENTITY", "USER", "HISTORY", "MEMORY",
        "SEARCH", "VOICE", "PLANNER", "OLLAMA"
    }
    assert set(_FALLBACK_PLUGINS.keys()) == expected


def test_fallback_plugin_structure():
    """Each fallback plugin must have name, category, execute."""
    for name, plugin in _FALLBACK_PLUGINS.items():
        assert plugin.name == name
        assert plugin.category in ("ARCHIVE", "PLANNER", "OLLAMA", "VOICE")
        assert callable(plugin.execute)
        assert callable(plugin.validate)


def test_discover_idempotent():
    """Multiple calls to discover_plugins must return equivalent registries."""
    reg1 = discover_plugins()
    reg2 = discover_plugins()
    assert set(reg1._plugins.keys()) == set(reg2._plugins.keys())