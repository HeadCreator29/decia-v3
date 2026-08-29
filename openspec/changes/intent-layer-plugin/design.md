# Design: Intent Layer Plugin Architecture

## Technical Approach

Refactor the 1230-line monolithic `IntentLayer` into a plugin/registry architecture with 16 self-contained intent modules under `app/brain/plugins/`. The `IntentLayer` becomes a thin orchestrator (~200 lines) that delegates pattern storage to `PluginRegistry`, preserves all scoring/confidence/entity logic unchanged, and maintains identical public API (`classify()`, `ClassifyResult`, `Pattern`, `Candidate`). Migration follows 5 phases with zero behavioral change guarantee via golden master tests.

## Architecture Decisions

### Decision: Plugin Interface — Dataclass over Base Class

| Option | Tradeoff | Decision |
|--------|----------|----------|
| Abstract base class `IntentPlugin` with `get_patterns()`, `validate()` | More boilerplate; rigid inheritance | ❌ Rejected |
| **Dataclass `IntentPlugin` with optional `validate()` method** | Minimal boilerplate; patterns as data; validation as optional hook | ✅ Chosen |
| External config (YAML/JSON) | Regex escaping issues; loss of type safety; special logic still needs Python | ❌ Rejected |

**Rationale**: Simplest change achieving the goal. Patterns stay as Python code (type-safe, testable). Validation is an optional method on the dataclass, not forced inheritance.

### Decision: Registry Design — Eager Registration with Explicit Imports (Phase 2), Auto-Discovery (Phase 4)

| Option | Tradeoff | Decision |
|--------|----------|----------|
| Auto-discovery via `pkgutil` from Day 1 | Risk in packaged envs; harder to debug | ❌ Phase 2 |
| **Explicit imports in `_load_plugins()`** | More verbose; zero discovery failures | ✅ Phase 2 |
| Auto-discovery with explicit fallback | Best of both; slightly more code | ✅ Phase 4 |

**Rationale**: Phase 2 uses explicit imports for reliability. Phase 4 adds `pkgutil.walk_packages()` auto-discovery with graceful fallback to explicit list.

### Decision: Special Logic Extraction — Per-Plugin `validate()` Hooks

| Logic | Source | Destination | Mechanism |
|-------|--------|-------------|-----------|
| `_PLANNER_RECALL_BANNED` + negative lookahead | `intent_layer.py` module constants | `plugins/planner_create.py` module constants | `PLANNER_CREATE.validate()` returns False for banned phrases |
| `_has_exit_negation()` | `IntentLayer._has_exit_negation()` | `plugins/exit.py` | `EXIT.validate()` returns False on "no salir" |
| `_extract_archive_field()` | `IntentLayer._extract_archive_field()` | `plugins/archive_search.py` (shared utility) or keep in `IntentLayer` | Keep in `IntentLayer` (used by ARCHIVE_DIRECT/SEARCH); not plugin-specific |

**Rationale**: Validation hooks belong to the intent they gate. Archive field extraction is shared across ARCHIVE intents, stays in orchestrator.

### Decision: Priority System — Integer Tie-Breaker

| Option | Tradeoff | Decision |
|--------|----------|----------|
| No priority (score only) | Can't resolve equal-score conflicts deterministically | ❌ Rejected |
| **Integer `priority` on `IntentPlugin` (higher wins)** | Simple; explicit; documented per plugin | ✅ Chosen |
| Complex conflict rules per category | Over-engineered; implicit coupling | ❌ Rejected |

**Rationale**: Priority is a single integer per plugin. Default 0. High-priority intents (GREETING, EXIT, THANKS) get 10. Documented in each plugin. Sort key: `(-score, -priority)`.

### Decision: Thread Safety — Not Required

| Option | Tradeoff | Decision |
|--------|----------|----------|
| Thread-safe registry (locks) | Unnecessary overhead; single-threaded classification | ❌ Rejected |
| **Non-thread-safe, initialized once at startup** | Simpler; matches usage pattern | ✅ Chosen |

**Rationale**: `IntentLayer` instantiated once at app startup. Registry populated once. No concurrent registration/classification.

## Data Flow

```
User Message
     │
     ▼
normalize_strict(message)  ──► normalized string
     │
     ▼
PluginRegistry.get_all_patterns()
     │                    │
     │         { GREETING: [Pattern, ...],
     │           THANKS:   [Pattern, ...],
     │           ... 16 intents total }
     ▼
For each intent: score all patterns → best_score
     │
     ▼
Build Candidate(intent, score, matched_pattern, matched_type, entities)
     │
     ▼
Filter: entity-required intents (USER_NAME_SET, PREFERRED_NAME_SET, MEMORY_CREATE)
         must have extracted entity → else score = 0
     │
     ▼
PluginRegistry.validate_match(intent, message, entities)
         ├─ EXIT plugin: validate() checks "no salir" negation
         ├─ PLANNER_CREATE plugin: validate() checks recall-ban regex
         └─ Others: default True
     │
     ▼
Filter: score > 0
     │
     ▼
Sort candidates by (-score, -priority)
     │
     ▼
Confidence calculation (_calc_confidence: best_score, second_score, n_candidates)
     │
     ▼
Threshold logic:
   ├─ best.score < 50 & word_count ≤ 2 → AMBIGUOUS_INPUT (confidence ≥ 0.80)
   ├─ best.score < 50 & word_count > 2 → FREE_TALK (confidence = 0.0)
   └─ else → best.intent with calculated confidence
     │
     ▼
ClassifyResult(intent, confidence, entities, matched_pattern, candidates)
```

## File Changes

| File | Action | Description |
|------|--------|-------------|
| `app/brain/plugins/__init__.py` | Create | Package init; exports `IntentPlugin`, `PluginRegistry`, plugin list for explicit imports |
| `app/brain/plugins/base.py` | Create | `IntentPlugin` dataclass (name, category, patterns, entity_group, priority, validate()) |
| `app/brain/plugins/registry.py` | Create | `PluginRegistry` class (register, get_patterns, get_all_patterns, get_plugin, validate_match) |
| `app/brain/plugins/greeting.py` | Create | GREETING plugin (5 patterns, priority=10, entity_group=None) |
| `app/brain/plugins/thanks.py` | Create | THANKS plugin (4 patterns, priority=10) |
| `app/brain/plugins/decia_self.py` | Create | DECIA_SELF plugin (17 patterns, priority=5) |
| `app/brain/plugins/decia_creator.py` | Create | DECIA_CREATOR plugin (14 patterns, priority=5) |
| `app/brain/plugins/user_name_ask.py` | Create | USER_NAME_ASK plugin (11 patterns, priority=5) |
| `app/brain/plugins/preferred_name_ask.py` | Create | PREFERRED_NAME_ASK plugin (4 patterns, priority=5) |
| `app/brain/plugins/user_name_set.py` | Create | USER_NAME_SET plugin (7 REGEX patterns, entity_group="user_name", priority=5) |
| `app/brain/plugins/preferred_name_set.py` | Create | PREFERRED_NAME_SET plugin (7 REGEX patterns, entity_group="preferred_name", priority=5) |
| `app/brain/plugins/calculate.py` | Create | CALCULATE plugin (5 REGEX patterns, entity_group="math", priority=5) |
| `app/brain/plugins/time.py` | Create | TIME plugin (11 patterns, priority=10) |
| `app/brain/plugins/date.py` | Create | DATE plugin (14 patterns, priority=10) |
| `app/brain/plugins/memory_create.py` | Create | MEMORY_CREATE plugin (9 PHRASE patterns, entity_group="memory", priority=5) |
| `app/brain/plugins/memory_search.py` | Create | MEMORY_SEARCH plugin (28 patterns, entity_group="memory", priority=5) |
| `app/brain/plugins/archive_direct.py` | Create | ARCHIVE_DIRECT plugin (18 patterns, priority=5) |
| `app/brain/plugins/archive_search.py` | Create | ARCHIVE_SEARCH plugin (24 patterns, priority=5) |
| `app/brain/plugins/exit.py` | Create | EXIT plugin (11 patterns, priority=10, validate() for negation) |
| `app/brain/plugins/ambiguous_input.py` | Create | AMBIGUOUS_INPUT plugin (empty patterns, fallback, priority=0) |
| `app/brain/plugins/free_talk.py` | Create | FREE_TALK plugin (empty patterns, fallback, priority=0) |
| `app/brain/plugins/planner_create.py` | Create | PLANNER_CREATE plugin (3 REGEX patterns, priority=5, validate() for recall-ban, module constants `_PLANNER_RECALL_BANNED`, `_PLANNER_MARKER_SRC`, `_PLANNER_QUERY_WORDS_EXCLUDED`) |
| `app/brain/plugins/planner_query.py` | Create | PLANNER_QUERY plugin (6 REGEX patterns, priority=5) |
| `app/brain/intent_layer.py` | Modify | Remove `_init_patterns()`; add `_registry`, `_load_plugins()`; `classify()` uses registry; ~200 lines |
| `tests/plugins/test_plugin_base.py` | Create | Contract tests for `IntentPlugin` dataclass |
| `tests/plugins/test_registry.py` | Create | Registry tests: registration, discovery, priority ordering, validation hook |
| `tests/plugins/test_<intent>.py` (16 files) | Create | Per-intent contract tests: pattern count, weights, entity_group, priority, classification |
| `tests/plugins/test_regression.py` | Create | Parametrized matrix of all `test_intent_layer.py` cases |

## Interfaces / Contracts

### IntentPlugin Dataclass

```python
# app/brain/plugins/base.py
from dataclasses import dataclass
from brain.intent_types import Pattern

@dataclass
class IntentPlugin:
    name: str                          # e.g., "GREETING"
    category: str                      # e.g., "SOCIAL"
    patterns: list[Pattern]            # Patterns for this intent
    entity_group: str | None = None    # "user_name" | "preferred_name" | "memory" | "math"
    priority: int = 0                  # Tie-breaker (higher wins)

    def validate(self, message: str, entities: dict) -> bool:
        return True
```

### PluginRegistry Class

```python
# app/brain/plugins/registry.py
from brain.plugins.base import IntentPlugin
from brain.intent_types import Pattern

class PluginRegistry:
    def __init__(self):
        self._plugins: dict[str, IntentPlugin] = {}
        self._all_patterns: dict[str, list[Pattern]] = {}

    def register(self, plugin: IntentPlugin) -> None:
        self._plugins[plugin.name] = plugin
        self._all_patterns[plugin.name] = plugin.patterns

    def get_patterns(self, intent: str) -> list[Pattern]:
        return self._all_patterns.get(intent, [])

    def get_all_patterns(self) -> dict[str, list[Pattern]]:
        return self._all_patterns

    def get_plugin(self, intent: str) -> IntentPlugin | None:
        return self._plugins.get(intent)

    def validate_match(self, intent: str, message: str, entities: dict) -> bool:
        plugin = self._plugins.get(intent)
        return plugin.validate(message, entities) if plugin else True
```

### Example Plugin Module

```python
# app/brain/plugins/greeting.py
from brain.intent_types import Pattern, EXACT, PHRASE, GREETING
from brain.plugins.base import IntentPlugin

plugin = IntentPlugin(
    name=GREETING,
    category="SOCIAL",
    patterns=[
        Pattern(EXACT, "hola", 100, word_boundary=True),
        Pattern(PHRASE, "buenos dias", 95, {"buenos": 5}),
        Pattern(PHRASE, "buenas tardes", 95, {"buenas": 5}),
        Pattern(PHRASE, "buenas noches", 95, {"buenas": 5}),
        Pattern(PHRASE, "buenas", 90),
    ],
    priority=10,
)
```

### Modified IntentLayer (Orchestrator)

```python
# app/brain/intent_layer.py (simplified)
class IntentLayer:
    def __init__(self):
        from brain.plugins.registry import PluginRegistry
        self._registry = PluginRegistry()
        self._load_plugins()
        self._archive_keywords = {...}  # Unchanged

    def _load_plugins(self):
        # Phase 2: explicit imports
        from brain.plugins import (
            greeting, thanks, decia_self, decia_creator,
            user_name_ask, preferred_name_ask, user_name_set,
            preferred_name_set, calculate, time, date,
            memory_create, memory_search, archive_direct,
            archive_search, exit, ambiguous_input, free_talk,
            planner_create, planner_query
        )
        for mod in [greeting, thanks, decia_self, decia_creator,
                    user_name_ask, preferred_name_ask, user_name_set,
                    preferred_name_set, calculate, time, date,
                    memory_create, memory_search, archive_direct,
                    archive_search, exit, ambiguous_input, free_talk,
                    planner_create, planner_query]:
            self._registry.register(mod.plugin)

    def classify(self, message):
        # Same logic, but iterates self._registry.get_all_patterns()
        # Uses self._registry.validate_match() for post-match validation
        ...
```

## Testing Strategy

| Layer | What to Test | Approach |
|-------|--------------|----------|
| **Unit: Plugin Contract** | Each plugin exports correct `name`, `category`, `patterns` count, weights, `entity_group`, `priority` | `tests/plugins/test_<intent>.py` — direct import assertions |
| **Unit: Registry** | Registration, `get_all_patterns()`, `get_plugin()`, `validate_match()` default/override | `tests/plugins/test_registry.py` — mock plugins, priority sort verification |
| **Unit: Special Logic** | `EXIT.validate("no quiero salir", {})` → False; `PLANNER_CREATE.validate("algo de memoria", {})` → False | `tests/plugins/test_exit.py`, `test_planner_create.py` |
| **Integration: Classification** | Full `IntentLayer.classify()` produces identical `ClassifyResult` for all 100+ existing test cases | `tests/plugins/test_regression.py` — parametrized matrix from `test_intent_layer.py` |
| **Integration: Golden Master** | All existing `tests/test_intent_layer.py` pass unchanged | Run existing test suite as-is |
| **Performance: Stress** | 1000 messages classified; p95 latency within 5% of baseline; memory delta < 10MB | `tests/test_intent_stress.py` (existing) + new benchmark |

## Threat Matrix

N/A — no routing, shell, subprocess, VCS/PR automation, executable-file classification, or process-integration boundary.

## Migration / Rollout

**Phase 0: Test Baseline** (0.5 days)
- Run full test suite, capture baseline
- Add `tests/plugins/test_plugin_base.py` scaffolding
- Document all 16 intents' patterns in reference matrix

**Phase 1: Plugin Infrastructure** (1 day)
- Create `app/brain/plugins/` with `base.py`, `registry.py`, `__init__.py`
- Implement `PluginRegistry` with explicit registration
- Write registry tests
- **No changes to `IntentLayer` yet**

**Phase 2: Extract Intent Plugins** (4-5 days)
One intent at a time, TDD per intent:
1. Create plugin module (e.g., `plugins/greeting.py`)
2. Copy patterns verbatim from `intent_layer.py`
3. Add plugin test: `tests/plugins/test_greeting.py`
4. Register in registry
5. Run full test suite — must pass identically
6. Delete patterns from `intent_layer._init_patterns()`
7. Repeat for all 16 intents

Order (low-risk first): GREETING, THANKS, EXIT, CALCULATE, TIME, DATE → DECIA_SELF, DECIA_CREATOR → USER_NAME_ASK/SET, PREFERRED_NAME_ASK/SET → MEMORY_CREATE, MEMORY_SEARCH → ARCHIVE_DIRECT, ARCHIVE_SEARCH → PLANNER_CREATE, PLANNER_QUERY → AMBIGUOUS_INPUT, FREE_TALK

**Phase 3: Special Logic Extraction** (1 day)
- Move `_PLANNER_RECALL_BANNED`, `_PLANNER_MARKER_SRC`, `_PLANNER_QUERY_WORDS_EXCLUDED` to `plugins/planner_create.py`
- Implement `PLANNER_CREATE.validate()` for recall-ban
- Move `_has_exit_negation()` to `plugins/exit.py` as `validate()`
- `_extract_archive_field()` stays in `IntentLayer` (shared by ARCHIVE_DIRECT/SEARCH)

**Phase 4: Cleanup & Optimization** (1 day)
- Remove `_init_patterns()` entirely from `IntentLayer`
- `IntentLayer` becomes thin orchestrator (~200 lines)
- Add auto-discovery with `pkgutil.walk_packages()` + explicit fallback
- Performance benchmark

**Phase 5: Verification** (0.5 days)
- Full test suite passes
- Run stress test for performance
- Manual smoke test
- Archive delta spec

### Rollback Plan

If issues arise at any phase:
- `git revert` on `app/brain/intent_layer.py` restores monolith
- Plugin modules under `app/brain/plugins/` remain but are unused
- Zero risk to `core.py`, `handlers.py`, or `intent_types.py`

## Open Questions

- [ ] Should `AMBIGUOUS_INPUT` and `FREE_TALK` plugins have empty pattern lists or be handled as special cases in orchestrator? (Exploration suggests empty lists; current monolith has empty list for FREE_TALK)
- [ ] Confirm priority values for all 16 plugins — exploration only shows examples (GREETING=10, EXIT=10). Need explicit priority per intent for deterministic tie-breaking.
- [ ] Auto-discovery in Phase 4: use `pkgutil.iter_modules()` or `importlib.metadata` entry points? (pkgutil simpler, no setuptools dependency)

---

**Design complete.** Ready for `sdd-tasks` phase.