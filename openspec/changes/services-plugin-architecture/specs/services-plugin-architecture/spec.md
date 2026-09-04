# Delta for Services Plugin Architecture

## ADDED Requirements

### Requirement: ServicePlugin Base Dataclass

The system MUST provide `ServicePlugin` dataclass in `app/services/plugins/base.py` with `name`, `category`, `version`, `dependencies`, `config_schema`, `initialize()`, and `shutdown()`.

#### Scenario: Plugin instantiation

- GIVEN `ServicePlugin(name="identity", category="archive", version="1.0.0")`
- WHEN `plugin.initialize()` called
- THEN `plugin.name == "identity"` AND `plugin.dependencies` is a list

#### Scenario: Dependency resolution

- GIVEN `MemoryPlugin(dependencies=["identity", "search"])`
- WHEN registered in `ServiceRegistry`
- THEN `registry.get_dependencies("memory")` returns `["identity", "search"]`

### Requirement: ServiceRegistry

`ServiceRegistry` MUST provide `register()`, `get()`, `get_instance()`, `discover()` and use `pkgutil` auto-discovery.

#### Scenario: Registration and retrieval

- GIVEN `IdentityPlugin` registered
- WHEN `registry.get("identity")` called
- THEN returns the registered plugin; `get_instance("identity")` returns initialized instance

#### Scenario: Auto-discovery

- GIVEN plugin modules under `app/services/plugins/`
- WHEN `registry.discover()` called
- THEN all 8 plugin classes found and registered

### Requirement: Archive Plugins (Identity, User, History, Memory, Search)

Five plugins MUST wrap `archive.py` functions with identical signatures: `IdentityPlugin` (identity), `UserPlugin` (user), `HistoryPlugin` (history), `MemoryPlugin` (memories + search + normalize), `SearchPlugin` (search + normalize).

#### Scenario: Archive operation parity

- GIVEN `MemoryPlugin` initialized
- WHEN `plugin.search("keyword")` called
- THEN returns identical results to original `search_archive("keyword")`

#### Scenario: Edge case — missing archive file

- GIVEN `IdentityPlugin` with missing `identity.json`
- WHEN `plugin.get("key")` called
- THEN returns `{}` — identical to original `load_archive` behavior

### Requirement: Voice Plugin

`VoicePlugin` MUST merge `voice.py` and `speaker.py` into one module with `speak(text)` and audio config. Config schema: `{model_size, mic_device, sample_rate, voice_threshold}`.

#### Scenario: TTS output

- GIVEN `VoicePlugin` initialized
- WHEN `plugin.speak("hola")` called
- THEN speech output identical to original `voice.py` + `speaker.py` combined

### Requirement: Planner Plugin

`PlannerPlugin` MUST wrap `planner.py` (`load_plans`, `save_plan`, `query_plans`, `update_plan_time`).

#### Scenario: Plan persistence

- GIVEN `PlannerPlugin` initialized
- WHEN `plugin.save_plan(plan)` then `plugin.query_plans()` called
- THEN returns the saved plan — identical to original `planner.py`

### Requirement: Ollama Plugin

`OllamaPlugin` MUST wrap `ollama_service.py` with input prompt/messages, output LLM response. Config schema: `{model, url}`.

#### Scenario: LLM completion

- GIVEN `OllamaPlugin` with `model="llama3.2:3b"`
- WHEN `plugin.complete(prompt)` called
- THEN returns identical response to original `ollama_service`

### Requirement: Plugin Façade — Zero Behavioral Change

Each plugin MUST expose the same public functions as the original modules. All callers MUST work identically through `services.plugins` façade.

#### Scenario: Callers use identical API

- GIVEN `from services.plugins.identity import get_identity`
- WHEN `get_identity("key")` called
- THEN identical result to original `from services.archive import get_identity`

## MODIFIED Requirements

### Requirement: Services Imports via Façade

All imports MUST route through `app/services/plugins/` instead of direct `services.archive.*` or `services.speaker.*`. Façade re-exports original signatures unchanged.

(Previously: 21 direct `services.archive` imports + 5 `services.speaker` imports)

#### Scenario: Handlers import via façade

- GIVEN `app/brain/handlers.py` imports from `services.plugins.archive`
- WHEN handlers call `get_identity()`, `save_user()`, `search_archive()`
- THEN identical behavior — all direct-import sites routed through façade

## REMOVED Requirements

### Requirement: Direct `archive.py` Internal Imports

Direct `from services.archive import ...` (21 occurrences) MUST be removed.

(Reason: Encapsulate archive internals behind plugin boundary)
(Migration: Façade modules re-export all functions; imports update to `services.plugins.<domain>`)

### Requirement: `speaker.py` Duplicate Module

`services/speaker.py` (24L duplicate of `voice.py` TTS) MUST be removed.

(Reason: Eliminate duplicate TTS implementation)
(Migration: `services.speaker` façade re-exports `VoicePlugin.speak()`)

## Non-Functional Constraints

### Requirement: Zero Behavioral Change and Performance Parity

All plugins MUST produce identical output to monolithic source. p95 latency MUST stay within 5% of baseline; memory overhead < 10MB.

#### Scenario: Regression + benchmark

- GIVEN golden master tests covering all archive/voice/planner/ollama functions
- WHEN pytest runs all tests + 1000 calls through each plugin
- THEN 100% pass rate AND p95 within 5% of baseline

### Requirement: Test Coverage

Suite MUST include `test_plugin_base.py`, `test_registry.py`, one `test_<plugin>.py` per plugin, and `test_regression.py` with parametrized matrix.

#### Scenario: Full coverage

- GIVEN all existing test cases parametrized into `test_regression.py`
- WHEN pytest runs
- THEN identical results; 100% pass rate
