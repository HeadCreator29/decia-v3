# Delta for Conflict Resolution

## ADDED Requirements

### Requirement: Conflict Object Schema
The system MUST store conflicts with: id, type, involved_memory_ids[], contradiction_type, resolution, date, status. Conflicts arise when memories contradict each other.

#### Scenario: Conflict detected
- GIVEN memory A with content X and memory B with content contradicting X
- WHEN contradiction is detected
- THEN a conflict object is created
- AND involved_memory_ids references both A and B

#### Scenario: Conflict resolution
- GIVEN a conflict with status OPEN
- WHEN user resolves it
- THEN resolution field is populated
- AND status transitions to RESOLVED

### Requirement: Contradiction Types
Contradiction_type MUST be one of: factual, interpretive, temporal, priority.

#### Scenario: Factual contradiction
- GIVEN two memories stating opposite facts
- WHEN classified
- THEN contradiction_type is "factual"
- AND both memories flagged accordingly

## ACCEPTANCE CRITERIA
- Conflict objects created and tracked
- All contradiction types supported
- Resolution workflow functional
- All golden master tests pass