# Delta for Unified Search

## ADDED Requirements

### Requirement: SQLite + FTS5 Schema
The system MUST migrate search backend from JSON substring matching to SQLite with FTS5 virtual table. JSON remains the export format. All memory types MUST be indexed in a unified FTS5 table.

#### Scenario: FTS5 index creation
- GIVEN memories of all 8 types exist
- WHEN FTS5 index is built
- THEN all memory content is searchable via FTS5
- AND structured fields (type, date, confidence) are queryable

#### Scenario: Search parity
- GIVEN a search query
- WHEN FTS5 search runs
- THEN results match the legacy substring baseline
- AND structured filters refine results correctly

### Requirement: Dual Query Interface
Search MUST support both natural language queries and structured queries: query(text), filter_by_type(), filter_by_date_range(), filter_by_confidence(), filter_by_relations().

#### Scenario: Natural language search
- GIVEN user types a search query
- WHEN query() executes
- THEN relevant memories across all types are returned
- AND results ranked by relevance

#### Scenario: Structured filter combination
- GIVEN memories exist with various types and dates
- WHEN filter_by_type(FACT).filter_by_date_range(2024, 2026).filter_by_confidence(0.5, 1.0) runs
- THEN only matching memories are returned

#### Scenario: Relation-based search
- GIVEN memories with relations
- WHEN filter_by_relations("supports") runs
- THEN all memories supporting others are returned

### Requirement: Search Performance
Search MUST complete in <100ms p95 on 5k entries.

#### Scenario: Performance benchmark
- GIVEN 5k indexed memories
- WHEN a search query executes
- THEN p95 latency is under 100ms
- AND results are complete and correct

## ACCEPTANCE CRITERIA
- FTS5 index built and queryable
- NL and structured queries functional
- <100ms p95 on 5k entries
- All 354 golden master tests pass
- Search parity with legacy substring matching verified