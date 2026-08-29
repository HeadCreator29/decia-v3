# Tasks: Intent Layer Plugin Architecture Refactor

## Review Workload Forecast

| Field | Value |
|-------|-------|
| Estimated changed lines | ~2,100 |
| 400-line budget risk | High |
| Chained PRs recommended | Yes |
| Suggested split | PR 1: infra → PR 2: intents 1-8 → PR 3: intents 9-16 → PR 4: logic+cleanup → PR 5: verify |
| Delivery strategy | auto-chain |
| Chain strategy | feature-branch-chain |

Decision needed before apply: No
Chained PRs recommended: Yes
Chain strategy: feature-branch-chain
400-line budget risk: High

## Phase 0: Test Baseline + Contract Scaffolding

- [ ] T-001 Baseline: `pytest tests/test_intent_layer.py -v` — 123 tests pass
- [ ] T-002 Create `tests/plugins/__init__.py`
- [ ] T-003 `tests/plugins/test_plugin_base.py` — `IntentPlugin` fields, `validate()`→True, `entity_group is None`
- [ ] T-004 Pattern reference matrix for all 16 intents

## Phase 1: Plugin Infrastructure

- [ ] T-005 `app/brain/plugins/__init__.py` — export `IntentPlugin`, `PluginRegistry`; 16 module names
- [ ] T-006 `app/brain/plugins/base.py` — `IntentPlugin` dataclass: `name`, `category`, `patterns`, `entity_group=None`, `priority=0`, `validate()→True`
- [ ] T-007 `app/brain/plugins/registry.py` — `register()`, `get_patterns()`, `get_all_patterns()`, `get_plugin()`, `validate_match()`; sort `(-score, -priority)`
- [ ] T-008 `tests/plugins/test_registry.py` — registration, priority tie-break, `validate_match()` default/override
- [ ] T-009 `pytest tests/plugins/ -x` — infra tests pass

## Phase 2: Extract 16 Intent Plugins (TDD per intent; parallelizable)

- [ ] T-010 **GREETING** — `tests/plugins/test_greeting.py` (5 p, p=10, "hola"→GREETING≥0.90); `plugins/greeting.py` verbatim; reg; suite; del block
- [ ] T-011 **THANKS** — `test_thanks.py` (4 p); `plugins/thanks.py`; reg; suite; del
- [ ] T-012 **EXIT** — `test_exit.py` (11 p, p=10); `plugins/exit.py`; reg; suite; del
- [ ] T-013 **CALCULATE** — `test_calculate.py` (5 REGEX, eg="math"); `plugins/calculate.py`; reg; suite; del
- [ ] T-014 **TIME** — `test_time.py` (11 p, p=10); `plugins/time.py`; reg; suite; del
- [ ] T-015 **DATE** — `test_date.py` (14 p, p=10); `plugins/date.py`; reg; suite; del
- [ ] T-016 **DECIA_SELF** — `test_decia_self.py` (17 p, p=5); `plugins/decia_self.py`; reg; suite; del
- [ ] T-017 **DECIA_CREATOR** — `test_decia_creator.py` (14 p, p=5); `plugins/decia_creator.py`; reg; suite; del
- [ ] T-018 **USER_NAME_ASK/SET** — `test_user_name_ask.py` (11) + `test_user_name_set.py` (7 REGEX, eg="user_name"); both; reg; suite; del
- [ ] T-019 **PREFERRED_NAME_ASK/SET** — `test_preferred_name_ask.py` (4) + `test_preferred_name_set.py` (7 REGEX, eg="preferred_name"); both; reg; suite; del
- [ ] T-020 **MEMORY_CREATE/SEARCH** — `test_memory_create.py` (9 PHRASE, eg="memory") + `test_memory_search.py` (28); both; reg; suite; del
- [ ] T-021 **ARCHIVE_DIRECT/SEARCH** — `test_archive_direct.py` (18) + `test_archive_search.py` (24); both; reg; suite; del
- [ ] T-022 **PLANNER_CREATE/QUERY** — `test_planner_create.py` (3 REGEX, p=5) + `test_planner_query.py` (6 REGEX); both; reg; suite; del
- [ ] T-023 **AMBIGUOUS_INPUT/FREE_TALK** — `test_ambiguous_input.py` (empty) + `test_free_talk.py` (empty); both; reg; suite; del
- [ ] T-024 Regression: `pytest tests/test_intent_layer.py tests/plugins/ -v` — all 123+ pass identically

## Phase 3: Special Logic Extraction

- [ ] T-025 **PLANNER_CREATE recall-ban** — move `_PLANNER_RECALL_BANNED`, `_PLANNER_MARKER_SRC`, `_PLANNER_QUERY_WORDS_EXCLUDED` to `plugins/planner_create.py`; `validate()`→False; RED: "algo de memoria"→False; del constants from `intent_layer.py`
- [ ] T-026 **EXIT negation** — move `_has_exit_negation()` to `plugins/exit.py` as `validate()`; RED: "no quiero salir"→False; del from `intent_layer.py`
- [ ] T-027 **ARCHIVE keywords** — `_archive_keywords` accessible to ARCHIVE_DIRECT/SEARCH; `_extract_archive_field()` stays in `IntentLayer`; RED: keyword matching unchanged

## Phase 4: Cleanup & Optimization

- [ ] T-028 Remove `_init_patterns()`; `__init__`→`PluginRegistry`+`_load_plugins()`+`_archive_keywords`; reduce to ~200 lines
- [ ] T-029 Add `pkgutil.walk_packages()` auto-discovery + explicit fallback; update `test_registry.py`
- [ ] T-030 Benchmark: `pytest tests/test_intent_stress.py` — p95 within 5%, memory delta < 10MB

## Phase 5: Verification + Archive

- [ ] T-031 Full suite: `pytest tests/ -x --tb=short` — all pass
- [ ] T-032 Smoke: `python -c "from brain.intent_layer import IntentLayer; r=IntentLayer().classify('hola'); assert r.intent==GREETING and r.confidence>=0.90"`
- [ ] T-033 Archive delta via `sdd-archive`; verify `core.py` and `handlers.py` unchanged (`git diff` empty)
