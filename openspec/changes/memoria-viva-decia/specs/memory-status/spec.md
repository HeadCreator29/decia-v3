# Delta for Memory Status

## ADDED Requirements

### Requirement: Memory Status Field
Every memory MUST have a status field: confirmed|contradicted|superseded|disputed. Status MUST be validated against the enum.

#### Scenario: Memory confirmed
- GIVEN a newly created memory
- WHEN no contradictions found
- THEN status is confirmed

#### Scenario: Memory contradicted
- GIVEN a memory contradicted by another
- WHEN detection runs
- THEN status becomes contradicted
- AND conflict object linked

#### Scenario: Memory superseded
- GIVEN a memory replaced by a newer version
- WHEN supersession detected
- THEN status becomes superseded
- AND the superseding memory referenced

### Requirement: Status Transitions
Status MUST transition validly: confirmed → contradicted|superseded|disputed. Disputed memories require resolution.

#### Scenario: Valid transition
- GIVEN confirmed memory
- WHEN contradicted
- THEN status becomes contradicted

#### Scenario: Invalid transition prevented
- GIVEN disputed memory
- WHEN no resolution
- THEN status remains disputed
- AND cannot revert without resolution

## ACCEPTANCE CRITERIA
- Status field on all memories
- Validated enum values
- Status transitions enforced
- All golden master tests pass