# Proposal: Memoria Viva DECIA

## Executive Summary

Transform DECIA's flat JSON memory into a **typed, temporal, searchable, self-reflective memory system** with 8 memory types, prediction horizons, decision logs, lessons, identity versioning, and encrypted diary reflections. Delivered in 8 progressive phases (<400 lines each) extending the existing plugin architecture — zero massive refactor, model stays `llama3.2:3b`, voice stack untouched, 354 golden tests pass throughout.

---

## Current State (from Exploration)

| Aspect | Current |
|--------|---------|
| **Storage** | Single `memories.json` array (1,300+ entries) |
| **Types** | Only `type: "memory"` (string) |
| **Plugins** | `MemoryPlugin` (CRUD + dedup), `IdentityPlugin` (key-value), `HistoryPlugin` (temporal events), `SearchPlugin` (orchestration) |
| **Intent** | `MEMORY_CREATE` / `MEMORY_SEARCH` only |
| **Tests** | 354 golden master tests passing; `test_services/test_memory.py` contract suite |
| **Schema** | `{id, text, date, type, source}` — no confidence, relations, predictions, lessons, identity versioning |
| **Search** | Substring match on canonicalized content; no FTS5, no structured query |

---

## Target Architecture

### Plugin Map (New + Extended)

| Plugin | Category | Responsibility |
|--------|----------|----------------|
| `MemoryPlugin` (extended) | ARCHIVE | Typed CRUD, confidence, relations, migration |
| `DecisionPlugin` | ARCHIVE | DECISION_CREATE intent, structured choice log |
| `PredictionPlugin` | ARCHIVE | PREDICTION_CREATE, horizon tracking, status |
| `LearningPlugin` | ARCHIVE | LESSON capture from outcomes |
| `ReflectionPlugin` | ARCHIVE | Auto-draft diary + user approval flow |
| `IdentityCorePlugin` | ARCHIVE | Versioned identity source with audit trail |
| `SearchPlugin` (extended) | ARCHIVE | FTS5 unified index, dual NL + structured query |
| `TemporalPlugin` | ARCHIVE | Year tabs (2026-2035), timeline, semantic nav |
| `PatternsPlugin` | ARCHIVE | Cross-domain pattern detection |
| `ContextPlugin` | ARCHIVE | Context assembly for LLM prompts |

### Data Model (JSON → SQLite Migration Path)

```json
// Phase 1: Extended JSON (backward compatible)
{
  "id": "uuid",
  "type": "FACT|MEMORY|DECISION|GOAL|PREDICTION|LESSON|INTERPRETATION|UNKNOWN",
  "content": "string",
  "confidence": 0.0-1.0,
  "source": "conversation|user|decia|migration",
  "created_at": "ISO8601",
  "updated_at": "ISO8601",
  "version": 1,
  "relations": [{"type": "relates-to|supports|contradicts|supersedes", "target_id": "uuid"}],
  // Type-specific fields:
  "horizons": {"short": "...", "medium": "...", "long": "..."},  // PREDICTION
  "choice": {...}, "rationale": "...", "alternatives": [...],  // DECISION
  "outcome": "...", "applied": true,                          // LESSON
  "approved": true, "draft": "...",                           // INTERPRETATION/REFLECTION
  "encryption": "none|optional|mandatory"                     // per-type policy
}
```

**Phase 7**: Migrate to SQLite with FTS5 virtual table for unified search; JSON remains export format.

---

## 8-Phase Breakdown

| Phase | Focus | Est. Lines | Key Deliverable | Acceptance |
|-------|-------|------------|-----------------|------------|
| **1** | Typed Memory Foundation | ~200 | `MemoryPlugin` + type/confidence/relations fields; migration tool (1300→MEMORY, 0.7 legacy) | All golden tests pass; migration idempotent; new fields queryable |
| **2** | Decision Memory | ~300 | `DecisionPlugin`, `DECISION_CREATE` intent, handler | Decision log created from conversation; queryable by date/topic |
| **3** | Future Engine (Predictions) | ~350 | `PredictionPlugin`, `PREDICTION_CREATE`, status tracking (open/confirmed/refuted) | Predictions stored with 3 horizons; status transitions audited |
| **4** | Learning/Lessons | ~250 | `LearningPlugin`, lesson capture from outcomes | Lessons auto-generated from prediction resolutions + manual |
| **5** | Reflections/Diary | ~200 | `ReflectionPlugin`, auto-draft + user approval flow | Post-conversation drafts → user edits → encrypted persistence |
| **6** | Identity Core | ~200 | `IdentityCorePlugin`, versioned identity source | Identity changes versioned; user approval required; audit trail |
| **7** | Search + FTS5 (SQLite) | ~400 | `SearchPlugin` with FTS5, unified index | NL search <100ms; structured query (type/date/confidence/relations) |
| **8** | Cross-Domain Intelligence | ~400 | `TemporalPlugin`, `PatternsPlugin`, `ContextPlugin` | Year tabs UI-ready; pattern alerts; context bundles for LLM |

---

## Capabilities Contract (for sdd-spec)

### New Capabilities
- `typed-memory`: Type/confidence/relations on all memories; migration tool
- `decision-log`: Structured decision capture with alternatives & rationale
- `prediction-tracking`: Multi-horizon forecasts with status lifecycle
- `lesson-capture`: Actionable takeaways from outcomes
- `reflection-diary`: Encrypted diary with user approval flow
- `identity-versioning`: Evolvable identity with audit trail & user ceremony
- `unified-search`: FTS5 + structured query + temporal navigation
- `cross-domain-intel`: Temporal views, pattern detection, context assembly

### Modified Capabilities
- `memory-crud`: Extended schema (type, confidence, relations, encryption)
- `search-orchestration`: Backend swapped to SQLite FTS5; API unchanged
- `intent-classification`: New intents `DECISION_CREATE`, `PREDICTION_CREATE`, `REFLECTION_APPROVE`

---

## Migration Strategy (1,300+ Existing Memories)

1. **Phase 1 tool**: One-shot script reads `memories.json`, writes enriched JSON with:
   - `type: "MEMORY"` (default)
   - `confidence: 0.7` (legacy default)
   - `source: "migration"`
   - `version: 1`
   - `relations: []`
   - `encryption: "optional"` (per MEMORY policy)
2. **Idempotent**: Re-runnable; detects already-migrated entries via `source: "migration"`
3. **Backup**: Original `memories.json` → `memories.pre-migration.backup.json`
4. **Batch Re-classification** (Phase 1 CLI): Interactive tool to bulk-update types for known categories (facts, decisions, goals)
5. **Zero Downtime**: Plugin reads both old and new schema during transition

---

## Risk Analysis

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Schema evolution breaks golden tests | Medium | High | Phase 1: extend only (additive fields); contract tests validate old+new |
| FTS5 index drift from JSON | Low | High | Phase 7: write-ahead sync; rebuild command; verification test |
| Intent regression (new intents) | Medium | Medium | Per-phase intent contract tests; regression matrix vs 354 baseline |
| Context bloat in LLM prompts | Medium | Medium | Phase 8: `ContextPlugin` with token budget, relevance ranking |
| Encryption key management | Low | High | Phase 5/6: derive from user passphrase; no cloud; local-only |
| Migration data loss | Low | Critical | Backup + idempotent tool + dry-run flag + verification hash |
| Plugin coupling creep | Medium | Medium | Strict plugin interface; registry-only communication; no cross-imports |

---

## Test Strategy

| Layer | Coverage |
|-------|----------|
| **Golden Master** | All 354 existing tests pass unchanged every phase |
| **Contract Tests** | Per-plugin: `test_services/test_<plugin>.py` (CRUD, validation, edge cases) |
| **Intent Contracts** | New intents: `DECISION_CREATE`, `PREDICTION_CREATE`, `REFLECTION_APPROVE` |
| **Migration Tests** | Round-trip: original → migrated → query = identical semantics |
| **FTS5 Tests** | Search parity: NL results match substring baseline; structured query correctness |
| **E2E Scenarios** | Conversation → decision → prediction → outcome → lesson → reflection → identity update |
| **Performance** | Phase 7: search <100ms p95 on 5k entries; Phase 8: context assembly <200ms |

---

## Delivery Plan

- **Branch Strategy**: Feature branch per phase (`memoria-viva/phase-1-typed-memory` … `phase-8-intelligence`)
- **PR Chain**: 8 PRs, each <400 lines changed (chained, stacked)
- **Review Budget**: 800 lines max per review session (cognitive-doc-design)
- **Merge Gate**: Golden master + new contract tests + migration verification (where applicable)
- **Archiving**: Each phase archived via `sdd-archive` before next phase begins

---

## Open Questions — RESOLVED (11 Decisions Locked)

| # | Decision | Resolution |
|---|----------|------------|
| 1 | Memory types | 8 types: FACT, MEMORY, DECISION, GOAL, PREDICTION, LESSON, INTERPRETATION, UNKNOWN |
| 2 | Prediction horizons | Multiple per entry: short (days-weeks), medium (months), long (years 2026-2035) |
| 3 | Confidence model | Continuous 0.0-1.0 hybrid (user sets initial, DECIA calibrates) |
| 4 | Relations | Hybrid: manual explicit (relates-to, supports, contradicts, supersedes) + embedding suggestions |
| 5 | Identity | Evolvable & versioned with audit trail; user approves; hard limits need ceremony |
| 6 | Diary/Reflections | Hybrid: DECIA drafts post-conversation → user edits/approves → persist |
| 7 | Migration (1300+) | Default MEMORY, 0.7 legacy; batch re-classification tool in Phase 1 |
| 8 | Privacy/Encryption | FACT=none; MEMORY/DECISION/PREDICTION/GOAL=optional; INTERPRETATION/LESSON/IDENTITY=mandatory |
| 9 | Search | Dual: NL primary + structured (type, date range, confidence, relations) |
| 10 | Temporal Navigation | Dual: year tabs (2026-2035) + timeline + semantic search |
| 11 | Conflicts | Explicit contradiction object + status field (confirmed, contradicted, superseded, disputed) |

---

## Rollback Plan

| Phase | Rollback Action |
|-------|-----------------|
| 1 | Delete new plugin files; revert `MemoryPlugin` to pre-Phase-1 version; restore `memories.json` from backup |
| 2-6 | Remove phase-specific plugin; revert intent registry additions; no data migration needed (additive) |
| 7 | Drop SQLite/FTS5; revert `SearchPlugin` to JSON orchestration; JSON remains source of truth |
| 8 | Remove intelligence plugins; core memory/search/identity unchanged |

**Full rollback**: `git revert` the 8 PRs in reverse order. Zero impact on voice, intent classification (except 3 new intents), or handlers.

---

## Dependencies

- **Runtime**: Python 3.11+, `sqlite3` (stdlib), `json` (stdlib)
- **No new external deps** (constraint honored)
- **Existing**: `faster-whisper`, `sounddevice`, `numpy`, `pyttsx3`, `ollama` HTTP — unchanged
- **Model**: `llama3.2:3b` — unchanged

---

## Success Criteria (Overall)

- [ ] All 354 golden master tests pass after each phase
- [ ] 1,300+ memories migrated with zero loss; queryable by new fields
- [ ] 8 new memory types creatable, searchable, relatable
- [ ] Decisions, predictions, lessons, reflections, identity versioning all functional
- [ ] FTS5 search <100ms p95; structured queries return correct results
- [ ] Temporal navigation (year tabs, timeline) data-ready
- [ ] Cross-domain patterns detected; context bundles reduce LLM tokens by ≥30%
- [ ] Encryption policies enforced; keys never leave process
- [ ] Zero regression on voice.py, Whisper, TTS, audio thresholds
- [ ] 8 PRs merged, each <400 lines, chained review complete

---

## Next Step

Ready for **specs (sdd-spec)** — each new capability becomes a spec file; modified capabilities get delta specs. Phase 1 starts with `typed-memory` spec.