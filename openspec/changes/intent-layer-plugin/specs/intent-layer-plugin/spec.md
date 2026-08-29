# Delta for Intent Layer Plugin Architecture

## ADDED Requirements

### Requirement: Plugin Infrastructure — Base and Registry

The system MUST provide `IntentPlugin` dataclass and `PluginRegistry` in `app/brain/plugins/`. Each intent module MUST export a `plugin` instance. Registry MUST support `register()`, `get_patterns()`, `get_all_patterns()`, `get_plugin()`, and `validate_match()`.

#### Scenario: Plugin registration

- GIVEN a plugin with `name=GREETING`, `patterns=[...]`, `priority=10`
- WHEN `registry.register(plugin)` is called
- THEN `registry.get_plugin("GREETING")` returns that plugin AND `registry.get_patterns("GREETING")` returns its patterns

#### Scenario: Priority-based conflict resolution

- GIVEN two intents with equal classification scores
- WHEN `IntentLayer.classify()` resolves the tie
- THEN the intent with higher `plugin.priority` wins; ties broken by score descending

### Requirement: Per-Intent Plugin Modules

16 self-contained modules MUST exist under `app/brain/plugins/`: `greeting.py`, `thanks.py`, `decia_self.py`, `decia_creator.py`, `user_name_ask.py`, `user_name_set.py`, `preferred_name_ask.py`, `preferred_name_set.py`, `calculate.py`, `time.py`, `date.py`, `memory_create.py`, `memory_search.py`, `archive_direct.py`, `archive_search.py`, `exit.py`, `ambiguous_input.py`, `free_talk.py`, `planner_create.py`, `planner_query.py`.

Each module MUST export `plugin` with `name`, `category`, `patterns`, `entity_group`, `priority`, and optional `validate()`.

#### Scenario: Pattern fidelity per plugin

- GIVEN `from brain.plugins.greeting import plugin`
- WHEN `len(plugin.patterns)` and `plugin.patterns[0].type == EXACT` and `plugin.patterns[0].value == "hola"` and `plugin.patterns[0].weight == 100`
- THEN all patterns match `intent_layer.py` verbatim; `plugin.entity_group is None`; `plugin.priority == 10`

### Requirement: Special Logic Extraction

`_PLANNER_RECALL_BANNED` MUST be moved to `plugins/planner_create.py` as module constant; `PLANNER_CREATE.validate()` MUST return False for banned phrases. `_has_exit_negation()` MUST be moved to `plugins/exit.py` as `validate()`. `_archive_keywords` MUST remain accessible to `archive_search` plugin.

#### Scenario: PLANNER_CREATE recall-ban validation

- GIVEN message contains "algo de memoria"
- WHEN `plugin.validate(message, entities)` is called on PLANNER_CREATE plugin
- THEN validate returns False; PLANNER_CREATE score becomes 0; MEMORY_SEARCH preserved

#### Scenario: Exit negation validation

- GIVEN "no quiero salir"
- WHEN `plugin.validate(message, entities)` is called on EXIT plugin
- THEN validate returns False; EXIT score becomes 0; result.intent != EXIT

### Requirement: IntentLayer Orchestrator Refactor

`IntentLayer.__init__()` MUST create `PluginRegistry`, call `_load_plugins()`, and preserve `_archive_keywords`. `_init_patterns()` MUST be removed. `classify(message)` MUST iterate `self._registry.get_all_patterns()` and call `self._registry.validate_match()`.

#### Scenario: Classification via registry

- GIVEN `IntentLayer()` with all 16 plugins loaded
- WHEN `classify("hola")` called
- THEN result.intent == GREETING, confidence >= 0.90 — identical to monolithic behavior

### Requirement: Plugin Contract Tests

New test suite `tests/plugins/` MUST contain `test_plugin_base.py`, `test_registry.py`, one `test_<intent>.py` per intent, and `test_regression.py` with parametrized matrix of all `test_intent_layer.py` cases.

#### Scenario: Regression matrix passes

- GIVEN every test case from `test_intent_layer.py` parametrized into `test_regression.py`
- WHEN pytest runs both suites
- THEN identical `ClassifyResult` for every case; 100% pass rate

### Requirement: Non-Functional Constraints

Classification latency MUST stay within 5% of baseline p95. Plugin memory overhead MUST stay under 10MB.

#### Scenario: Stress test parity

- GIVEN 1000 messages classified with all plugins loaded
- WHEN p95 latency measured
- THEN within 5% of monolithic baseline AND memory delta < 10MB

## MODIFIED Requirements

### Requirement: Pattern Classification — All 16 Intents

All 16 intents MUST classify identically to the monolithic `IntentLayer._init_patterns()`. Patterns are now sourced from `PluginRegistry.get_all_patterns()` instead of `self._patterns`. Scoring precedence EXACT > PHRASE > REGEX > KEYWORD, confidence tiers (SEGURO ≥0.90, PROBABLE ≥0.70, AMBIGUO ≥0.50), and `_calc_confidence()` logic MUST be preserved exactly.

(Previously: patterns stored in monolithic `self._patterns` dict inside `IntentLayer._init_patterns()`)

#### Scenario: High-confidence safe intent routing

- GIVEN a message matching GREETING, THANKS, EXIT, CALCULATE, TIME, DATE, DECIA_SELF, DECIA_CREATOR, or ARCHIVE_DIRECT
- WHEN classify(message) is called
- THEN result.intent in _SAFE_INTENTS AND result.confidence >= 0.90

#### Scenario: Below-threshold fallback chain

- GIVEN no pattern matches above threshold
- WHEN candidates evaluated
- AND word_count <= 2 THEN intent = AMBIGUOUS_INPUT, confidence >= 0.50
- AND word_count > 2 THEN intent = FREE_TALK, confidence = 0.0

#### Scenario: Confidence boundaries

- GIVEN "hola" (exact weight 100) THEN confidence >= 0.90
- AND WHEN best_score < 50, word_count > 2 THEN intent = FREE_TALK, confidence < 0.50

#### Scenario: Priority ordering

- GIVEN multiple candidates with equal scores
- WHEN sorted, higher-priority intent wins; else score descending

### Requirement: Public API Invariant

`IntentLayer.classify(message)` signature, `ClassifyResult(intent, confidence, entities, matched_pattern, candidates)`, and all `Pattern`, `Candidate` fields MUST be unchanged. `core.py` and `handlers.py` MUST NOT be modified.

(Previously: `IntentLayer` was a 1230-line monolith; public API was the only contract)

#### Scenario: API compatibility

- GIVEN any call to classify(message)
- THEN return type and fields identical to monolithic implementation

## REMOVED Requirements

### Requirement: Monolithic `_init_patterns()` Pattern Loading

The `IntentLayer._init_patterns()` method (1230 lines, all 16 intents hardcoded) is removed. Patterns are now distributed across plugin modules.

(Reason: Refactor goal — replace monolith with plugin architecture)
(Migration: Patterns preserved verbatim in `app/brain/plugins/<intent>.py`; registry loads them at startup)

## RENAMED Requirements

### Requirement: IntentLayer Internal Storage → Plugin Registry

`IntentLayer._patterns` dict is replaced by `IntentLayer._registry` (PluginRegistry instance). Internal method `_init_patterns()` is replaced by `_load_plugins()`.

(Reason: Architecture change — pattern storage moves from monolithic dict to registry)
(Migration: `self._patterns` references replaced by `self._registry.get_all_patterns()` in classify logic; `_archive_keywords` remains unchanged)

## Contracts (Interfaces That MUST NOT Change)

| Contract | Type | Status |
|----------|------|--------|
| `IntentLayer.classify(message)` | Public method | Frozen |
| `ClassifyResult(intent, confidence, entities, matched_pattern, candidates)` | Dataclass | Frozen |
| `Pattern(type, value, weight, boosts, entity_group, word_boundary)` | Dataclass | Frozen |
| `Candidate(intent, score, matched_pattern, matched_type, entities)` | Dataclass | Frozen |
| `core.py` routing logic | Consumer | Frozen |
| `handlers.py` implementations | Consumer | Frozen |
| `_SAFE_INTENTS` set | Constant | Frozen |
| `_calc_confidence(best, second, n)` | Internal logic | Frozen |
| `_extract_archive_field()` | Internal logic | Frozen |

## Non-Goals

- Changing classification behavior, scoring, or confidence tiers
- Modifying `handlers.py` or `core.py` routing logic
- Adding new intent types or pattern types
- Runtime config (YAML/JSON) — patterns stay in Python
- Auto-discovery in Phase 2 (explicit imports first; auto in Phase 4)
- Behavior changes of any kind — golden master tests are authoritative

## Acceptance Criteria

- [ ] All 100+ existing tests in `test_intent_layer.py` pass identically
- [ ] All 16 plugin contract tests pass
- [ ] Registry tests cover discovery, priority ordering, validation hook
- [ ] Regression matrix produces identical `ClassifyResult` for every test case
- [ ] Classification p95 latency within 5% of baseline
- [ ] Memory overhead < 10MB
- [ ] `core.py` and `handlers.py` unchanged (git diff empty)
- [ ] `IntentLayer` reduced to ~200 lines (thin orchestrator)
- [ ] `_init_patterns()` fully removed from `IntentLayer`
