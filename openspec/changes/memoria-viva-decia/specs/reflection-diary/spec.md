# Delta for Reflection Diary

## ADDED Requirements

### Requirement: Reflection Schema
The system MUST store reflections with: id, date, draft_content, approved_content, status (DRAFT|APPROVED|ARCHIVED), related_conversation_id, user_edited.

#### Scenario: Auto-draft after conversation
- GIVEN a conversation completes
- WHEN reflection is generated
- THEN a DRAFT reflection is created with draft_content
- AND related_conversation_id links to the conversation
- AND user_edited is false

#### Scenario: User approval flow
- GIVEN a DRAFT reflection
- WHEN user edits and approves
- THEN approved_content is set to the edited version
- AND status transitions to APPROVED
- AND user_edited is true

### Requirement: Reflection Status Lifecycle
Status MUST progress: DRAFT → APPROVED|ARCHIVED. Archived reflections are immutable.

#### Scenario: User rejects draft
- GIVEN a DRAFT reflection
- WHEN user discards it
- THEN status becomes ARCHIVED
- AND draft_content is preserved for audit

#### Scenario: Mandatory encryption
- GIVEN a reflection with INTERPRETATION or LESSON type
- WHEN stored
- THEN encryption is mandatory and applied
- AND key never leaves the process

### Requirement: Encrypted Persistence
Reflections with INTERPRETATION or LESSON type MUST be encrypted at rest. Encryption keys MUST derive from user passphrase.

#### Scenario: Encryption applied
- GIVEN a reflection requiring encryption
- WHEN persisted
- THEN content is encrypted
- AND decryption requires the user passphrase

## ACCEPTANCE CRITERIA
- Post-conversation drafts auto-generated
- User edit and approval flow functional
- Encryption enforced per policy
- All golden master tests pass