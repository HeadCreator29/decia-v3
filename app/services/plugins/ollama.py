# app/services/plugins/ollama.py - OllamaPlugin
# Ollama LLM completion with search dependency

from typing import Optional
from app.services.plugins.base import ServicePlugin
from app.services.plugins.search import SearchPlugin


class OllamaPlugin:
    """Plugin for Ollama LLM completion with optional search context."""

    def __init__(self, search: Optional[SearchPlugin] = None):
        self._model = "llama3"
        self._temperature = 0.7
        self._search = search
        self._plugin = ServicePlugin(
            name="OLLAMA",
            category="OLLAMA",
            description="Ollama LLM completion with search dependency",
            execute=self.execute,
        )

    @property
    def name(self) -> str:
        return self._plugin.name

    @property
    def category(self) -> str:
        return self._plugin.category

    def execute(self, context: dict) -> dict:
        """Execute Ollama operation.

        Args:
            context: Dict with action (complete|configure) and parameters

        Returns:
            Result dict
        """
        action = context.get("action", "complete")

        if action == "complete":
            prompt = context.get("prompt", "")
            use_search = context.get("use_search", False)
            stream = context.get("stream", False)

            # Build context from search if requested
            context_used = ""
            if use_search and self._search:
                search_results = self._search.execute({"action": "search", "query": prompt})
                # Extract relevant text from search results
                parts = []
                for source, results in search_results.items():
                    if isinstance(results, dict):
                        for v in results.values():
                            if isinstance(v, dict) and "content" in v:
                                parts.append(v["content"])
                            elif isinstance(v, str):
                                parts.append(v)
                    elif isinstance(results, list):
                        for v in results:
                            if isinstance(v, dict) and "content" in v:
                                parts.append(v["content"])
                context_used = " ".join(parts[:5])  # Limit context

            # In real implementation, would call Ollama API
            # For now, return mock completion
            completion = f"[Mock completion for: {prompt[:50]}]"
            if context_used:
                completion += f" | Context: {context_used[:100]}"

            return {
                "completion": completion,
                "model": self._model,
                "temperature": self._temperature,
                "streamed": stream,
                "context_used": context_used,
            }

        elif action == "configure":
            if "model" in context:
                self._model = context["model"]
            if "temperature" in context:
                self._temperature = context["temperature"]
            return {"status": "configured", "model": self._model, "temperature": self._temperature}

        else:
            raise ValueError(f"Unknown action: {action}")


# Module-level PLUGIN for auto-discovery (standalone)
PLUGIN = OllamaPlugin()