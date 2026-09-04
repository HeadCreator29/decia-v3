# Delta for Identity Versioning

## ADDED Requirements

### Requirement: Identity Core Schema
The system MUST store identity with: version, name, origin, purpose, mission, values[], principles[], rules[], limits[], deca_relation, creator_relation, audit_log[{version, date, changes, approved_by}].

#### Scenario: Creating initial identity
- GIVEN a new DECIA instance
- WHEN identity is initialized
- THEN version is 1 with all required fields populated
- AND audit_log contains the creation entry

#### Scenario: Identity evolution
- GIVEN identity version N
- WHEN a change is approved
- THEN version increments to N+1
- AND audit_log entry records the change with approved_by

### Requirement: Audit Trail
Every identity change MUST be recorded in audit_log with version, date, changes, and approved_by fields.

#### Scenario: Audit entry creation
- GIVEN identity is updated
- WHEN the update is approved
- THEN audit_log.append({version, date, changes, approved_by})
- AND previous version preserved in history

#### Scenario: User approval required
- GIVEN an identity change proposal
- WHEN user does not approve
- THEN identity version remains unchanged
- AND audit_log records the rejection

### Requirement: Versioned Identity Source
Identity MUST be the authoritative source of truth for DECIA's self-description. Changes MUST require user ceremony.

#### Scenario: Hard limits and ceremony
- GIVEN a change to values or principles
- WHEN it exceeds defined limits
- THEN a ceremony is triggered
- AND user must explicitly approve

## ACCEPTANCE CRITERIA
- Identity changes versioned
- User approval required for changes
- Audit trail complete and immutable
- All golden master tests pass