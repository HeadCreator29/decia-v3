# Tasks: Services Plugin Architecture

## Review Workload Forecast

| Field | Value |
|-------|-------|
| Estimated changed lines | ~1,200 |
| 400-line budget risk | High |
| Chained PRs recommended | Yes |
| Suggested split | PR 0→1→2→3→4→5→6 |
| Delivery strategy | auto-chain |
| Chain strategy | feature-branch-chain |
| Decision needed before apply | No |
| Chained PRs recommended | Yes |
| Chain strategy | feature-branch-chain |
| 400-line budget risk | High |

Decision needed before apply: No
Chained PRs recommended: Yes
Chain strategy: feature-branch-chain
400-line budget risk: High

## Phase 1: Foundation / Registry Infrastructure

- [ ] 1.1 RED: Write `tests/services/test_plugin_base.py` — ServicePlugin contract
- [ ] 1.2 GREEN: Create `app/services/plugins/base.py` — `ServicePlugin(ABC)` dataclass
- [ ] 1.3 RED: Write `tests/services/test_registry.py` — register/get/get_instance/discover
- [ ] 1.4 GREEN: Create `app/services/plugins/registry.py` — `ServiceRegistry`
- [ ] 1.5 RED: Write `tests/services/test_discovery.py` — pkgutil auto-discovery + fallback
- [ ] 1.6 GREEN: Create `app/services/plugins/__init__.py` — auto-discovery + `_FALLBACK_PLUGINS`
- [ ] 1.7 REFACTOR: `pytest tests/services/ -v` — all green

## Phase 2: Archive Plugins (Identity → User → History → Memory → Search)

- [ ] 2.1 RED: Write `tests/services/test_identity.py` — get/save parity, missing → `{}`
- [ ] 2.2 GREEN: Create `app/services/plugins/identity.py` — IdentityPlugin
- [ ] 2.3 RED: Write `tests/services/test_user.py` — get/save parity
- [ ] 2.4 GREEN: Create `app/services/plugins/user.py` — UserPlugin
- [ ] 2.5 RED: Write `tests/services/test_history.py` — events + temporal query
- [ ] 2.6 GREEN: Create `app/services/plugins/history.py` — HistoryPlugin
- [ ] 2.7 RED: Write `tests/services/test_memory.py` — CRUD, dedup, canonical forms
- [ ] 2.8 GREEN: Create `app/services/plugins/memory.py` — MemoryPlugin (most complex)
- [ ] 2.9 RED: Write `tests/services/test_search.py` — orchestration, temporal filter
- [ ] 2.10 GREEN: Create `app/services/plugins/search.py` — SearchPlugin (deps: 1-4)
- [ ] 2.11 REFACTOR: `pytest tests/ -x` — golden master all archive phases

## Phase 3: Voice Merge

- [ ] 3.1 RED: Write `tests/services/test_voice.py` — speak/listen parity
- [ ] 3.2 GREEN: Create `app/services/plugins/voice.py` — VoicePlugin (voice + speaker)
- [ ] 3.3 REFACTOR: Deprecate `services/speaker.py`; re-export `VoicePlugin.speak()`; `pytest tests/ -x`

## Phase 4: Planner & Ollama

- [ ] 4.1 RED: Write `tests/services/test_planner.py` — load/save/query/update parity
- [ ] 4.2 GREEN: Create `app/services/plugins/planner.py` — PlannerPlugin
- [ ] 4.3 RED: Write `tests/services/test_ollama.py` — completion parity, search dep
- [ ] 4.4 GREEN: Create `app/services/plugins/ollama.py` — OllamaPlugin (deps: search)
- [ ] 4.5 REFACTOR: Update `services/ollama_service.py` façade; `pytest tests/ -x`

## Phase 5: Façade & Import Routing

- [ ] 5.1 Convert `services/archive.py` to thin façade; preserve `__all__`
- [ ] 5.2 Convert `services/speaker.py` to deprecated façade; re-export `VoicePlugin.speak()`
- [ ] 5.3 Route 21 archive + 5 speaker imports through `services.plugins.*` in handlers/tests
- [ ] 5.4 RED: Write `tests/services/test_regression.py` — parametrized 21 call sites
- [ ] 5.5 REFACTOR: `pytest tests/ -x` — 100% pass; `pytest tests/test_intent_stress.py` p95 within 5%

## Phase 6: Cleanup & Verification

- [ ] 6.1 Remove monolith functions from `services/archive.py` (façade only)
- [ ] 6.2 `pytest tests/ -v` — all tests pass
- [ ] 6.3 `pytest tests/test_intent_stress.py -v` — p95 within 5%, memory < 10MB
