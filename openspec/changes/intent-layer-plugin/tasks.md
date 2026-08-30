# Tasks: Intent Layer Plugin Architecture Refactor

## Review Workload Forecast

| Field | Value |
|-------|-------|
| Estimated changed lines | 800 |
| 400-line budget risk | High |
| Chained PRs recommended | Yes |
| Suggested split | 5 chained PRs (infrastructure → 4 plugin groups → verification) |
| Delivery strategy | auto-chain |
| Chain strategy | feature-branch-chain |
| Decision needed before apply | No |

Decision needed before apply: No
Chained PRs recommended: Yes
Chain strategy: feature-branch-chain
400-line budget risk: High

### Suggested Work Units

| Unit | Goal | Likely PR | Focused test command | Runtime harness | Rollback boundary |
|------|------|-----------|----------------------|-----------------|-------------------|
| 1 | Create plugin package infrastructure (base, registry, __init__.py) | PR 1 (tracker) | `python -m pytest tests/plugins/test_plugin_base.py -v` | Import `IntentLayer` and verify it loads without error | Revert `app/brain/plugins/`; `IntentLayer` reverts to monolith |
| 2 | Extract GREETING + THANKS plugins + registry tests | PR 2 (base=PR1) | `python -m pytest tests/plugins/test_greeting.py tests/plugins/test_thanks.py tests/plugins/test_registry.py -v` | `IntentLayer.classify("hola")` returns GREETING; `IntentLayer.classify("gracias")` returns THANKS | Revert PR1 + PR2 plugin modules; run existing test_intent_layer.py to confirm parity |
| 3 | Extract remaining 14 plugins (DECIA_SELF, DECIA_CREATOR, USER_NAME_ASK, PREFERRED_NAME_ASK, USER_NAME_SET, PREFERRED_NAME_SET, CALCULATE, TIME, DATE, MEMORY_CREATE, MEMORY_SEARCH, ARCHIVE_DIRECT, ARCHIVE_SEARCH) | PR 3-4 (batched groups) | Per-intent: `python -m pytest tests/plugins/test_<intent>.py -v` | Full `IntentLayer.classify()` for each intent matches golden master | Revert all plugin modules; `test_intent_layer.py` passes on monolith |
| 4 | Extract special logic: PLANNER_CREATE validate(), EXIT validate() | PR 5 (base=PR4) | `python -m pytest tests/plugins/test_planner_create.py tests/plugins/test_exit.py -v` | `PLANNER_CREATE.validate("banned phrase", {})` → False; `EXIT.validate("no salir", {})` → False | Revert validate() hooks; archive field extraction and core logic unchanged |
| 5 | Cleanup: remove _init_patterns(), add auto-discovery, benchmark; full verification | PR 6 (base=PR5) | `python -m pytest tests/test_intent_layer.py -v` + `python -m pytest tests/test_intent_stress.py -v` | Classify latency within 5% of baseline; all 100+ tests pass unchanged | Revert `intent_layer.py` to monolith; all plugin modules unused but present |

## Phase 1: Foundation / Infrastructure

- [x] 1.1 Create `app/brain/plugins/` package directory with `__init__.py`; export `IntentPlugin`, `PluginRegistry`
- [x] 1.2 Create `app/brain/plugins/base.py`: `IntentPlugin` dataclass with `name`, `category`, `patterns`, `entity_group`, `priority`, optional `validate()` method
- [x] 1.3 Create `app/brain/plugins/registry.py`: `PluginRegistry` class with `register()`, `get_patterns()`, `get_all_patterns()`, `get_plugin()`, `validate_match()` — default `validate()` returns True
- [x] 1.4 Write `tests/plugins/test_plugin_base.py`: contract assertions for `name`, `category`, `patterns` count/weights/`entity_group`/`priority`; default `validate()`
- [x] 1.5 Write `tests/plugins/test_registry.py`: registration, discovery, priority ordering, validation hook default/override

## Phase 2: Extract 16 Intent Plugins (TDD)

- [x] 2.1 Extract GREETING plugin: copy patterns verbatim from `intent_layer._init_patterns()`; write `tests/plugins/test_greeting.py`; register in registry; run full test suite — must pass identically; delete patterns from `_init_patterns()`
- [x] 2.2 Extract THANKS plugin: same workflow; write `tests/plugins/test_thanks.py`
- [x] 2.3 Extract EXIT plugin: same workflow; write `tests/plugins/test_exit.py`; note: will include `validate()` for exit negation in Phase 3
- [x] 2.4 Extract CALCULATE plugin: copy REGEX patterns with `entity_group="math"`; write `tests/plugins/test_calculate.py`; priority=5
- [x] 2.5 Extract TIME plugin: copy PHRASE + REGEX patterns; write `tests/plugins/test_time.py`; priority=10
- [x] 2.6 Extract DATE plugin: copy PHRASE + REGEX patterns; write `tests/plugins/test_date.py`; priority=10
- [x] 2.7 Extract DECIA_SELF plugin: copy 17 patterns (EXACT + PHRASE); write `tests/plugins/test_decia_self.py`; priority=5
- [x] 2.8 Extract DECIA_CREATOR plugin: copy 14 patterns (PHRASE + KEYWORD); write `tests/plugins/test_decia_creator.py`; priority=5
- [x] 2.9 Extract USER_NAME_ASK plugin: copy 9 patterns (EXACT + PHRASE); write `tests/plugins/test_user_name_ask.py`; priority=5
- [x] 2.10 Extract PREFERRED_NAME_ASK plugin: copy 4 patterns; write `tests/plugins/test_preferred_name_ask.py`; priority=5
- [x] 2.11 Extract USER_NAME_SET plugin: copy 7 REGEX patterns with `entity_group="user_name"`; write `tests/plugins/test_user_name_set.py`; priority=5
- [x] 2.12 Extract PREFERRED_NAME_SET plugin: copy 7 REGEX patterns with `entity_group="preferred_name"`; write `tests/plugins/test_preferred_name_set.py`; priority=5
- [x] 2.13 Extract MEMORY_CREATE plugin: copy 9 PHRASE patterns with `entity_group="memory"`; write `tests/plugins/test_memory_create.py`; priority=5
- [x] 2.14 Extract MEMORY_SEARCH plugin: copy 28 patterns (KEYWORD + REGEX + PHRASE); write `tests/plugins/test_memory_search.py`; priority=5
- [x] 2.15 Extract ARCHIVE_DIRECT plugin: copy 21 patterns (PHRASE + REGEX); write `tests/plugins/test_archive_direct.py`; priority=5
- [x] 2.16 Extract ARCHIVE_SEARCH plugin: copy 24 patterns (KEYWORD + PHRASE + REGEX); write `tests/plugins/test_archive_search.py`; priority=5
- [x] 2.17 Extract PLANNER_QUERY plugin: copy 6 REGEX patterns; write `tests/plugins/test_planner_query.py`; priority=5

## Phase 3: Special Logic Extraction

- [x] 3.1 Move `_PLANNER_RECALL_BANNED`, `_PLANNER_MARKER_SRC`, `_PLANNER_QUERY_WORDS_EXCLUDED` constants to `plugins/planner_create.py`; implement `PLANNER_CREATE.validate()` returning False for banned phrases matching `_PLANNER_RECALL_BANNED` regex
- [x] 3.2 Move `_has_exit_negation()` logic to `plugins/exit.py` as `EXIT.validate()` returning False when message contains "no" before "salir"
- [x] 3.3 Verify `_extract_archive_field()` stays in `IntentLayer` (shared by ARCHIVE_DIRECT/SEARCH); not moved to plugin

## Phase 4: Cleanup & Optimization

- [x] 4.1 Remove `_init_patterns()` entirely from `IntentLayer`; replace `self._patterns` initialization with registry iteration in `classify()`
- [x] 4.2 Add auto-discovery: `pkgutil.iter_modules()` to auto-import plugins from `app/brain.plugins`, with explicit import fallback list for Phase 2 reliability
- [x] 4.3 Performance benchmark: run `tests/test_intent_stress.py`; confirm p95 latency within 5% of baseline; memory delta < 10MB
- [x] 4.4 Update docstrings and comments in `intent_layer.py` to reflect registry-based pattern source

## Phase 5: Verification

- [x] 5.1 Run full golden master: `python -m pytest tests/test_intent_layer.py -v` — all 100+ tests pass unchanged
- [x] 5.2 Run regression matrix: `python -m pytest tests/plugins/test_regression.py -v` — parametrized matrix from `test_intent_layer.py` cases produces identical `ClassifyResult`
- [x] 5.3 Run stress test: `python -m pytest tests/test_intent_stress.py -v` — p95 latency within 5% of baseline
- [x] 5.4 Manual smoke test: classify real-world queries covering all 16 intents; verify confidence tiers (SEGURO/PROBABLE/AMBIGUO)
- [x] 5.5 Archive delta spec: capture changes for delta spec synchronization

## Open Questions (carry forward)

- [x] Should `AMBIGUOUS_INPUT` and `FREE_TALK` plugins have empty pattern lists or be handled as special cases in orchestrator? (Exploration suggests empty lists; current monolith has empty list for FREE_TALK) -- **Resolved: empty pattern lists as plugins**
- [x] Confirm priority values for all 16 plugins -- design only shows examples (GREETING=10, EXIT=10). Need explicit priority per intent for deterministic tie-breaking. -- **Resolved: all 16 explicit priorities set**
- [x] Auto-discovery in Phase 4: use `pkgutil.iter_modules()` or `importlib.metadata` entry points? (pkgutil simpler, no setuptools dependency) -- **Resolved: pkgutil.iter_modules()**

## Workload & PR Boundary Summary

- **Total tasks**: 37 concrete implementation tasks across 5 phases (all complete)
- **Estimated changed lines**: 800 (HIGH — over 400-line budget)
- **Chain strategy**: feature-branch-chain
  - PR #1 base: feature/tracker branch (infrastructure)
  - PR #2 base: PR #1 branch (GREETING + THANKS + registry)
  - PR #3-4 base: previous PR branch (remaining plugins batched)
  - PR #4 base: PR #3 branch (special logic extraction)
  - PR #5 base: PR #4 branch (cleanup + verification)
- **Review budget impact**: 800 lines exceeds 400 budget; chained PRs required. Each PR stays under ~150-200 lines of changed code.
- **Rollback boundary**: Revert specific PR's plugin modules + `intent_layer.py` changes; golden master test suite provides safety net at each step.