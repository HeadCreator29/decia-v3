# Delta for Intent Classification

## ADDED Requirements

### Requirement: New Intents
The system MUST support 3 new intents: DECISION_CREATE, PREDICTION_CREATE, REFLECTION_APPROVE. These MUST be registered alongside existing MEMORY_CREATE and MEMORY_SEARCH.

#### Scenario: DECISION_CREATE intent
- GIVEN conversation content suggesting a decision
- WHEN intent classification runs
- THEN DECISION_CREATE is returned with confidence
- AND arguments are extracted

#### Scenario: PREDICTION_CREATE intent
- GIVEN conversation content suggesting a forecast
- WHEN intent classification runs
- THEN PREDICTION_CREATE is returned
- AND horizons are identified

#### Scenario: REFLECTION_APPROVE intent
- GIVEN a DRAFT reflection
- WHEN user approves
- THEN REFLECTION_APPROVE intent fires
- AND approved_content is set

### Requirement: Intent Regression
New intents MUST NOT affect existing intent classification accuracy. All existing intents MUST maintain their confidence thresholds.

#### Scenario: Existing intent unchanged
- GIVEN a MEMORY_CREATE query
- WHEN classified with new intents registered
- THEN confidence and classification match pre-change baseline
- AND no regression detected

## MODIFIED Requirements

### Requirement: Intent Classification
Intent classification now includes DECISION_CREATE, PREDICTION_CREATE, REFLECTION_APPROVE alongside existing MEMORY_CREATE and MEMORY_SEARCH. Classification accuracy must remain unchanged for existing intents.
(Previously: only MEMORY_CREATE / MEMORY_SEARCH intents)

#### Scenario: Full intent set
- GIVEN all intents registered
- WHEN classification runs
- THEN each intent returns correct type
- AND per-phase contract tests validate

## ACCEPTANCE CRITERIA
- 3 new intents functional
- No regression on existing intents
- Per-phase intent contract tests pass
- 354 golden master tests unchanged