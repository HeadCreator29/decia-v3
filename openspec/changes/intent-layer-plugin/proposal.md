# Proposal: Intent Layer Plugin Architecture Refactor

## Intent

Refactor the 1230-line monolithic `IntentLayer` into a plugin/registry architecture with 16 self-contained intent modules. Current code blocks parallel work, causes merge conflicts, and prevents isolated testing. Plugin architecture enables independent intent development, easier debugging, and cleaner separation of concerns — all with zero breaking changes to public API.

## Scope

### In Scope
- Plugin infrastructure: `app/brain/plugins/` package (base, registry, discovery)
- 16 intent plugins extracted (one module per intent, preserving all patterns verbatim)
- Special logic moved to plugins: PLANNER_CREATE recall-ban, exit negation, archive keywords
- Test baseline + contract tests + regression matrix ensuring 100% behavioral parity
- Thin `IntentLayer` orchestrator (~200 lines) using registry

### Out of Scope
- Changing classification behavior, scoring, or confidence tiers
- Modifying `handlers.py` or `core.py` routing logic
- Adding new intent types or pattern types
- Runtime config (YAML/JSON) — patterns stay in Python
- Auto-discovery in Phase 2 (explicit imports first; auto in Phase 4)

## Capabilities

### New Capabilities
None — pure refactor, no new user-facing capabilities.

### Modified Capabilities
None — `intent-classification` spec requirements unchanged; only implementation changes.

## Approach

**Per-Intent Plugin Module** (Approach 1 from exploration). Each intent = Python module in `app/brain/plugins/` exporting `plugin` instance with patterns, entity_group, priority, optional `validate()`. Registry loads plugins at startup. `IntentLayer.classify()` iterates registry patterns — same logic, new source. Phased migration:
- Phase 0: Test baseline, contract scaffolding (0.5d)
- Phase 1: Plugin infrastructure, registry tests (1d)
- Phase 2: Extract 16 plugins one-by-one TDD (4-5d)
- Phase 3: Special logic extraction (1d)
- Phase 4: Cleanup, auto-discovery, benchmark (1d)
- Phase 5: Verification, archive (0.5d)

## Affected Areas

| Area | Impact | Description |
|------|--------|-------------|
| `app/brain/intent_layer.py` | Modified | Replace `_init_patterns()` with registry iteration; ~1000 lines removed |
| `app/brain/intent_types.py` | Modified | Minor extensions for plugin metadata if needed |
| `app/brain/plugins/` | New | 16 plugin modules + base.py + registry.py + __init__.py |
| `tests/test_intent_layer.py` | Modified | Must pass identically (golden master) |
| `tests/plugins/` | New | Contract tests per plugin + registry + regression matrix |

## Risks

| Risk | Likelihood | Mitigation |
|------|------------|------------|
| Behavioral drift in scoring | Medium | Golden master tests + parallel old/new runs during Phase 2 |
| Cross-intent priority conflicts | Medium | Explicit priority per plugin; documented conflict rules; conflict tests |
| PLANNER_CREATE recall-ban breaks | Medium | Extract to plugin.validate(); specific banned-phrase tests |
| Exit negation logic breaks | Low | Move to exit plugin validate(); test "no salir" cases |
| Plugin discovery fails in packaging | Low | Explicit imports in Phase 2; auto-discovery only Phase 4 with fallback |
| Circular imports | Low | Plugins leaf modules (import only intent_types) |

## Rollback Plan

Revert `app/brain/intent_layer.py` to monolithic version (git history). Plugin modules remain but unused. Zero impact on `core.py` or `handlers.py`. Full test suite passes on monolith.

## Dependencies

- Python 3.11+ (dataclasses, importlib)
- Existing test infrastructure (pytest)
- No external dependencies

## Success Criteria

- [ ] All 100+ existing tests in `test_intent_layer.py` pass unchanged
- [ ] New plugin contract tests pass for all 16 intents
- [ ] Regression matrix: identical `ClassifyResult` for all test cases
- [ ] Classification latency within 5% of baseline (stress test)
- [ ] No changes to `core.py` or `handlers.py` behavior
- [ ] Plugin modules independently testable in isolation