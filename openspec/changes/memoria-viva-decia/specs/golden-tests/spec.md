# Delta for Golden Master Tests

## ADDED Requirements

### Requirement: Phase 1 Test Suite
All 354 existing golden master tests MUST pass after Phase 1. NEW contract tests MUST validate typed memory CRUD and migration.

#### Scenario: Golden master regression
- GIVEN Phase 1 complete
- WHEN 354 golden master tests run
- THEN all pass unchanged
- AND zero regression detected

#### Scenario: Migration verification
- GIVEN 1300+ memories migrated
- WHEN round-trip test runs
- THEN original → migrated → query = identical semantics

### Requirement: Phase 2-6 Test Suites
Each phase (Decision, Prediction, Lesson, Reflection, Identity) MUST add per-plugin contract tests in test_services/test_<plugin>.py.

#### Scenario: Per-plugin contracts
- GIVEN DecisionPlugin implemented
- WHEN test_services/test_decision_plugin.py runs
- THEN CRUD, validation, and edge cases covered

### Requirement: Phase 7 Test Suite
FTS5 search tests MUST verify parity with legacy substring matching. Performance tests MUST confirm <100ms p95 on 5k entries.

#### Scenario: Search parity
- GIVEN legacy substring baseline results
- WHEN FTS5 search runs
- THEN results match the baseline

#### Scenario: Performance benchmark
- GIVEN 5k indexed entries
- WHEN p95 latency measured
- THEN <100ms

### Requirement: Phase 8 Test Suite
E2E scenarios MUST cover: conversation → decision → prediction → outcome → lesson → reflection → identity update. Context assembly MUST reduce LLM tokens by ≥30%.

#### Scenario: E2E flow
- GIVEN a complete conversation lifecycle
- WHEN E2E scenario runs
- THEN all phases produce correct outputs

#### Scenario: Token reduction
- GIVEN context assembly with and without ContextPlugin
- WHEN token count measured
- THEN ContextPlugin reduces tokens by ≥30%

## ACCEPTANCE CRITERIA
- 354 golden tests pass each phase
- Contract tests per plugin
- Migration round-trip verified
- FTS5 parity confirmed
- E2E scenarios pass
- Token reduction ≥30%