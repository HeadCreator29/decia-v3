# Delta for Typed Memory

## ADDED Requirements

### Requirement: Typed Memory Schema v2
The system MUST support 8 memory types: FACT, MEMORY, DECISION, GOAL, PREDICTION, LESSON, INTERPRETATION, UNKNOWN. Every memory MUST include: id, content, date, source, type, confidence (0.0-1.0), relations (array of {target_id, relation_type}), encryption_flag, metadata, version, created_at, updated_at. Relations MUST use types: relates-to, supports, contradicts, supersedes.

#### Scenario: Creating a typed memory
- GIVEN a user provides content and type FACT
- WHEN the system creates the memory
- THEN the memory includes all required fields with confidence defaulting to 0.7
- AND type is validated against the 8-type enum

#### Scenario: Memory with relations
- GIVEN memories A and B exist
- WHEN a relation {type: "supports", target_id: B.id} is added to A
- THEN A's relations array contains the reference to B
- AND B is not modified

### Requirement: Migration Tool
The system MUST provide a one-shot migration that reads `memories.json` and enriches each entry: type=MEMORY, confidence=0.7, source=migration, version=1, relations=[], encryption=optional. The tool MUST be idempotent (detect source=migration), create a backup `memories.pre-migration.backup.json`, and support a dry-run flag.

#### Scenario: Idempotent migration run
- GIVEN memories.json already migrated (source=migration present)
- WHEN migration tool runs again
- THEN no entries are modified or duplicated
- AND backup is not overwritten

#### Scenario: Dry-run migration
- GIVEN 1300+ existing memories
- WHEN dry-run flag is set
- THEN no files are written
- AND a report of changes is returned

### Requirement: MemoryPlugin v2 Contract
The extended MemoryPlugin MUST implement: create_typed(), get_by_type(), get_by_confidence_range(), add_relation(), update_confidence(), search_by_content(). All existing functions MUST remain backward compatible and unchanged.

#### Scenario: Backward-compatible read
- GIVEN existing code calls legacy memory functions
- WHEN memory-plugin v2 is loaded
- THEN legacy functions return identical results
- AND no behavioral regression occurs

### Requirement: Batch Re-classification
The system MUST provide a CLI tool to bulk-update memory types for known categories (facts, decisions, goals). Results MUST be previewable before applying.

#### Scenario: Preview re-classification
- GIVEN memories matching fact patterns
- WHEN re-classification preview runs
- THEN a summary of affected memories is shown
- AND no changes are persisted

## MODIFIED Requirements

### Requirement: Memory CRUD Operations
Memory creation and retrieval operations now support the extended schema (type, confidence, relations, encryption, version). All existing fields are preserved and new fields default per policy.
(Previously: schema was {id, text, date, type, source} with no confidence, relations, or versioning)

#### Scenario: Create memory with defaults
- GIVEN a new memory is created without type or confidence
- WHEN defaults are applied
- THEN type defaults to MEMORY, confidence defaults to 0.7
- AND version defaults to 1

## REMOVED Requirements

### Requirement: Flat memory schema
The flat {id, text, date, type, source} schema is replaced by the typed schema v2.
(Reason: Insufficient structure for typed memory, confidence, relations, and cross-domain intelligence)
(Migration: Legacy field "text" maps to "content"; old data preserved and enriched by migration tool)

## RENAMED Requirements

### Requirement: Memory text → Memory content
The "text" field is renamed to "content" for semantic clarity across all memory types.
(Reason: "content" is more precise and inclusive of all memory types)
(Migration: Migration tool maps "text" → "content"; backward-compatible aliases may exist during transition)

## ACCEPTANCE CRITERIA
- All 354 golden master tests pass after Phase 1
- Migration completes for 1300+ entries with zero data loss
- New fields queryable via get_by_type() and get_by_confidence_range()
- Migration idempotent and dry-run supported