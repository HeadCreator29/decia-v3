# Tasks: Memoria Viva DECIA

## Overview

8 progressive phases delivering a typed, temporal, searchable, self-reflective memory system. Each phase <400 lines changed, all 354 golden master tests pass throughout. Zero regression on voice/intent/handler layers. Chained PRs via `delivery_strategy: ask-on-risk` with `chain_strategy: stacked-to-main`.

---

## Phase 1 — Typed Memory Foundation (~200 lines)

**Target**: `MemoryPlugin` v2 + migration tool + 8-type schema + confidence/relations

### Tasks

- [x] **1.1** Extend `app/services/plugins/memory.py` with typed memory methods
  - Add `create_typed(content, type, confidence=0.7, relations=None, encryption="optional")`
  - Add `get_by_type(type)` — filter by 8-type enum (FACT, MEMORY, DECISION, GOAL, PREDICTION, LESSON, INTERPRETATION, UNKNOWN)
  - Add `get_by_confidence_range(min_conf, max_conf)`
  - Add `add_relation(source_id, target_id, relation_type)` — validate `relates-to|supports|contradicts|supersedes`
  - Add `update_confidence(memory_id, confidence)` — clamp 0.0-1.0
  - Add `search_by_content(query, filters)` — support type/date/confidence filters
  - Add `migrate_legacy(default_type="MEMORY", default_confidence=0.7)` — one-shot enrichment
  - **Keep `execute()` unchanged** for backward compatibility

- [x] **1.2** Create migration tool `data/archive/migrations/migrate_memories_v2.py`
  - Read `memories.json`, enrich each entry with v2 fields
  - Defaults: `type="MEMORY"`, `confidence=0.7`, `source="migration"`, `version=1`, `relations=[]`, `encryption="optional"`
  - Map legacy `text` → `content`
  - **Idempotent**: detect `source="migration"` and skip
  - **Backup**: write `memories.pre-migration.backup.json` before changes
  - **Dry-run flag**: `--dry-run` returns report without writing

- [x] **1.3** Create batch re-classification CLI `data/archive/migrations/reclassify_cli.py`
  - Pattern-based bulk update for facts/decisions/goals
  - `--preview` flag shows affected memories without persisting
  - `--apply` commits changes
  - Log re-classification summary

- [x] **1.4** Update `app/services/archive.py`
  - Add save/load for new JSON files (decisions, predictions, etc. — placeholder stubs for now)
  - Register migration tool entry point

- [x] **1.5** Contract tests `test_services/test_memory_plugin.py`
  - CRUD with extended schema
  - Migration: round-trip original → migrated → query = identical semantics
  - Idempotent migration, dry-run, backup verification
  - Type validation, confidence clamping, relation types

- [x] **1.6** Run golden master regression
  - `pytest tests/ -k "golden"` — all 354 tests pass
  - Verify zero behavioral regression on existing `execute()` paths

---

## Phase 2 — Decision Memory (~300 lines)

**Target**: `DecisionPlugin` + `DECISION_CREATE`/`DECISION_CONFIRM` intents + handler

### Tasks

- [x] **2.1** Create `app/services/plugins/decision.py`
  - `DecisionPlugin` with: `create(problem, arguments, decision, rationale, confidence)`, `confirm(decision_id, outcome, learning)`, `get_by_status(status)`, `link_memory(decision_id, memory_id, relation)`
  - Schema: id, date, problem, arguments[], decision, rationale, outcome, learning, status (OPEN|CONFIRMED|FAILED|PARTIAL|CANCELLED), related_memory_ids[], confidence
  - Status lifecycle: OPEN → CONFIRMED|FAILED|PARTIAL|CANCELLED (auditable timestamps)

- [x] **2.2** Create intent plugins `app/brain/plugins/decision_create.py`, `decision_confirm.py`
  - `DECISION_CREATE`: extract problem, arguments, decision, rationale from conversation
  - `DECISION_CONFIRM`: extract outcome, learning for status transition

- [x] **2.3** Update `app/brain/handlers.py`
  - Add handler for `DECISION_CREATE` → calls `DecisionPlugin.create()`
  - Add handler for `DECISION_CONFIRM` → calls `DecisionPlugin.confirm()`
  - Link contributing memories via `link_memory()`

- [x] **2.4** Update `app/brain/intent_types.py`
  - Add `DECISION_CREATE`, `DECISION_CONFIRM` constants

- [x] **2.5** Update `app/brain/core.py`
  - Route new intents to handlers
  - Register new intent plugins

- [x] **2.6** Contract tests `test_services/test_decision_plugin.py`
  - CRUD, status transitions, argument/rationale capture, memory linking

- [x] **2.7** Intent contract tests `test_handlers.py`
  - `DECISION_CREATE` fires with correct extraction
  - `DECISION_CONFIRM` transitions status correctly
  - No regression on existing intents

- [x] **2.8** Golden master regression — all 354 pass

---

## Phase 3 — Future Engine (Predictions) (~350 lines)

**Target**: `PredictionPlugin` + `PREDICTION_CREATE`/`PREDICTION_REVIEW` intents + handler

### Tasks

- [x] **3.1** Create `app/services/plugins/prediction.py`
  - `PredictionPlugin` with: `create(prediction_text, horizons, confidence, reasons)`, `update_status(prediction_id, status)`, `schedule_review(prediction_id, review_date)`, `get_due_reviews()`, `resolve(prediction_id, outcome, learning)`
  - Schema: id, date, prediction_text, horizons[{label, timeframe, target_date}], confidence, reasons[], status (OPEN|CONFIRMED|FAILED|PARTIAL|CANCELLED), review_date, outcome, learning, related_memory_ids[]
  - Validate: short < medium < long timeframe; target_dates within valid range (up to 2035)

- [x] **3.2** Create intent plugins `app/brain/plugins/prediction_create.py`, `prediction_review.py`
  - `PREDICTION_CREATE`: extract prediction_text, horizons (short/medium/long), confidence, reasons
  - `PREDICTION_REVIEW`: trigger status update when review_date passes

- [x] **3.3** Update `app/brain/handlers.py`
  - Handler for `PREDICTION_CREATE` → `PredictionPlugin.create()`
  - Handler for `PREDICTION_REVIEW` → `PredictionPlugin.update_status()` / `resolve()`

- [x] **3.4** Update `app/brain/intent_types.py`, `app/brain/core.py`
  - Add `PREDICTION_CREATE`, `PREDICTION_REVIEW` constants and routing

- [x] **3.5** Contract tests `test_services/test_prediction_plugin.py`
  - CRUD, horizon validation, status lifecycle, review scheduling, resolution with auto-lesson

- [x] **3.6** Intent contract tests — no regression on existing intents

- [x] **3.7** Golden master regression — all 354 pass

---

## Phase 4 — Learning/Lessons (~250 lines)

**Target**: `LearningPlugin` + `LEARNING_CREATE` intent + auto-generation from predictions

### Tasks

- [x] **4.1** Create `app/services/plugins/learning.py`
  - `LearningPlugin` with: `create(trigger_id, expected, actual, delta, lesson, future_considerations, confidence)`, `get_by_trigger(trigger_id)`
  - Schema: id, date, trigger_id (decision/prediction ref), expected, actual, delta, lesson, future_considerations, confidence
  - Auto-generate from `PredictionPlugin.resolve()` outcome
  - Validate trigger_id references existing decision or prediction

- [x] **4.2** Create intent plugin `app/brain/plugins/learning_create.py`
  - `LEARNING_CREATE`: extract trigger, expected/actual, lesson, future_considerations

- [x] **4.3** Update `app/brain/handlers.py`, `app/brain/intent_types.py`, `app/brain/core.py`
  - Handler for `LEARNING_CREATE` → `LearningPlugin.create()`
  - Wire auto-generation: `PredictionPlugin.resolve()` calls `LearningPlugin.create()` with trigger_id

- [x] **4.4** Contract tests `test_services/test_learning_plugin.py`
  - Manual creation, auto-generation from prediction resolution
  - Trigger validation, orphan handling, delta calculation

- [x] **4.5** Golden master regression — all 354 pass

---

## Phase 5 — Reflections/Diary (~200 lines)

**Target**: `ReflectionPlugin` + `REFLECTION_CREATE`/`REFLECTION_APPROVE` intents + encryption

### Tasks

- [x] **5.1** Create `app/services/plugins/encryption.py` (shared service)
  - `EncryptionService(passphrase)` — PBKDF2 key derivation
  - `encrypt(plaintext)` → base64(ciphertext+nonce+tag) AES-GCM
  - `decrypt(ciphertext_b64)` — raise on key mismatch
  - `policy_for_type(memory_type)` → `"none"|"optional"|"mandatory"` per spec:
    - FACT=none, MEMORY/DECISION/PREDICTION/GOAL=optional, INTERPRETATION/LESSON/IDENTITY=mandatory

- [x] **5.2** Create `app/services/plugins/reflection.py`
  - `ReflectionPlugin` with: `create_draft(draft_content, related_conversation_id)`, `approve(reflection_id, approved_content)`, `archive(reflection_id)`
  - Schema: id, date, draft_content, approved_content, status (DRAFT|APPROVED|ARCHIVED), related_conversation_id, user_edited
  - Status lifecycle: DRAFT → APPROVED|ARCHIVED (archived immutable)
  - Apply encryption via `EncryptionService` for INTERPRETATION/LESSON types

- [x] **5.3** Create intent plugins `app/brain/plugins/reflection_create.py`, `reflection_approve.py`
  - `REFLECTION_CREATE`: auto-draft post-conversation
  - `REFLECTION_APPROVE`: user edit/approve flow

- [x] **5.4** Update `app/brain/handlers.py`, `app/brain/intent_types.py`, `app/brain/core.py`
  - Handlers for both intents
  - Auto-draft trigger after conversation completion

- [x] **5.5** Contract tests `test_services/test_encryption.py`, `test_services/test_reflection_plugin.py`
  - Policy enforcement, key derivation, isolation, draft→approve flow

- [x] **5.6** Golden master regression — all 354 pass

---

## Phase 6 — Identity Core (~200 lines)

**Target**: `IdentityCorePlugin` + `IDENTITY_PROPOSE`/`IDENTITY_APPROVE` intents + ceremony

### Tasks

- [x] **6.1** Create `app/services/plugins/identity_core.py`
  - `IdentityCorePlugin` with: `initialize(version=1, name, origin, purpose, mission, values[], principles[], rules[], limits[], deca_relation, creator_relation)`, `propose_changes(changes)`, `approve(version, approved_by)`, `get_audit_log()`
  - Schema: version, name, origin, purpose, mission, values[], principles[], rules[], limits[], deca_relation, creator_relation, audit_log[{version, date, changes, approved_by}]
  - Audit trail immutable; user approval required for version increment
  - Hard limits trigger ceremony (explicit user approval)

- [x] **6.2** Create intent plugins `app/brain/plugins/identity_propose.py`, `identity_approve.py`
  - `IDENTITY_PROPOSE`: extract proposed changes
  - `IDENTITY_APPROVE`: user ceremony confirmation

- [x] **6.3** Update `app/brain/handlers.py`, `app/brain/intent_types.py`, `app/brain/core.py`
  - Handlers for both intents
  - Call `ContextPlugin.enrich_prompt()` before Ollama (Phase 8 prep — stub for now)

- [x] **6.4** Contract tests `test_services/test_identity_core_plugin.py`
  - Versioning, audit trail, approval ceremony, hard limits

- [x] **6.5** Golden master regression — all 354 pass

---

## Phase 7 — Search + FTS5 (SQLite) (~400 lines)

**Target**: `SearchPlugin` v2 with FTS5 backend + unified index + structured queries

### Tasks

- [x] **7.1** Extend `app/services/plugins/search.py`
  - Keep `execute()` unchanged (API compatibility)
  - Add `query(text, filters)`, `filter_by_type()`, `filter_by_date_range()`, `filter_by_confidence()`, `filter_by_relations()` — chainable builder
  - Phase 7: implement SQLite FTS5 backend
    - Single FTS5 virtual table indexing all 8 memory types
    - Write-ahead sync: every memory write updates JSON + SQLite atomically
    - `rebuild_index()` command rebuilds from JSON (source of truth)

- [x] **7.2** Create intent plugin `app/brain/plugins/temporal_query.py` (for Phase 8 temporal search)
  - `TEMPORAL_QUERY`: extract time range, domains for cross-domain queries

- [x] **7.3** Update `app/brain/handlers.py`, `app/brain/intent_types.py`, `app/brain/core.py`
  - Route `TEMPORAL_QUERY` (stub for Phase 8 integration)

- [x] **7.4** Contract tests `test_services/test_search_fts5.py`
  - FTS5 index creation, unified index across all types
  - Search parity: NL results match legacy substring baseline
  - Structured filters: type, date range, confidence, relations
  - Performance: <100ms p95 on 5k entries
  - Rebuild command verification

- [x] **7.5** Golden master regression — all 354 pass

---

## Phase 8 — Cross-Domain Intelligence (~400 lines)

**Target**: `TemporalPlugin`, `PatternsPlugin`, `ContextPlugin` + context enrichment in core

### Tasks

- [x] **8.1** Create `app/services/plugins/temporal.py`
  - `TemporalPlugin` with: `query_by_timerange(domains[], start, end)` → fused sorted results
  - Support empty domain filters, year tabs (2026-2035) data-ready

- [x] **8.2** Create `app/services/plugins/patterns.py`
  - `PatternsPlugin` with: `detect_recurring_patterns(domains[])` → themes + suggested planner tasks
  - Return empty list when no patterns found

- [x] **8.3** Create `app/services/plugins/context.py`
  - `ContextPlugin` with: `enrich_prompt(intent, entities, token_budget=1000)` → formatted context string
  - Relevance scoring: recency*0.3 + confidence*0.3 + relation_density*0.2 + type_priority*0.2
  - Token budget enforcement with relevance ranking

- [x] **8.4** Update `app/brain/core.py`
  - Call `ContextPlugin.enrich_prompt()` before Ollama call
  - Pass enriched context to LLM

- [x] **8.5** Create intent plugin `app/brain/plugins/pattern_suggest.py`
  - `PATTERN_SUGGEST`: surface detected patterns as suggestions

- [x] **8.6** Update `app/brain/handlers.py`, `app/brain/intent_types.py`
  - Handlers for `TEMPORAL_QUERY`, `PATTERN_SUGGEST`

- [x] **8.7** Contract tests `test_services/test_temporal_plugin.py`, `test_patterns_plugin.py`, `test_context_plugin.py`
  - Cross-domain temporal fusion, pattern detection, token budget enforcement
  - E2E: conversation → decision → prediction → outcome → lesson → reflection → identity update

- [x] **8.8** Performance test: ContextPlugin reduces LLM tokens by ≥30%

- [x] **8.9** Golden master regression — all 354 pass

---

## Cross-Phase Requirements (Every Phase)

- [x] **X.1** All 354 golden master tests pass (`pytest tests/ -k "golden"`)
- [x] **X.2** Per-phase contract tests added and passing
- [x] **X.3** No regression on voice.py, Whisper, TTS, audio thresholds
- [x] **X.4** Code follows existing patterns (ServicePlugin dataclass, registry auto-discovery)
- [x] **X.5** PR <400 lines changed, chained via stacked-to-main
- [x] **X.6** Run `sdd-archive` before next phase begins

---

## Delivery Gates

| Phase | Review Budget | Merge Gate |
|-------|---------------|------------|
| 1-6   | 800 lines     | Golden master + contract tests + migration verification |
| 7     | 800 lines     | + FTS5 parity + performance <100ms p95 |
| 8     | 800 lines     | + E2E scenarios + token reduction ≥30% |

---

## Rollback Reference (from Proposal)

| Phase | Rollback Action |
|-------|-----------------|
| 1 | Delete new plugin files; revert `MemoryPlugin`; restore `memories.json` from backup |
| 2-6 | Remove phase plugin; revert intent registry additions |
| 7 | Drop SQLite; revert `SearchPlugin` to JSON orchestration |
| 8 | Remove intelligence plugins; core unchanged |

**Full rollback**: `git revert` the 8 PRs in reverse order.

---

## Open Questions (from Design)

- [x] **Token budget default**: Confirm exact default (~1000 tokens) and config location
- [x] **Encryption passphrase UX**: When/how user provides passphrase (first run? settings? CLI?)
- [x] **Relation suggestion engine**: Phase for embedding-based relation suggestions? What model?
- [x] **Conflict detection trigger**: Automatic (embedding similarity) or manual? Phase?
- [x] **Year tab UI contract**: What data shape does UI expect for 2026-2035 tabs?

---

## Skill Dependencies

- `sdd-apply` — implements tasks per phase
- `sdd-verify` — validates against specs
- `chained-pr` — manages stacked PRs (<400 lines each)
- `work-unit-commits` — reviewable work unit commits per phase
- `gentle-ai-bench` — journey verification for E2E scenarios

---

*Generated from proposal.md, design.md, and 14 spec files*