# Exploration: Intent Layer Plugin Architecture Refactor

## Current State

The `IntentLayer` class in `app/brain/intent_layer.py` is a **1230-line monolith** with all 16 intents' patterns hardcoded in a single `_init_patterns()` method. Each intent has a list of `Pattern` objects (EXACT, PHRASE, REGEX, KEYWORD) with weights, boosts, and entity extraction rules. Classification iterates all patterns, scores them, sorts candidates, applies confidence logic, and returns a `ClassifyResult`.

**16 Intents across 8 categories:**
| Category | Intents |
|----------|---------|
| SOCIAL | GREETING, THANKS |
| DECIA_IDENTITY | DECIA_SELF, DECIA_CREATOR |
| USER_IDENTITY | USER_NAME_ASK, USER_NAME_SET, PREFERRED_NAME_ASK, PREFERRED_NAME_SET |
| UTILITY | CALCULATE, TIME, DATE |
| MEMORY | MEMORY_CREATE, MEMORY_SEARCH |
| DECA_ARCHIVE | ARCHIVE_DIRECT, ARCHIVE_SEARCH |
| NAVIGATION | EXIT |
| AMBIGUOUS/CONVERSATION | AMBIGUOUS_INPUT, FREE_TALK, PLANNER_CREATE, PLANNER_QUERY |

**Key behaviors to preserve exactly:**
- Pattern types: EXACT (word_boundary), PHRASE (substring), REGEX (re.search), KEYWORD (with boosts)
- Scoring precedence: EXACT > PHRASE > REGEX > KEYWORD
- 3 confidence tiers: SEGURO (≥0.90), PROBABLE (≥0.70), AMBIGUO (≥0.50)
- Entity extraction for: user_name, preferred_name, memory, math
- Special logic: exit negation ("no salir"), entity-required filtering, short-input (≤2 words) ambiguity handling
- `_archive_keywords` for DECA archive field detection

**Consumer:** `app/brain/core.py` calls `IntentLayer.classify(message)` and routes based on intent + confidence. `_SAFE_INTENTS` set determines high-confidence fast paths. Handlers in `handlers.py` must not change.

**Tests:** `tests/test_intent_layer.py` has 100+ test cases covering all intents, conflicts, entities, confidence, edge cases. Strict TDD required.

---

## Affected Areas

- `app/brain/intent_layer.py` — Primary refactor target (replace with plugin architecture)
- `app/brain/intent_types.py` — May extend Pattern/Candidate/ClassifyResult for plugin metadata
- `app/brain/core.py` — Consumer; must remain unchanged (uses `IntentLayer.classify()`)
- `app/brain/handlers.py` — Unchanged (handler implementations)
- `tests/test_intent_layer.py` — Must pass identically; new plugin tests added
- New: `app/brain/plugins/` — Plugin modules (one per intent or intent group)

---

## Approaches

### 1. **Per-Intent Plugin Module** (Recommended)
Each intent = separate Python module in `app/brain/plugins/` with:
- `patterns: list[Pattern]` — The patterns for this intent
- `entity_group: str | None` — For extraction (user_name, preferred_name, memory, math)
- `priority: int` — Tie-breaker when scores equal (higher = wins)
- Optional: `validate(message, entities) -> bool` — Post-match validation

Registry loads all plugins at startup, builds combined pattern index. Classification logic stays in `IntentLayer` but iterates plugin patterns.

**Pros:**
- Clean separation: each intent self-contained
- Easy to add/remove intents without touching core
- Parallel development possible
- Natural test boundaries (test per plugin)
- Backward compatible: same `IntentLayer.classify()` API

**Cons:**
- Slight startup overhead (plugin discovery)
- Need convention for cross-intent conflicts (e.g., DECIA_CREATOR vs ARCHIVE_DIRECT)
- Priority system adds complexity

**Effort:** Medium

---

### 2. **Pattern Registry with YAML/JSON Config**
Patterns defined in external config files (YAML/JSON), loaded at runtime. Each intent has a config file with patterns, weights, boosts, entity_group.

**Pros:**
- Non-code pattern editing (product can tweak without deploy)
- Clear separation of data vs logic
- Versionable pattern configs

**Cons:**
- Regex in YAML is fragile (escaping hell)
- Loss of Python-type safety for Pattern dataclass
- Complex boost/entity logic hard to express in config
- Still need Python for special logic (PLANNER_CREATE negative lookahead, exit negation)
- More runtime parsing overhead

**Effort:** High (config schema + parser + validation)

---

### 3. **Hybrid: Base Class + Plugin Registry**
Abstract base class `IntentPlugin` with `get_patterns()`, `extract_entities()`, `validate()`. Concrete plugins subclass. Registry discovers subclasses.

**Pros:**
- OOP pattern familiar to team
- Can encapsulate complex logic (PLANNER_CREATE's recall-ban regex) in plugin
- Type-safe

**Cons:**
- More boilerplate per intent
- Over-engineered for simple pattern lists
- Inheritance hierarchy can become rigid

**Effort:** Medium-High

---

## Recommendation

**Approach 1 (Per-Intent Plugin Module)** with a lightweight registry.

**Rationale:**
- Simplest change that achieves the goal
- Preserves all current behavior exactly (patterns stay as Python code)
- Minimal core changes: `IntentLayer` becomes a thin orchestrator
- Test strategy: keep existing tests + add plugin contract tests
- Zero risk to `core.py` and handlers

---

## Proposed Plugin Interface

```python
# app/brain/plugins/base.py
from dataclasses import dataclass
from brain.intent_types import Pattern, Candidate, ClassifyResult

@dataclass
class IntentPlugin:
    """Self-contained intent definition."""
    name: str                          # e.g., "GREETING"
    category: str                      # e.g., "SOCIAL"
    patterns: list[Pattern]            # Patterns for this intent
    entity_group: str | None = None    # "user_name" | "preferred_name" | "memory" | "math"
    priority: int = 0                  # Tie-breaker (higher wins)
    
    # Optional post-match validation (e.g., PLANNER_CREATE recall-ban)
    def validate(self, message: str, entities: dict) -> bool:
        return True

# app/brain/plugins/registry.py
class PluginRegistry:
    def __init__(self):
        self._plugins: dict[str, IntentPlugin] = {}
        self._all_patterns: dict[str, list[Pattern]] = {}  # intent -> patterns
    
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

**Example plugin (`app/brain/plugins/greeting.py`):**
```python
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
    priority=10,  # High priority for common intents
)
```

**Modified `IntentLayer` (minimal changes):**
```python
class IntentLayer:
    def __init__(self):
        from brain.plugins.registry import PluginRegistry
        self._registry = PluginRegistry()
        self._load_plugins()  # Discovers and registers all plugins
        self._archive_keywords = {...}  # Unchanged
    
    def _load_plugins(self):
        # Import all plugin modules, register their `plugin` instance
        from brain.plugins import greeting, thanks, decia_self, ...
        for mod in [greeting, thanks, decia_self, ...]:
            self._registry.register(mod.plugin)
    
    def classify(self, message):
        # Same logic, but iterates self._registry.get_all_patterns()
        # Uses self._registry.validate_match() for post-match validation
        ...
```

---

## Migration Strategy (Phased, Backward-Compatible)

### Phase 0: Test Baseline (Week 0)
- Run full test suite, capture baseline pass/fail
- Add plugin contract tests: `tests/plugins/test_plugin_base.py`
- Document all 16 intents' patterns in a reference matrix

### Phase 1: Plugin Infrastructure (Week 1)
- Create `app/brain/plugins/` package with `base.py`, `registry.py`, `__init__.py`
- Implement `PluginRegistry` with discovery/registration
- Write tests for registry: discovery, priority ordering, validation hook
- **No changes to `IntentLayer` yet**

### Phase 2: Extract Intent Plugins (Week 2-3)
**One intent at a time, TDD per intent:**
1. Create plugin module (e.g., `plugins/greeting.py`)
2. Copy patterns verbatim from `intent_layer.py`
3. Add plugin test: `tests/plugins/test_greeting.py` (pattern count, weights, entities)
4. Register in registry
5. Run full test suite — must pass identically
6. Delete patterns from `intent_layer._init_patterns()`
7. Repeat for all 16 intents

**Order (low-risk first):** GREETING, THANKS, EXIT, CALCULATE, TIME, DATE → DECIA_SELF, DECIA_CREATOR → USER_NAME_ASK/SET, PREFERRED_NAME_ASK/SET → MEMORY_CREATE, MEMORY_SEARCH → ARCHIVE_DIRECT, ARCHIVE_SEARCH → PLANNER_CREATE, PLANNER_QUERY → AMBIGUOUS_INPUT, FREE_TALK (fallback)

### Phase 3: Special Logic Extraction (Week 3)
- Move `_PLANNER_RECALL_BANNED`, `_PLANNER_MARKER_SRC`, `_PLANNER_QUERY_WORDS_EXCLUDED` to `plugins/planner_create.py` as module constants
- Implement `validate()` in `PLANNER_CREATE` plugin for recall-ban logic
- Move `_has_exit_negation()` to `plugins/exit.py` as `validate()`
- Move `_extract_archive_field()` to `plugins/archive_search.py` or keep in `IntentLayer` (shared)

### Phase 4: Cleanup & Optimization (Week 4)
- Remove `_init_patterns()` entirely from `IntentLayer`
- `IntentLayer` becomes thin orchestrator (~200 lines)
- Add plugin discovery auto-import (pkgutil/walk_packages)
- Performance benchmark: ensure classification latency unchanged
- Update docs

### Phase 5: Verification (Week 4)
- Full test suite passes
- Run `test_intent_stress.py` for performance
- Manual smoke test with real queries
- Archive delta spec

---

## Test Strategy for Classification Correctness

### 1. **Golden Master Tests (Existing)**
- All 100+ tests in `test_intent_layer.py` must pass unchanged
- These are the source of truth for behavior

### 2. **Plugin Contract Tests (New)**
Per plugin: `tests/plugins/test_<intent>.py`
```python
def test_greeting_plugin_patterns():
    from brain.plugins.greeting import plugin
    assert plugin.name == GREETING
    assert len(plugin.patterns) == 5
    assert plugin.patterns[0].type == EXACT
    assert plugin.patterns[0].value == "hola"
    assert plugin.patterns[0].weight == 100
    assert plugin.entity_group is None
    assert plugin.priority == 10

def test_greeting_plugin_classification():
    il = IntentLayer()
    r = il.classify("hola")
    assert r.intent == GREETING
    assert r.confidence >= 0.90
```

### 3. **Registry Tests (New)**
- `tests/plugins/test_registry.py`: discovery, priority ordering, validation hook
- Cross-intent conflict resolution (priority wins)

### 4. **Regression Tests (New)**
- `tests/plugins/test_regression.py`: parametrized matrix of all test cases from `test_intent_layer.py` run against new implementation
- Property-based: for each test case, old and new implementation produce identical `ClassifyResult`

### 5. **Stress/Performance Tests**
- Reuse `test_intent_stress.py` — ensure no latency regression

---

## Risks and Tradeoffs

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| **Behavioral drift** — subtle scoring changes | Medium | High | Golden master tests + regression matrix; run old and new in parallel during Phase 2 |
| **Plugin discovery fails in packaged env** | Low | Medium | Explicit imports in Phase 2; auto-discovery only in Phase 4 with fallback |
| **Cross-intent priority conflicts** | Medium | Medium | Explicit priority per plugin; document conflict resolution rules; test conflicts |
| **PLANNER_CREATE recall-ban logic breaks** | Medium | High | Extract to plugin.validate(); add specific test cases for banned phrases |
| **Exit negation logic breaks** | Low | High | Move to exit plugin validate(); test "no salir", "no quiero salir" |
| **Startup latency increase** | Low | Low | Lazy load plugins; benchmark; 16 plugins is trivial |
| **Circular imports** | Low | Medium | Keep plugins leaf modules (no imports from brain.* except intent_types) |

**Tradeoffs:**
- **Pro:** Clean architecture, testable, extensible, parallelizable
- **Con:** More files (16 plugin modules + registry), slight indirection
- **Con:** Priority system adds implicit coupling (document well)
- **Neutral:** No runtime config — patterns stay in Python (type-safe, testable)

---

## Effort Estimate

| Phase | Tasks | Estimate |
|-------|-------|----------|
| Phase 0: Test Baseline | Baseline capture, contract test scaffolding | 0.5 days |
| Phase 1: Plugin Infrastructure | Registry, base, discovery, tests | 1 day |
| Phase 2: Extract 16 Plugins | 16 intents × (create plugin + test + verify) | 4-5 days |
| Phase 3: Special Logic | PLANNER_CREATE, EXIT, archive keywords | 1 day |
| Phase 4: Cleanup | Remove _init_patterns, auto-discovery, benchmark | 1 day |
| Phase 5: Verification | Full suite, stress, smoke, archive | 0.5 days |
| **Total** | | **~8-9 days** |

**Parallelizable:** Phase 2 intents can be done in parallel by multiple developers (each intent independent).

---

## Ready for Proposal

**Yes.** The exploration is complete with:
- Concrete pain points from code analysis
- Clear plugin interface design
- Phased migration with zero-breaking-change guarantee
- Test strategy preserving 100% behavioral compatibility
- Risk assessment with mitigations
- Realistic effort estimate

**Next step:** Orchestrator should present this to user for approval, then launch `sdd-propose` with this exploration as input.