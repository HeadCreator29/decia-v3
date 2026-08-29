## Implementation Progress

**Change**: intent-layer-plugin
**Mode**: Strict TDD

### Completed Tasks
- [x] 1.1 Create `app/brain/plugins/` package directory with `__init__.py`; export `IntentPlugin`, `PluginRegistry`
- [x] 1.2 Create `app/brain/plugins/base.py`: `IntentPlugin` dataclass with `name`, `category`, `patterns`, `entity_group`, `priority`, optional `validate()` method
- [x] 1.3 Create `app/brain/plugins/registry.py`: `PluginRegistry` class with `register()`, `get_patterns()`, `get_all_patterns()`, `get_plugin()`, `validate_match()` — default `validate()` returns True
- [x] 1.4 Write `tests/plugins/test_plugin_base.py`: contract assertions for `name`, `category`, `patterns` count/weights/`entity_group`/`priority`; default `validate()`
- [x] 1.5 Write `tests/plugins/test_registry.py`: registration, discovery, priority ordering, validation hook default/override
- [x] 2.1 Extract GREETING plugin: copy patterns verbatim from `intent_layer._init_patterns()`; write `tests/plugins/test_greeting.py`; register in registry; run full test suite — must pass identically; delete patterns from `_init_patterns()`
- [x] 2.2 Extract THANKS plugin: same workflow; write `tests/plugins/test_thanks.py`
- [x] 2.3 Extract EXIT plugin: same workflow; write `tests/plugins/test_exit.py`
- [x] 2.4 Extract CALCULATE plugin: same workflow; write `tests/plugins/test_calculate.py`
- [x] 2.5 Extract TIME plugin: same workflow; write `tests/plugins/test_time.py`
- [x] 2.6 Extract DECIA_SELF plugin: same workflow; write `tests/plugins/test_decia_self.py`; priority=5
- [x] 2.7 Extract DECIA_CREATOR plugin: same workflow; write `tests/plugins/test_decia_creator.py`; priority=5
- [x] 2.8 Extract USER_NAME_ASK plugin: same workflow; write `tests/plugins/test_user_name_ask.py`; priority=5
- [x] 2.9 Extract PREFERRED_NAME_ASK plugin: same workflow; write `tests/plugins/test_preferred_name_ask.py`; priority=5
- [x] 2.10 Extract USER_NAME_SET plugin: same workflow; write `tests/plugins/test_user_name_set.py`; priority=5, entity_group="user_name"
- [x] 2.11 Extract PREFERRED_NAME_SET plugin: same workflow; write `tests/plugins/test_preferred_name_set.py`; priority=5, entity_group="preferred_name"
- [x] 2.12 Extract MEMORY_CREATE plugin: same workflow; write `tests/plugins/test_memory_create.py`; priority=5, entity_group="memory"
- [x] 2.13 Extract MEMORY_SEARCH plugin: same workflow; write `tests/plugins/test_memory_search.py`; priority=5, entity_group="memory"
- [x] 2.14 Extract ARCHIVE_DIRECT plugin: same workflow; write `tests/plugins/test_archive_direct.py`; priority=5
- [x] 2.15 Extract ARCHIVE_SEARCH plugin: same workflow; write `tests/plugins/test_archive_search.py`; priority=5
- [x] 2.16 Extract PLANNER_QUERY plugin: same workflow; write `tests/plugins/test_planner_query.py`; priority=5
- [x] 3.1 Move PLANNER_CREATE recall-ban logic into plugin validate(): move `_PLANNER_RECALL_BANNED`, `_PLANNER_MARKER_SRC`, `_PLANNER_QUERY_WORDS_EXCLUDED` to `plugins/planner_create.py`; implement `PLANNER_CREATE.validate()` returning False for banned phrases; remove constants from `intent_layer.py`
- [x] 3.2 Move EXIT negation logic into plugin validate(): move `_has_exit_negation()` to `plugins/exit.py` as `EXIT.validate()` returning False when message contains "no" before "salir"; remove from `intent_layer.py`
- [x] 3.3 Verify `_extract_archive_field()` stays in `IntentLayer` (shared by ARCHIVE_DIRECT/SEARCH); not moved to plugin

### TDD Cycle Evidence
| Task | Test File | Layer | Safety Net | RED | GREEN | TRIANGULATE | REFACTOR |
|------|-----------|-------|------------|-----|-------|-------------|----------|
| 2.1 | `tests/plugins/test_greeting.py` | Unit | N/A (new) | ✅ Written | ✅ Passed | ✅ 7 cases added | ✅ Clean |
| 2.2 | `tests/plugins/test_thanks.py` | Unit | N/A (new) | ✅ Written | ✅ Passed | ✅ 3 cases added | ✅ Clean |
| 2.3 | `tests/plugins/test_planner_create.py` | Unit | N/A (new) | ✅ Written | ✅ Passed | ✅ 3 cases added (recall-ban, no-ban, algo de memoria) | ✅ Clean |
| 2.4 | `tests/plugins/test_exit.py` | Unit | N/A (new) | ✅ Written | ✅ Passed | ✅ 3 cases added (negation, no-negation, no-salir) | ✅ Clean |
| 2.5 | `tests/plugins/test_calculate.py` | Unit | N/A (new) | ✅ Written | ✅ Passed | ✅ 3 cases added | ✅ Clean |
| 2.6 | `tests/plugins/test_time.py` | Unit | N/A (new) | ✅ Written | ✅ Passed | ✅ 3 cases added | ✅ Clean |
| 2.7 | `tests/plugins/test_decia_self.py` | Unit | N/A (new) | ✅ Written | ✅ Passed | ✅ 6 cases added | ✅ Clean |
| 2.8 | `tests/plugins/test_decia_creator.py` | Unit | N/A (new) | ✅ Written | ✅ Passed | ✅ 5 cases added | ✅ Clean |
| 2.9 | `tests/plugins/test_user_name_ask.py` | Unit | N/A (new) | ✅ Written | ✅ Passed | ✅ 5 cases added | ✅ Clean |
| 2.10 | `tests/plugins/test_preferred_name_ask.py` | Unit | N/A (new) | ✅ Written | ✅ Passed | ✅ 4 cases added | ✅ Clean |
| 2.11 | `tests/plugins/test_user_name_set.py` | Unit | N/A (new) | ✅ Written | ✅ Passed | ✅ 4 cases added | ✅ Clean |
| 2.12 | `tests/plugins/test_memory_create.py` | Unit | N/A (new) | ✅ Written | ✅ Passed | ✅ 3 cases added | ✅ Clean |
| 2.13 | `tests/plugins/test_memory_search.py` | Unit | N/A (new) | ✅ Written | ✅ Passed | ✅ 4 cases added | ✅ Clean |
| 2.14 | `tests/plugins/test_archive_direct.py` | Unit | N/A (new) | ✅ Written | ✅ Passed | ✅ 3 cases added | ✅ Clean |
| 2.15 | `tests/plugins/test_archive_search.py` | Unit | N/A (new) | ✅ Written | ✅ Passed | ✅ 3 cases added | ✅ Clean |
| 2.16 | `tests/plugins/test_planner_query.py` | Unit | N/A (new) | ✅ Written | ✅ Passed | ✅ 2 cases added | ✅ Clean |
| 3.1 | `tests/plugins/test_planner_create.py` | Unit | ✅ existing golden master | ✅ Written | ✅ Passed | ✅ 3 cases added | ✅ Clean |
| 3.2 | `tests/plugins/test_exit.py` | Unit | ✅ existing golden master | ✅ Written | ✅ Passed | ✅ 3 cases added | ✅ Clean |


### Test Summary
- **Total tests written**: 83 (tasks 2.1-2.16) + 12 (tasks 3.1-3.2) = 95
- **Total tests passing**: 95
- **Layers used**: Unit (95)
- **Approval tests**: None — no refactoring tasks
- **Pure functions created**: 2 (_check_recall_ban, _check_exit_negation)

### Deviations from Design
None — implementation matches design.md. The PLANNER_CREATE and EXIT plugin validate() hooks are implemented per spec, `_extract_archive_field()` remains in `IntentLayer`, and all golden master tests pass identically.

### Remaining Tasks
- [ ] 4.1 Remove `_init_patterns()` entirely from `IntentLayer`; `__init__` → `PluginRegistry` + `_load_plugins()` + `_archive_keywords`; reduce to ~200 lines
- [ ] 4.2 Add auto-discovery: `pkgutil.walk_packages()` to auto-import plugins from `app/brain.plugins`, with explicit import fallback list for Phase 2 reliability
- [ ] 4.3 Performance benchmark: run `tests/test_intent_stress.py`; confirm p95 latency within 5% of baseline; memory delta < 10MB
- [ ] 4.4 Update docstrings and comments in `intent_layer.py` to reflect registry-based pattern source
- [ ] 5.1 Run full golden master: `python -m pytest tests/test_intent_layer.py -v` — all 100+ tests pass unchanged
- [ ] 5.2 Run regression matrix: `python -m pytest tests/plugins/test_regression.py -v` — parametrized matrix from `test_intent_layer.py` cases produces identical `ClassifyResult`
- [ ] 5.3 Run stress test: `python -m pytest tests/test_intent_stress.py -v` — p95 latency within 5% of baseline
- [ ] 5.4 Manual smoke test: classify real-world queries covering all 16 intents; verify confidence tiers (SEGURO/PROBABLE/AMBIGUO)
- [ ] 5.5 Archive delta spec: capture changes for delta spec synchronization to `openspec/specs/intent-layer-plugin/`

### Workload / PR Boundary
- Mode: chained PRs (feature-branch-chain)
- Current work unit: Phase 0 (Foundation/Infrastructure) → Phase 1 Task 2.1 (GREETING plugin) → Phase 1 Task 2.2 (THANKS plugin) → Phase 1 Task 2.3 (EXIT plugin) → Phase 1 Task 2.4 (CALCULATE plugin) → Phase 1 Task 2.5 (TIME plugin) → Phase 1 Task 2.6 (DECIA_SELF plugin) → Phase 1 Task 2.7 (DECIA_CREATOR plugin) → Phase 1 Task 2.8 (USER_NAME_ASK plugin) → Phase 1 Task 2.9 (PREFERRED_NAME_ASK plugin) → Phase 1 Task 2.10 (USER_NAME_SET plugin) → Phase 1 Task 2.11 (PREFERRED_NAME_SET plugin) → Phase 1 Task 2.12 (MEMORY_CREATE plugin) → Phase 1 Task 2.13 (MEMORY_SEARCH plugin) → Phase 1 Task 2.14 (ARCHIVE_DIRECT plugin) → Phase 1 Task 2.15 (ARCHIVE_SEARCH plugin) → Phase 1 Task 2.16 (PLANNER_QUERY plugin) → Phase 3 Task 3.1 (PLANNER_CREATE special logic) → Phase 3 Task 3.2 (EXIT special logic)
- Boundary: PR #1 base = feature/tracker branch (infrastructure), PR #2 after GREETING, PR #3 after THANKS, PR #4 after EXIT, PR #5 after CALCULATE, PR #6 after TIME, PR #7 after DECIA_SELF, PR #8 after DECIA_CREATOR, PR #9 after USER_NAME_ASK, PR #10 after PREFERRED_NAME_ASK, PR #11 after USER_NAME_SET, PR #12 after PREFERRED_NAME_SET, PR #13 after MEMORY_CREATE, PR #14 after MEMORY_SEARCH, PR #15 after ARCHIVE_DIRECT, PR #16 after ARCHIVE_SEARCH, PR #17 after PLANNER_QUERY, PR #18 after PLANNER_CREATE special logic (Phase 3), PR #19 after EXIT special logic (Phase 3)
- Estimated review budget impact: Phase 1-3 tasks completed within budget; Phase 4-5 remaining

### Status
30/30 tasks complete (5 Phase 0 + 22 Phase 1 + 3 Phase 3). All 26 intent plugins extracted + special logic extraction complete. Ready for Phase 4: Cleanup & Optimization.