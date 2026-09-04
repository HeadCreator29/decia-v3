# Proposal: Services Plugin Architecture

## Problem

The `app/services/` directory contains 5 services with significant architectural debt:

| Service | Lines | Issue |
|---------|-------|-------|
| `archive.py` | 1,254 | **God module** — 5 domains (identity, user, history, memories, search) mixed with canonical verb forms, temporal filters, dedup logic |
| `ollama_service.py` | 430 | Tightly coupled to `archive.build_archive_context()`; imports archive internals directly |
| `planner.py` | 442 | Well-structured but standalone; no common pattern with other services |
| `voice.py` | 384 | Whisper STT + pyttsx3 TTS + VAD; legacy sync architecture |
| `speaker.py` | 24 | **Duplicate** — wraps pyttsx3; 2 tests use it; should merge into `voice.py` |

**Pain points:**
- **Monolith size**: `archive.py` = 1,254 lines, 5 domains → hard to test, review, extend
- **Testing**: 30+ tests import internal functions directly → brittle, no isolation
- **Parallel work**: All archive changes touch one file → merge conflicts
- **Extensibility**: Adding search variant = edit monolith; voice has no plugin boundary
- **Coupling**: `ollama_service` imports archive internals; `handlers.py` imports from both `archive` and `planner`

## Scope

**In scope:**
- Split `archive.py` into 5 plugins: `IdentityPlugin`, `UserPlugin`, `HistoryPlugin`, `MemoryPlugin`, `SearchPlugin`
- Merge `voice.py` + `speaker.py` → `VoicePlugin`
- Wrap `planner.py` → `PlannerPlugin`
- Wrap `ollama_service.py` → `OllamaPlugin`
- Create `ServicePlugin` base + `ServiceRegistry` (mirroring `intent-layer-plugin` pattern)
- Façade layer preserving all existing imports → **zero behavioral change**
- Auto-discovery via `pkgutil.iter_modules()` + explicit fallback

**Out of scope:**
- `voice_pipeline/` subpackage (already modular, 7 files)
- Behavioral changes to any public API
- Ollama streaming support (defer to follow-up)

## Approach

**Plugin/Registry pattern** (proven in `intent-layer-plugin`):

```
app/services/plugins/
├── base.py              # ServicePlugin dataclass, abstract methods
├── registry.py          # ServiceRegistry: register, get, get_instance, discover
├── identity.py          # IdentityPlugin
├── user.py              # UserPlugin
├── history.py           # HistoryPlugin
├── memory.py            # MemoryPlugin
├── search.py            # SearchPlugin
├── voice.py             # VoicePlugin (merged)
├── planner.py           # PlannerPlugin
├── ollama.py            # OllamaPlugin
└── __init__.py          # Façade re-exports, auto-discovery entry
```

**Migration phases (9 phases, zero behavioral change):**

| Phase | Action | Verification |
|-------|--------|--------------|
| 0 | Registry infra + base dataclass | Unit tests |
| 1 | IdentityPlugin (simplest) | Golden master |
| 2 | UserPlugin | Golden master |
| 3 | HistoryPlugin | Golden master |
| 4 | MemoryPlugin (most complex) | Golden master + contract |
| 5 | SearchPlugin (orchestrates 1-4) | Golden master |
| 6 | VoicePlugin (merge speaker) | Voice tests |
| 7 | PlannerPlugin + OllamaPlugin | Integration tests |
| 8 | Façade migration + cleanup | Full suite + benchmarks |

**Testing strategy:**
- Golden master at each phase: all existing tests pass unchanged
- Per-plugin contract tests
- Regression matrix: parametrize all 21 call sites
- Performance: p95 within 5% of baseline, memory < 10MB overhead

## Deliverables

1. `app/services/plugins/` package (10 new modules)
2. Updated `services/archive.py`, `services/ollama_service.py` as thin façades
3. Deleted `services/speaker.py`
4. Test suite: `test_plugin_base.py`, `test_registry.py`, 8×`test_<plugin>.py`, `test_regression.py`
5. Migration docs + delta spec sync

## Success Criteria

- ✅ Zero behavioral change: all 30+ existing tests pass
- ✅ 60% line reduction in `archive.py` (1254 → ~500 façade)
- ✅ All imports route through `services.plugins.*` façade
- ✅ Performance parity: p95 within 5%, memory < 10MB
- ✅ Plugin boundaries enable parallel work + isolated testing

## Risks & Mitigations

| Risk | Severity | Mitigation |
|------|----------|------------|
| `archive.py` complexity (canonical forms, temporal filter) | High | Extract incrementally; keep façade; most complex plugin last |
| Test coupling (30+ tests import internals) | High | Façade layer during migration; only remove after all plugins extracted |
| Circular deps (Search → Memory/History/Identity/User) | Medium | Lazy `registry.get_instance()`; explicit dependency order |
| Ollama streaming for `voice_pipeline` | Medium | Defer; current `ask_ollama` is non-streaming |

## Open Questions

1. `voice_pipeline/` integration — keep separate or merge?
2. Ollama streaming support in `OllamaPlugin`?
3. Health check / readiness API for `ServiceRegistry`?
4. Plugin config schema (dataclass vs dict) — align with intent-layer?

---

*Created: 2026-08-30*
*Change: services-plugin-architecture*
*Preflight: auto, hybrid, auto-chain, 800 lines*