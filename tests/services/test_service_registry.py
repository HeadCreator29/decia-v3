# tests/services/test_registry.py
# Contract assertions for ServiceRegistry:
# - register/get/get_instance/discover

import sys
from pathlib import Path

# Add app directory to path
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "app"))

from app.services.plugins.base import ServicePlugin
from app.services.plugins.registry import ServiceRegistry


def test_registry_register_and_get():
    """Registry must register and retrieve plugins by name."""
    registry = ServiceRegistry()
    plugin = ServicePlugin(name="IDENTITY", category="ARCHIVE")
    registry.register(plugin)
    retrieved = registry.get("IDENTITY")
    assert retrieved is plugin


def test_registry_get_instance_returns_new():
    """get_instance must return a fresh instance each call."""
    registry = ServiceRegistry()
    plugin = ServicePlugin(name="IDENTITY", category="ARCHIVE")
    registry.register(plugin)
    instance1 = registry.get_instance("IDENTITY")
    instance2 = registry.get_instance("IDENTITY")
    assert instance1 is not instance2
    assert instance1.name == "IDENTITY"
    assert instance2.name == "IDENTITY"


def test_registry_discover_by_category():
    """discover must return plugins matching category."""
    registry = ServiceRegistry()
    registry.register(ServicePlugin(name="IDENTITY", category="ARCHIVE"))
    registry.register(ServicePlugin(name="USER", category="ARCHIVE"))
    registry.register(ServicePlugin(name="PLANNER", category="PLANNER"))
    archive_plugins = registry.discover("ARCHIVE")
    assert len(archive_plugins) == 2
    assert all(p.category == "ARCHIVE" for p in archive_plugins)


def test_registry_get_missing_raises():
    """get must raise KeyError for missing plugin."""
    registry = ServiceRegistry()
    try:
        registry.get("NONEXISTENT")
        assert False, "Expected KeyError"
    except KeyError:
        pass


def test_registry_duplicate_register_raises():
    """Registering duplicate name must raise ValueError."""
    registry = ServiceRegistry()
    registry.register(ServicePlugin(name="IDENTITY", category="ARCHIVE"))
    try:
        registry.register(ServicePlugin(name="IDENTITY", category="ARCHIVE"))
        assert False, "Expected ValueError"
    except ValueError:
        pass