# Delta for Search Orchestration

## ADDED Requirements

### Requirement: SQLite FTS5 Backend
Search orchestration MUST use SQLite with FTS5 as the backend. JSON remains the export format. The SearchPlugin interface MUST remain unchanged.

#### Scenario: Backend migration
- GIVEN JSON-based search
- WHEN FTS5 backend is activated
- THEN SearchPlugin API calls return identical results
- AND FTS5 index is the source of truth for search

#### Scenario: Index sync
- GIVEN a new memory is written
- WHEN the FTS5 index is updated
- THEN the index reflects the new memory within the same transaction
- AND no drift occurs

### Requirement: Unified Index
A single FTS5 virtual table MUST index all 8 memory types. Search queries MUST span all types by default.

#### Scenario: Cross-type search
- GIVEN memories of all 8 types
- WHEN a search query executes
- THEN results from all types are included
- AND no type filtering unless requested

## MODIFIED Requirements

### Requirement: Search Orchestration
Search orchestration backend is swapped from JSON substring matching to SQLite FTS5. The external API remains unchanged — existing code calls SearchPlugin identically.
(Previously: JSON substring match on canonicalized content; no FTS5, no structured query)

#### Scenario: API compatibility
- GIVEN existing search calls
- WHEN FTS5 backend is active
- THEN all existing calls return equivalent results
- AND performance improves to <100ms p95

## ACCEPTANCE CRITERIA
- FTS5 backend functional
- API unchanged — zero regression
- Unified index across all types
- All golden master tests pass
- Search rebuild command available