# app/services/plugins/__init__.py
# Auto-discovery + fallback plugins for service registry

import pkgutil
import importlib
from typing import Dict

from app.services.plugins.base import ServicePlugin
from app.services.plugins.registry import ServiceRegistry


# Fallback plugin definitions (used when auto-discovery finds nothing)
# Categories: ARCHIVE, PLANNER, OLLAMA, VOICE, DECISION, PREDICTION, LEARNING, REFLECTION, IDENTITY_CORE
_FALLBACK_PLUGINS: Dict[str, ServicePlugin] = {
    "IDENTITY_CORE": ServicePlugin(
        name="IDENTITY_CORE",
        category="ARCHIVE",
        description="Versioned identity core with audit log and proposal/approval ceremony",
        execute=lambda ctx: {"status": "not_implemented"},
    ),
    "IDENTITY": ServicePlugin(
        name="IDENTITY",
        category="ARCHIVE",
        description="User identity management",
        execute=lambda ctx: {"status": "not_implemented"},
    ),
    "USER": ServicePlugin(
        name="USER",
        category="ARCHIVE",
        description="User profile and preferences",
        execute=lambda ctx: {"status": "not_implemented"},
    ),
    "HISTORY": ServicePlugin(
        name="HISTORY",
        category="ARCHIVE",
        description="Conversation history and events",
        execute=lambda ctx: {"status": "not_implemented"},
    ),
    "MEMORY": ServicePlugin(
        name="MEMORY",
        category="ARCHIVE",
        description="Long-term memory with deduplication",
        execute=lambda ctx: {"status": "not_implemented"},
    ),
    "SEARCH": ServicePlugin(
        name="SEARCH",
        category="ARCHIVE",
        description="Search orchestration with temporal filters",
        execute=lambda ctx: {"status": "not_implemented"},
    ),
    "VOICE": ServicePlugin(
        name="VOICE",
        category="VOICE",
        description="Voice I/O (STT + TTS merged)",
        execute=lambda ctx: {"status": "not_implemented"},
    ),
    "PLANNER": ServicePlugin(
        name="PLANNER",
        category="PLANNER",
        description="Task planning and scheduling",
        execute=lambda ctx: {"status": "not_implemented"},
    ),
    "OLLAMA": ServicePlugin(
        name="OLLAMA",
        category="OLLAMA",
        description="Ollama LLM completion with search dependency",
        execute=lambda ctx: {"status": "not_implemented"},
    ),
    "DECISION": ServicePlugin(
        name="DECISION",
        category="ARCHIVE",
        description="Structured decision logging with status lifecycle",
        execute=lambda ctx: {"status": "not_implemented"},
    ),
    "PREDICTION": ServicePlugin(
        name="PREDICTION",
        category="ARCHIVE",
        description="Structured prediction logging with status lifecycle",
        execute=lambda ctx: {"status": "not_implemented"},
    ),
    "LEARNING": ServicePlugin(
        name="LEARNING",
        category="ARCHIVE",
        description="Learning capture from decisions and predictions",
        execute=lambda ctx: {"status": "not_implemented"},
    ),
    "REFLECTION": ServicePlugin(
        name="REFLECTION",
        category="ARCHIVE",
        description="Reflection/diary entries with mandatory encryption",
        execute=lambda ctx: {"status": "not_implemented"},
    ),
}


def _discover_via_pkgutil() -> Dict[str, ServicePlugin]:
    """Discover plugins via pkgutil from app.services.plugins package."""
    discovered = {}
    try:
        package = __import__("app.services.plugins", fromlist=[""])
        for _, module_name, _ in pkgutil.iter_modules(package.__path__):
            if module_name in ("base", "registry", "__init__"):
                continue
            try:
                module = importlib.import_module(f"app.services.plugins.{module_name}")
                if hasattr(module, "PLUGIN"):
                    plugin = module.PLUGIN
                    if isinstance(plugin, ServicePlugin):
                        discovered[plugin.name] = plugin
            except Exception:
                # Silently skip modules that fail to load
                pass
    except Exception:
        pass
    return discovered


# Module-level cache for idempotent discovery
_DISCOVERED_REGISTRY: ServiceRegistry | None = None


def discover_plugins() -> ServiceRegistry:
    """Discover and return a populated ServiceRegistry.

    Tries pkgutil auto-discovery first, falls back to _FALLBACK_PLUGINS.
    Results are cached for idempotent calls.
    """
    global _DISCOVERED_REGISTRY
    if _DISCOVERED_REGISTRY is not None:
        return _DISCOVERED_REGISTRY

    registry = ServiceRegistry()
    discovered = _discover_via_pkgutil()

    # Use discovered plugins if any, otherwise fallbacks
    plugins_to_register = discovered if discovered else _FALLBACK_PLUGINS

    for plugin in plugins_to_register.values():
        registry.register(plugin)

    _DISCOVERED_REGISTRY = registry
    return registry


def reset_discovery_cache() -> None:
    """Reset the discovery cache (mainly for testing)."""
    global _DISCOVERED_REGISTRY
    _DISCOVERED_REGISTRY = None


# Public exports
__all__ = [
    "ServicePlugin",
    "ServiceRegistry",
    "discover_plugins",
    "reset_discovery_cache",
    "_FALLBACK_PLUGINS",
]