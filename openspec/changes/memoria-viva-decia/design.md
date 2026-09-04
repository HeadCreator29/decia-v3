# Design: Memoria Viva DECIA

## Technical Approach

Progressive 8-phase extension of DECIA's dual plugin architecture (service plugins + brain intent plugins) to transform flat JSON memory into a typed, temporal, searchable, self-reflective system. Each phase delivers a functional increment (<400 lines) while maintaining all 354 golden master tests. Phase 1-6 extend JSON schema additively; Phase 7 migrates search backend to SQLite FTS5; Phase 8 adds cross-domain intelligence.

## Architecture Decisions

### Decision: Plugin Interface Pattern

| Option | Tradeoff | Decision |
|--------|----------|----------|
| Extend `ServicePlugin` dataclass with new fields | Breaks existing plugins | **Rejected** |
| Add new methods to `MemoryPlugin` class | Maintains backward compat; no interface change | **Chosen** |
| Create new plugin classes per phase | Clean separation; registry auto-discovers | **Chosen for new plugins (Decision, Prediction, etc.)** |

**Rationale**: Service plugins use a dataclass (`ServicePlugin`) with `execute(context)` — not a class hierarchy. New plugins are new `ServicePlugin` instances registered via `ServiceRegistry`. Existing `MemoryPlugin` class is extended with new methods (`create_typed`, `get_by_type`, etc.) while keeping `execute()` for backward compat.

### Decision: Data Migration Strategy (JSON → SQLite)

| Option | Tradeoff | Decision |
|--------|----------|----------|
| Big-bang migration to SQLite | Risk of data loss; breaks golden tests | **Rejected** |
| Dual-write during transition | Complex; sync issues | **Rejected** |
| Phase 1-6: JSON v2 (additive); Phase 7: SQLite FTS5 backend only | Zero risk; JSON remains source of truth; FTS5 is index | **Chosen** |

**Rationale**: JSON files stay the authoritative store through Phase 6. Phase 7 introduces SQLite FTS5 as a *search index only* — writes go to both JSON and SQLite atomically. Rebuild command handles drift.

### Decision: Encryption Key Management

| Option | Tradeoff | Decision |
|--------|----------|----------|
| External key management (AWS KMS, etc.) | Adds deps; cloud dependency | **Rejected** |
| Per-user passphrase derived key (PBKDF2) | Local-only; no cloud; keys never leave process | **Chosen** |
| Per-memory-type key | Over-engineered; same passphrase | **Rejected** |

**Rationale**: Specs mandate "keys derive from user passphrase; no cloud; local-only". PBKDF2 with per-process salt, keys held only in memory during encryption/decryption.

### Decision: Cross-Plugin Communication

| Option | Tradeoff | Decision |
|--------|----------|----------|
| Direct imports between plugins | Creates coupling; breaks isolation | **Rejected** |
| Event bus / pub-sub | Adds framework; overkill | **Rejected** |
| `ServiceRegistry.discover(category)` + explicit dependency injection | Uses existing pattern; explicit deps | **Chosen** |

**Rationale**: `SearchPlugin` already takes `IdentityPlugin`, `UserPlugin`, `HistoryPlugin`, `MemoryPlugin` in `__init__`. New plugins follow same pattern — dependencies injected at construction, discovered via registry.

### Decision: Intent Classification Extension

| Option | Tradeoff | Decision |
|--------|----------|----------|
| Modify existing intent plugins | Risks regression on 354 tests | **Rejected** |
| Add new intent plugins (`decision_create.py`, etc.) | Zero impact on existing; registry auto-loads | **Chosen** |
| Single "MEMORIA_VIVA" mega-intent | Loses granularity; harder to test | **Rejected** |

**Rationale**: Brain intent plugins are independent files. Adding 11 new intent plugins (DECISION_CREATE, PREDICTION_CREATE, REFLECTION_APPROVE, etc.) follows existing pattern — zero modification to existing plugins.

## Data Flow

```
┌─────────────────┐     ┌──────────────────┐     ┌────────────────────┐
│   User Input    │────▶│  Intent Layer    │────▶│  Handler / Plugin  │
│  (voice/text)   │     │  (classify)      │     │  (execute)         │
└─────────────────┘     └──────────────────┘     └─────────┬──────────┘
                                                           │
                              ┌────────────────────────────┼────────────────────────────┐
                              ▼                            ▼                            ▼
                       ┌───────────────┐            ┌───────────────┐            ┌───────────────┐
                       │ MemoryPlugin  │            │DecisionPlugin │            │SearchPlugin   │
                       │ (typed CRUD)  │            │ (structured)  │            │ (FTS5 index)  │
                       └───────┬───────┘            └───────┬───────┘            └───────┬───────┘
                               │                            │                            │
                               ▼                            ▼                            ▼
                       ┌─────────────────────────────────────────────────────────────────┐
                       │                    JSON Files (source of truth)                 │
                       │  memories.json  │ decisions.json │ predictions.json │ ...       │
                       └─────────────────────────────────────────────────────────────────┘
                                          │
                                          ▼ (Phase 7+)
                               ┌───────────────────────┐
                               │   SQLite FTS5 Index   │
                               │  (search acceleration)│
                               └───────────────────────┘
```

## File Changes

| File | Action | Description |
|------|--------|-------------|
| `app/services/plugins/memory.py` | Modify | Extend `MemoryPlugin` with `create_typed`, `get_by_type`, `get_by_confidence_range`, `add_relation`, `update_confidence`, `search_by_content`, `migrate_legacy` |
| `app/services/plugins/search.py` | Modify | Extend `SearchPlugin` with `query`, `filter_by_type`, `filter_by_date_range`, `filter_by_confidence`, `filter_by_relations`; Phase 7: add FTS5 backend |
| `app/services/plugins/decision.py` | Create | New `DecisionPlugin` with CRUD, status lifecycle, linking |
| `app/services/plugins/prediction.py` | Create | New `PredictionPlugin` with horizons, status, review scheduling |
| `app/services/plugins/learning.py` | Create | New `LearningPlugin` with auto-generation from outcomes |
| `app/services/plugins/reflection.py` | Create | New `ReflectionPlugin` with draft→approve flow, encryption |
| `app/services/plugins/identity_core.py` | Create | New `IdentityCorePlugin` with versioning, audit trail, ceremony |
| `app/services/plugins/temporal.py` | Create | New `TemporalPlugin` with `query_by_timerange` across domains |
| `app/services/plugins/patterns.py` | Create | New `PatternsPlugin` with `detect_recurring` → planner tasks |
| `app/services/plugins/context.py` | Create | New `ContextPlugin` with `enrich_prompt` + token budget |
| `app/services/plugins/encryption.py` | Create | Shared encryption service (PBKDF2, per-type policy) |
| `app/services/archive.py` | Modify | Add save/load for new JSON files; migration tool entry point |
| `app/brain/plugins/decision_create.py` | Create | `DECISION_CREATE` intent patterns |
| `app/brain/plugins/decision_confirm.py` | Create | `DECISION_CONFIRM` intent patterns |
| `app/brain/plugins/prediction_create.py` | Create | `PREDICTION_CREATE` intent patterns |
| `app/brain/plugins/prediction_review.py` | Create | `PREDICTION_REVIEW` intent patterns |
| `app/brain/plugins/learning_create.py` | Create | `LEARNING_CREATE` intent patterns |
| `app/brain/plugins/reflection_create.py` | Create | `REFLECTION_CREATE` intent patterns |
| `app/brain/plugins/reflection_approve.py` | Create | `REFLECTION_APPROVE` intent patterns |
| `app/brain/plugins/identity_propose.py` | Create | `IDENTITY_PROPOSE` intent patterns |
| `app/brain/plugins/identity_approve.py` | Create | `IDENTITY_APPROVE` intent patterns |
| `app/brain/plugins/temporal_query.py` | Create | `TEMPORAL_QUERY` intent patterns |
| `app/brain/plugins/pattern_suggest.py` | Create | `PATTERN_SUGGEST` intent patterns |
| `app/brain/handlers.py` | Modify | Add handlers for new intents (decision, prediction, reflection, identity) |
| `app/brain/core.py` | Modify | Route new intents; call `ContextPlugin.enrich_prompt()` before Ollama |
| `app/brain/intent_types.py` | Modify | Add new intent constants |
| `data/archive/migrations/migrate_memories_v2.py` | Create | One-shot migration script (idempotent, dry-run, backup) |
| `data/archive/migrations/reclassify_cli.py` | Create | Batch re-classification CLI with preview |

## Interfaces / Contracts

### MemoryPlugin v2 (Extended)

```python
class MemoryPlugin:
    # Existing execute() unchanged for backward compat
    
    def create_typed(self, content: str, type: str, confidence: float = 0.7,
                     relations: list = None, encryption: str = "optional") -> dict:
        """Create memory with full typed schema v2."""
    
    def get_by_type(self, type: str) -> list:
        """Filter memories by type (FACT, MEMORY, DECISION, GOAL, PREDICTION, LESSON, INTERPRETATION, UNKNOWN)."""
    
    def get_by_confidence_range(self, min_conf: float, max_conf: float) -> list:
        """Filter memories by confidence range."""
    
    def add_relation(self, source_id: str, target_id: str, relation_type: str) -> dict:
        """Add relation: relates-to | supports | contradicts | supersedes."""
    
    def update_confidence(self, memory_id: str, confidence: float) -> dict:
        """Update confidence score (0.0-1.0)."""
    
    def search_by_content(self, query: str, filters: dict = None) -> list:
        """Content search with optional type/date/confidence filters."""
    
    def migrate_legacy(self, default_type: str = "MEMORY", default_confidence: float = 0.7) -> dict:
        """One-shot migration: enrich all entries with v2 fields. Returns MigrationReport."""
```

### DecisionPlugin (New)

```python
class DecisionPlugin:
    def create(self, problem: str, arguments: list, decision: str, 
               rationale: str, confidence: float = 0.7) -> dict:
        """Create decision with status OPEN."""
    
    def confirm(self, decision_id: str, outcome: str, learning: str) -> dict:
        """Transition to CONFIRMED/FAILED/PARTIAL/CANCELLED."""
    
    def get_by_status(self, status: str) -> list:
        """Query by status."""
    
    def link_memory(self, decision_id: str, memory_id: str, relation: str) -> None:
        """Link decision to contributing memories."""
```

### PredictionPlugin (New)

```python
class PredictionPlugin:
    def create(self, prediction_text: str, horizons: list, confidence: float, 
               reasons: list) -> dict:
        """Create prediction with 3 horizons (short/medium/long up to 2035)."""
    
    def update_status(self, prediction_id: str, status: str) -> dict:
        """Status: OPEN → CONFIRMED | FAILED | PARTIAL | CANCELLED."""
    
    def schedule_review(self, prediction_id: str, review_date: str) -> None:
        """Set review_date for horizon tracking."""
    
    def get_due_reviews(self) -> list:
        """Predictions whose review_date has passed."""
    
    def resolve(self, prediction_id: str, outcome: str, learning: str) -> dict:
        """Finalize with outcome + auto-generate lesson."""
```

### SearchPlugin v2 (Extended)

```python
class SearchPlugin:
    # Existing execute() unchanged (API compatibility)
    
    def query(self, text: str, filters: dict = None) -> dict:
        """NL search across unified FTS5 index."""
    
    def filter_by_type(self, type: str) -> "SearchPlugin":
        """Chainable filter."""
    
    def filter_by_date_range(self, start: str, end: str) -> "SearchPlugin":
        """Chainable filter."""
    
    def filter_by_confidence(self, min: float, max: float) -> "SearchPlugin":
        """Chainable filter."""
    
    def filter_by_relations(self, relation_type: str, target_id: str) -> "SearchPlugin":
        """Chainable filter."""
```

### ContextPlugin (New, Phase 8)

```python
class ContextPlugin:
    def enrich_prompt(self, intent: str, entities: dict, token_budget: int = 1000) -> str:
        """Assemble relevant memories into structured context block for LLM.
        
        Relevance scoring: recency * 0.3 + confidence * 0.3 + 
        relation_density * 0.2 + type_priority * 0.2
        Returns formatted context string within token_budget.
        """
```

### Encryption Service (Shared)

```python
class EncryptionService:
    def __init__(self, passphrase: str):
        self._key = self._derive_key(passphrase)  # PBKDF2
    
    def encrypt(self, plaintext: str) -> str:
        """AES-GCM encrypt; return base64(ciphertext + nonce + tag)."""
    
    def decrypt(self, ciphertext_b64: str) -> str:
        """Decrypt; raise if key mismatch."""
    
    @staticmethod
    def policy_for_type(memory_type: str) -> str:
        """Return 'none' | 'optional' | 'mandatory' per spec."""
```

## Testing Strategy

| Layer | What to Test | Approach |
|-------|--------------|----------|
| Unit | Each plugin method (CRUD, validation, edge cases) | `test_services/test_<plugin>.py` per phase |
| Unit | Encryption service (policy, key derivation, isolation) | `test_services/test_encryption.py` |
| Unit | Migration tool (idempotent, dry-run, backup, round-trip) | `test_migrations/test_migrate_v2.py` |
| Integration | Intent → handler → plugin → storage | `test_handlers.py` new intent flows |
| Integration | SearchPlugin FTS5 parity with JSON baseline | `test_services/test_search_fts5.py` |
| E2E | Conversation → decision → prediction → outcome → lesson → reflection → identity update | `test_e2e/test_memoria_viva_flow.py` |
| Performance | FTS5 search <100ms p95 on 5k entries | Benchmark in `test_services/test_search_fts5.py` |
| Performance | ContextPlugin token reduction ≥30% | Measure tokens with/without in E2E test |
| Regression | All 354 golden master tests pass every phase | CI gate: `pytest tests/ -k "golden"` |

## Threat Matrix

N/A — no routing, shell, subprocess, VCS/PR automation, executable-file classification, or process-integration boundary. This change is pure data architecture and plugin extension.

## Migration / Rollout

**Phase 1 (Typed Memory Foundation)**:
1. Run `python data/archive/migrations/migrate_memories_v2.py --dry-run` → verify report
2. Run migration → creates `memories.pre-migration.backup.json`
3. Verify 1300+ entries enriched; `get_by_type("MEMORY")` returns all
4. Run `reclassify_cli.py --preview` → bulk update known categories

**Phase 7 (FTS5)**:
1. New `SearchPlugin` initializes FTS5 on first use
2. Write-ahead sync: every memory write updates both JSON and SQLite
3. `search_rebuild` command rebuilds index from JSON (source of truth)
4. Parity test validates NL results match legacy substring baseline

**Rollback per Phase** (from proposal):
- Phase 1: Delete new plugin files; revert `MemoryPlugin`; restore `memories.json` from backup
- Phase 2-6: Remove phase plugin; revert intent registry; no data migration needed
- Phase 7: Drop SQLite; revert `SearchPlugin` to JSON orchestration
- Phase 8: Remove intelligence plugins; core unchanged

## Open Questions

- [ ] **Token budget default**: Proposal says "configurable, default ~1000 tokens". Confirm exact default and config location.
- [ ] **Encryption passphrase UX**: When/how does user provide passphrase? First run? Settings? CLI?
- [ ] **Relation suggestion engine**: Spec says "embedding suggestions" for relations. Is this Phase 1 or later? What embedding model?
- [ ] **Conflict detection trigger**: Is contradiction detection automatic (embedding similarity) or manual? Phase?
- [ ] **Year tab UI contract**: Phase 8 "year tabs (2026-2035) UI-ready" — what data shape does UI expect?

---
*Generated by sdd-design sub-agent*