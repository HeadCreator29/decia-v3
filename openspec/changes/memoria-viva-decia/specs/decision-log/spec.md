# Delta for Decision Log

## ADDED Requirements

### Requirement: Decision Schema
The system MUST store decisions with: id, date, problem, arguments[], decision, rationale, outcome, learning, status (OPEN|CONFIRMED|FAILED|PARTIAL|CANCELLED), related_memory_ids[], confidence.

#### Scenario: Creating a decision from conversation
- GIVEN a conversation identifies a decision point
- WHEN DECISION_CREATE intent fires
- THEN a decision record is created with status OPEN
- AND related_memory_ids link to contributing memories

#### Scenario: Confirming a decision
- GIVEN a decision with status OPEN
- WHEN evidence confirms the choice
- THEN status transitions to CONFIRMED
- AND outcome and learning fields are populated

### Requirement: Decision Status Lifecycle
A decision MUST progress through: OPEN → CONFIRMED|FAILED|PARTIAL|CANCELLED. Each transition MUST be auditable with timestamps.

#### Scenario: Decision fails
- GIVEN a decision with status OPEN
- WHEN outcomes contradict the decision
- THEN status transitions to FAILED
- AND learning field captures the failure reason

#### Scenario: Partial decision
- GIVEN a decision with status OPEN
- WHEN only some arguments validate
- THEN status becomes PARTIAL
- AND confidence is reduced

### Requirement: Decision Arguments and Rationale
Arguments MUST capture the alternatives considered. Rationale MUST explain why the chosen path was selected.

#### Scenario: Multi-alternative decision
- GIVEN 3 alternatives considered
- WHEN decision is recorded
- THEN arguments[] contains all 3 alternatives
- AND rationale explains the selection

## ACCEPTANCE CRITERIA
- Decisions queryable by date and topic
- Status transitions validated
- All 354 golden master tests pass
- Intent DECISION_CREATE functional