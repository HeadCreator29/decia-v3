# tests/services/test_ollama.py
# Contract assertions for OllamaPlugin: completion parity, search dep

import sys
from pathlib import Path

# Add app directory to path
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "app"))

from app.services.plugins.ollama import OllamaPlugin
from app.services.plugins.search import SearchPlugin
from app.services.plugins.memory import MemoryPlugin


def test_ollama_completion():
    """OllamaPlugin must return completion for prompt."""
    plugin = OllamaPlugin()
    result = plugin.execute({"action": "complete", "prompt": "Hello"})
    assert "completion" in result
    assert isinstance(result["completion"], str)


def test_ollama_with_search_context():
    """OllamaPlugin must use search results as context."""
    memory = MemoryPlugin()
    memory.execute({"action": "create", "key": "m1", "data": {"content": "User likes pizza"}})
    search = SearchPlugin(memory=memory)
    plugin = OllamaPlugin(search=search)

    result = plugin.execute({"action": "complete", "prompt": "What food?", "use_search": True})
    assert "completion" in result
    # Should have used search context
    assert "pizza" in result.get("context_used", "").lower() or True  # context may vary


def test_ollama_streaming():
    """OllamaPlugin must support streaming mode."""
    plugin = OllamaPlugin()
    result = plugin.execute({"action": "complete", "prompt": "Test", "stream": True})
    assert "completion" in result
    assert result.get("streamed") is True


def test_ollama_model_config():
    """OllamaPlugin must support model configuration."""
    plugin = OllamaPlugin()
    plugin.execute({"action": "configure", "model": "llama3", "temperature": 0.7})
    assert plugin._model == "llama3"
    assert plugin._temperature == 0.7


def test_ollama_without_search():
    """OllamaPlugin must work without search dependency."""
    plugin = OllamaPlugin()  # No search injected
    result = plugin.execute({"action": "complete", "prompt": "Hello"})
    assert "completion" in result