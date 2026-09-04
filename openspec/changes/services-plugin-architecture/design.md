# Design: Services Plugin Architecture

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                      ServiceRegistry                             │
│  register()  get()  get_instance()  discover()                  │
└────────────────────────────┬────────────────────────────────────┘
         │                    │                    │
         ▼                    ▼                    ▼
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│  ARCHIVE     │     │   VOICE      │     │   LLM        │
│  Plugins     │     │  Plugin      │     │  Plugins     │
├──────────────┤     ├──────────────┤     ├──────────────┤
│ Identity     │     │ VoicePlugin  │     │ Planner      │
│ User         │     │ (merged)     │     │ Ollama       │
│ History      │     └──────────────┘     └──────────────┘
│ Memory       │
│ Search       │
└──────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────────────┐
│                     Façade Layer                                 │
│  services/archive.py  →  re-exports from registry               │
│  services/ollama_service.py  →  delegates to OllamaPlugin       │
│  services/speaker.py  →  re-exports VoicePlugin.speak()         │
└─────────────────────────────────────────────────────────────────┘
```

## Core Contracts

### `ServicePlugin` (in `app/services/plugins/base.py`)

```python
from dataclasses import dataclass
from abc import ABC, abstractmethod
from typing import Any

@dataclass
class ServicePlugin(ABC):
    name: str                    # "identity", "memory", "search", "voice", "planner", "ollama"
    category: str                # "ARCHIVE", "VOICE", "PLANNER", "LLM"
    version: str = "1.0.0"
    dependencies: list[str] = () # e.g., ["identity", "search"]
    
    @abstractmethod
    def initialize(self, config: dict[str, Any]) -> None:
        """Called once on first get_instance()."""
        pass
    
    @abstractmethod
    def shutdown(self) -> None:
        """Called on process exit."""
        pass
```

### `ServiceRegistry` (in `app/services/plugins/registry.py`)

```python
class ServiceRegistry:
    def __init__(self):
        self._plugins: dict[str, ServicePlugin] = {}
        self._instances: dict[str, Any] = {}
    
    def register(self, plugin: ServicePlugin) -> None:
        self._plugins[plugin.name] = plugin
    
    def get(self, name: str) -> ServicePlugin | None:
        return self._plugins.get(name)
    
    def get_instance(self, name: str) -> Any:
        if name not in self._instances:
            plugin = self._plugins[name]
            for dep in plugin.dependencies:
                self.get_instance(dep)  # ensure deps initialized first
            self._instances[name] = plugin.create_instance()
        return self._instances[name]
    
    def discover(self, package: str = "app.services.plugins") -> list[ServicePlugin]:
        import pkgutil, importlib
        plugins = []
        for _, modname, _ in pkgutil.iter_modules([f"app/services/plugins"]):
            module = importlib.import_module(f"app.services.plugins.{modname}")
            if hasattr(module, "plugin"):
                plugins.append(module.plugin)
        return plugins
```

## Plugin Designs

### 1. IdentityPlugin (`app/services/plugins/identity.py`)

```python
plugin = ServicePlugin(
    name="identity",
    category="ARCHIVE",
    dependencies=[],
    initialize=lambda cfg: load_archive_files(cfg.get("archive_path")),
    shutdown=lambda: None,
)

# Public API (identical to original services.archive)
def get_identity() -> dict: ...
def save_identity(data: dict) -> bool: ...
```

**Config:** `{"archive_path": "data/archive"}`

### 2. UserPlugin (`app/services/plugins/user.py`)

```python
plugin = ServicePlugin(
    name="user",
    category="ARCHIVE",
    dependencies=[],
    initialize=lambda cfg: load_user_file(cfg.get("archive_path")),
)

def get_user() -> dict: ...
def save_user(data: dict) -> bool: ...
```

### 3. HistoryPlugin (`app/services/plugins/history.py`)

```python
plugin = ServicePlugin(
    name="history",
    category="ARCHIVE",
    dependencies=[],
    initialize=lambda cfg: load_history_file(cfg.get("archive_path")),
)

def get_history() -> dict: ...
def query_events(start: str, end: str) -> list: ...
```

### 4. MemoryPlugin (`app/services/plugins/memory.py`)

```python
plugin = ServicePlugin(
    name="memory",
    category="ARCHIVE",
    dependencies=[],
    initialize=lambda cfg: load_memories(cfg.get("archive_path")),
)

def get_memories() -> dict: ...
def save_memory(memory: dict) -> bool: ...
def deduplicate_memories(memories: list) -> list: ...
def _memory_model(desc: str) -> tuple: ...
def _canonical_word(word: str) -> str: ...

# _VERB_FAMILY_BASE, _CANONICAL_EXCEPTIONS as module constants
```

### 5. SearchPlugin (`app/services/plugins/search.py`)

```python
plugin = ServicePlugin(
    name="search",
    category="ARCHIVE",
    dependencies=["identity", "user", "history", "memory"],
    initialize=lambda cfg: None,  # uses registry.get_instance() for deps
)

def search_archive(query: str) -> list: ...
def _resolve_temporal_filter(query: str) -> tuple | None: ...
def _word_match(word: str, query: str) -> bool: ...
```

### 6. VoicePlugin (`app/services/plugins/voice.py`)

```python
plugin = ServicePlugin(
    name="voice",
    category="VOICE",
    dependencies=[],
    initialize=lambda cfg: init_whisper_model(cfg),
    shutdown=lambda: cleanup_audio(),
)

# Merges voice.py + speaker.py
def speak(text: str) -> None: ...
def listen() -> str | None: ...
def speak_async(text: str) -> Future: ...  # if needed by voice_pipeline
```

**Config:** `{"model_size": "small", "mic_device": 1, "sample_rate": 16000, "voice_threshold": 0.025}`

### 7. PlannerPlugin (`app/services/plugins/planner.py`)

```python
plugin = ServicePlugin(
    name="planner",
    category="PLANNER",
    dependencies=[],
    initialize=lambda cfg: load_planner_file(cfg.get("archive_path")),
)

def load_plans() -> dict: ...
def save_plan(plan: dict) -> str: ...
def query_plans(**filters) -> list: ...
def update_plan_status(plan_id: str, status: str) -> bool: ...
def update_plan_time(plan_id: str, due_time: str) -> bool: ...
```

### 8. OllamaPlugin (`app/services/plugins/ollama.py`)

```python
plugin = ServicePlugin(
    name="ollama",
    category="LLM",
    dependencies=["search"],
    initialize=lambda cfg: create_http_client(cfg),
)

def complete(prompt: str, context: list | None = None) -> str: ...
def ask_ollama(message: str, context: list | None = None) -> str: ...
```

**Config:** `{"model": "llama3.2:3b", "url": "http://localhost:11434/api/chat"}`

## Façade Modules

### `services/archive.py` (thin wrapper)

```python
from services.plugins.registry import registry

# Re-export all original functions via registry
from services.plugins.identity import get_identity, save_identity
from services.plugins.user import get_user, save_user
from services.plugins.history import get_history
from services.plugins.memory import get_memories, save_memory, deduplicate_memories
from services.plugins.search import search_archive

# Preserve original module API
__all__ = [
    "load_archive", "get_identity", "save_identity",
    "get_user", "save_user", "get_history",
    "get_memories", "save_memory", "deduplicate_memories",
    "normalize", "deduplicate_memories", "search_archive",
    "build_archive_context",
]
```

### `services/ollama_service.py` (thin wrapper)

```python
from services.plugins.registry import registry

def ask_ollama(message: str, context: list | None = None) -> str:
    plugin = registry.get_instance("ollama")
    return plugin.ask_ollama(message, context)

# Preserve original functions that handlers.py may call directly
__all__ = ["ask_ollama", "remove_thinking", "needs_archive"]
```

### `services/speaker.py` (deprecated, re-exports)

```python
from services.plugins.voice import plugin as voice_plugin

def speak(text: str) -> None:
    return voice_plugin.get_instance("voice").speak(text)

# Preserve original API
engine = None  # deprecated
__all__ = ["speak", "engine"]
```

## Auto-Discovery

```python
# In app/services/plugins/__init__.py
from services.plugins.registry import ServiceRegistry, registry

def initialize_plugins(config: dict | None = None) -> ServiceRegistry:
    discovered = registry.discover()
    for plugin in discovered:
        plugin.initialize(config or {})
    return registry
```

**Explicit fallback list** (for reliability):
```python
_FALLBACK_PLUGINS = [
    "app.services.plugins.identity",
    "app.services.plugins.user",
    "app.services.plugins.history",
    "app.services.plugins.memory",
    "app.services.plugins.search",
    "app.services.plugins.voice",
    "app.services.plugins.planner",
    "app.services.plugins.ollama",
]
```

## Migration Phases (9 Phases)

| Phase | Tasks | Verification |
|-------|-------|--------------|
| **0** | Create `base.py`, `registry.py`, `__init__.py`; unit tests for registry | `pytest tests/services/test_plugin_base.py tests/services/test_registry.py` |
| **1** | Extract `IdentityPlugin`; façade re-exports | Full test suite passes |
| **2** | Extract `UserPlugin` | Full test suite passes |
| **3** | Extract `HistoryPlugin` | Full test suite passes |
| **4** | Extract `MemoryPlugin` (most complex) | Full test suite + contract tests |
| **5** | Extract `SearchPlugin` (depends on 1-4) | Full test suite + regression matrix |
| **6** | Merge `VoicePlugin` (voice.py + speaker.py); delete speaker.py | Voice tests + speaker tests pass |
| **7** | Create `PlannerPlugin`, `OllamaPlugin`; update ollama_service façade | Integration tests pass |
| **8** | Remove monolith functions from archive.py; full cleanup | Full suite + performance benchmarks |

## Testing Strategy

| Test File | Coverage |
|-----------|----------|
| `test_plugin_base.py` | ServicePlugin contract, initialize/shutdown |
| `test_registry.py` | Registration, instance resolution, dependency order, discovery |
| `test_identity.py` | IdentityPlugin get/save parity |
| `test_user.py` | UserPlugin get/save parity |
| `test_history.py` | HistoryPlugin events + temporal query |
| `test_memory.py` | MemoryPlugin CRUD, dedup, canonical forms |
| `test_search.py` | SearchPlugin orchestration, temporal filter |
| `test_voice.py` | VoicePlugin listen/speak parity (merged) |
| `test_planner.py` | PlannerPlugin CRUD parity |
| `test_ollama.py` | OllamaPlugin completion parity |
| `test_regression.py` | Parametrized matrix: all 21 call sites, all archive functions |

**Golden Master**: At each phase, run `pytest tests/ -x` — all existing tests must pass unchanged.

**Performance**: `pytest tests/test_intent_stress.py` — p95 within 5% baseline, memory < 10MB.

## Open Decisions

1. **voice_pipeline integration**: Keep separate (it's already modular). `VoicePlugin` provides `listen()`/`speak()` for legacy sync code; `voice_pipeline` uses its own processors.
2. **Ollama streaming**: Defer. Current `ask_ollama` is non-streaming. If `voice_pipeline` needs streaming, add `complete_stream()` to `OllamaPlugin` later.
3. **Health checks**: Add optional `health_check()` to `ServicePlugin` base if observability needed.
4. **Config schema**: Use `dict` for now (matches intent-layer pattern); can upgrade to dataclass if validation needed.

---

*Created: 2026-08-30*
*Change: services-plugin-architecture*
*Based on: specs/services-plugin-architecture/spec.md*