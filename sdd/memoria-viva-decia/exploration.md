## Exploration: memoria-viva-decia

### Current State

DECIA currently has fragmented memory across multiple JSON files in `data/archive/`:
- **identity.json** — Static DECA identity (name, meaning, creator, origin, vision, values)
- **history.json** — Events with date, title, description (2 events currently)
- **user.json** — User profile (user_name, preferred_name)
- **memories.json** — 1300+ entries with id, date, time, description, type, title, recorded_at, timestamp
- **planner.json** — Events/reminders with id, kind, due_date, due_time, description, status, created_at

**Services Layer** (`app/services/`):
- `archive.py` (1254 lines) — Read-only archive with search, deduplication, canonical forms, temporal filters, save_memory()
- `planner.py` (442 lines) — Planner CRUD with atomic writes, deduplication, validation
- `services/plugins/` — Plugin architecture: IdentityPlugin, UserPlugin, HistoryPlugin, MemoryPlugin, PlannerPlugin, SearchPlugin

**Brain Layer** (`app/brain/`):
- `core.py` (693 lines) — Main thinking loop with intent classification and routing to handlers
- `intent_layer.py` (576 lines) — Intent classification orchestrator using PluginRegistry (16 intent plugins)
- `context.py` — ConversationContext with history, last_intent, last_topic, last_entity, conversation_mode
- `handlers.py` (1929 lines) — Deterministic handlers for all intents
- `plugins/` — 16 intent plugins (GREETING, MEMORY_CREATE, PLANNER_CREATE, etc.)

**Intent System**: Pattern-based classification (EXACT, PHRASE, REGEX, KEYWORD) with confidence scoring, entity extraction, and golden master tests for regression.

**Data Persistence**: JSON files only — no SQLite, no FTS5 index.

### Affected Areas

- `app/services/archive.py` — Core memory search/storage; would need new typed memory schema
- `app/services/planner.py` — Decision/prediction scheduling integration
- `app/services/plugins/` — New plugins needed: DecisionPlugin, PredictionPlugin, LearningPlugin, ReflectionPlugin, TemporalPlugin, PatternsPlugin, ContextPlugin, IdentityCorePlugin, SearchPlugin (FTS5)
- `app/brain/core.py` — Context injection point for enriched prompts
- `app/brain/intent_layer.py` — New intents for decision/prediction/learning/reflection
- `app/brain/plugins/` — New intent plugins for new memory types
- `app/brain/handlers.py` — New handlers for decision/prediction/learning/reflection flows
- `data/archive/` — New JSON files or migration to SQLite with FTS5
- `tests/` — Golden master tests for new intents and handlers

### Approaches

1. **Progressive Plugin Extension (Recommended)** — Extend existing plugin architecture incrementally
   - Pros: Zero breaking changes, follows existing patterns, each phase < 400 lines, chained PRs
   - Cons: JSON storage limits query flexibility; FTS5 requires SQLite migration
   - Effort: Medium (phased over 6-8 PRs)

2. **SQLite + FTS5 Migration First** — Migrate all storage to SQLite with FTS5, then build plugins
   - Pros: Unified query layer, full-text search native, better for decade-scale data
   - Cons: Large upfront change, breaks golden master tests, violates "no massive refactor" rule
   - Effort: High (single large PR, high risk)

3. **Hybrid: JSON + SearchPlugin with FTS5 Index** — Keep JSON for persistence, build separate FTS5 index
   - Pros: Preserves JSON compatibility, adds search capability
   - Cons: Dual-write complexity, sync issues, more code to maintain
   - Effort: Medium-High

### Recommendation

**Progressive Plugin Extension (Approach 1)** with phased SQLite migration:

1. **Phase 1**: Add typed memory fields to existing MemoryPlugin (type, confidence, relations) — JSON only
2. **Phase 2**: DecisionPlugin + Decision intent + handler (structured decision log)
3. **Phase 3**: PredictionPlugin + Future Engine (predictions with status tracking)
4. **Phase 4**: LearningPlugin (lessons from decision/prediction outcomes)
5. **Phase 5**: ReflectionPlugin (diary/reflections separate from facts)
6. **Phase 6**: IdentityCorePlugin (structured persistent identity source)
7. **Phase 7**: SearchPlugin with FTS5 (SQLite index for unified search)
8. **Phase 8**: TemporalPlugin + PatternsPlugin + ContextPlugin (cross-domain queries, routine detection, prompt enrichment)

Each phase < 400 lines, golden master tests preserved, chained PRs.

### Risks

- **JSON scalability**: 1300+ memories already; decade-scale will need SQLite/FTS5
- **Schema migration**: Existing memories lack type/confidence/relations — need migration strategy
- **Intent classification**: New intents (DECISION_CREATE, PREDICTION_CREATE, LEARNING_CREATE, REFLECTION_CREATE) must not regress existing classification
- **Context injection**: brain/core.py Ollama call must enrich with relevant history without token bloat
- **Cross-plugin communication**: ServiceRegistry pattern exists but needs extension for new plugin dependencies

### Ready for Proposal

**Yes** — The exploration is complete. The orchestrator should tell the user:

> "Exploration complete. Current architecture uses JSON files with a dual plugin system (brain intent plugins + service data plugins). Recommended approach: Progressive Plugin Extension over 8 phases, each < 400 lines, preserving golden master tests. Key decision: defer full SQLite/FTS5 migration to Phase 7 after typed memory foundation is stable. Ready to proceed to sdd-propose for memoria-viva-decia."