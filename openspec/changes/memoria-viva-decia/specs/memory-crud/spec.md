# Delta for Memory CRUD

## ADDED Requirements

### Requirement: Extended Memory Schema
Memory CRUD operations now support the extended schema: type (8-type enum), confidence (0.0-1.0), relations (array of {target_id, relation_type}), encryption_flag, version, created_at, updated_at. All existing fields preserved.

#### Scenario: Create with extended fields
- GIVEN a memory creation call
- WHEN type and confidence are provided
- THEN the memory stores all extended fields
- AND defaults applied for omitted fields

#### Scenario: Query by type and confidence
- GIVEN memories with varying types and confidence
- WHEN get_by_type(FACT) or get_by_confidence_range(0.5, 1.0) runs
- THEN only matching memories are returned

### Requirement: Encryption Policy Enforcement
Memory CRUD MUST enforce per-type encryption: FACT=none, MEMORY/DECISION/PREDICTION/GOAL=optional, INTERPRETATION/LESSON/IDENTITY=mandatory.

#### Scenario: Mandatory encryption applied
- GIVEN an INTERPRETATION memory
- WHEN stored
- THEN encryption is applied automatically
- AND key never leaves the process

## MODIFIED Requirements

### Requirement: Memory CRUD Operations
Memory operations now support the full typed schema v2 with confidence, relations, and encryption fields alongside the original {id, text, date, type, source}.
(Previously: schema was {id, text, date, type, source} — flat, no confidence, no relations)

#### Scenario: Backward-compatible create
- GIVEN legacy code creates a memory without type
- WHEN operation completes
- THEN type defaults to MEMORY
- AND confidence defaults to 0.7

## ACCEPTANCE CRITERIA
- Extended schema functional
- Encryption policies enforced
- Backward compatibility maintained
- All golden master tests pass