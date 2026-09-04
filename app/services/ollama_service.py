# app/services/ollama_service.py - DEPRECATED façade
# Delegates to OllamaPlugin for backward compatibility
# TODO: Remove in Phase 6 cleanup

import warnings
from app.services.plugins.ollama import OllamaPlugin
from app.services.plugins.search import SearchPlugin


# Module-level plugin instances
_search_plugin = SearchPlugin()
_ollama_plugin = OllamaPlugin(search=_search_plugin)


def ask_ollama(message: str, context=None) -> str:
    """Deprecated: Use OllamaPlugin.execute() instead.

    This façade will be removed in Phase 6.
    """
    warnings.warn(
        "services.ollama_service.ask_ollama is deprecated. "
        "Use services.plugins.ollama.OllamaPlugin.execute() instead.",
        DeprecationWarning,
        stacklevel=2,
    )
    result = _ollama_plugin.execute({
        "action": "complete",
        "prompt": message,
        "use_search": True,
    })
    return result.get("completion", "")


# Re-export for backward compatibility
__all__ = ["ask_ollama"]