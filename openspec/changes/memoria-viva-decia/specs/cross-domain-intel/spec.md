# Delta for Cross-Domain Intelligence

## ADDED Requirements

### Requirement: TemporalPlugin
The system MUST provide query_by_timerange(domains[], start, end) → fused sorted results across all memory types.

#### Scenario: Cross-domain temporal query
- GIVEN memories of multiple types across 2026-2035
- WHEN query_by_timerange([DECISION, PREDICTION], 2026-01-01, 2026-12-31) runs
- THEN results from both domains are fused
- AND sorted chronologically

#### Scenario: Empty domain filter
- GIVEN a domain with no memories in range
- WHEN query_by_timerange runs
- THEN empty results returned without error

### Requirement: PatternsPlugin
The system MUST detect recurring patterns across memory types and suggest planner tasks.

#### Scenario: Pattern detection
- GIVEN memories showing repeated decision patterns
- WHEN detect_recurring_patterns([DECISION, LESSON]) runs
- THEN recurring themes are identified
- AND suggested planner tasks are generated

#### Scenario: No patterns found
- GIVEN diverse memories with no repetition
- WHEN pattern detection runs
- THEN empty pattern list is returned

### Requirement: ContextPlugin
The system MUST enrich prompts with relevant history: enrich_prompt(intent, entities) → relevant history injection for Ollama. Token budget MUST be enforced with relevance ranking.

#### Scenario: Context enrichment
- GIVEN intent="problem_solving" and entities=["project_x"]
- WHEN enrich_prompt runs
- THEN relevant memories are injected into the prompt
- AND token budget is respected

#### Scenario: Token budget enforcement
- GIVEN more relevant memories than token budget allows
- WHEN enrich_prompt runs
- THEN highest-relevance memories are selected
- AND total tokens stay within budget

## ACCEPTANCE CRITERIA
- Temporal queries fuse cross-domain results
- Pattern detection identifies recurring themes
- Context assembly respects token budget
- Context bundles reduce LLM tokens by ≥30%
- All golden master tests pass