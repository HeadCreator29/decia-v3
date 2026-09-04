# Delta for Encryption Policy

## ADDED Requirements

### Requirement: Per-Type Encryption
Encryption MUST be enforced per memory type: FACT=none (MUST NOT encrypt), MEMORY/DECISION/PREDICTION/GOAL=optional (SHOULD encrypt when requested), INTERPRETATION/LESSON/IDENTITY=mandatory (MUST encrypt). Encryption keys MUST derive from user passphrase and never leave the process.

#### Scenario: Mandatory encryption applied
- GIVEN an INTERPRETATION memory stored
- WHEN encryption is applied
- THEN content is encrypted at rest
- AND decryption requires the user passphrase

#### Scenario: FACT not encrypted
- GIVEN a FACT memory stored
- WHEN encryption policy checked
- THEN no encryption is applied
- AND content remains plaintext

### Requirement: Key Management
Encryption keys MUST derive from user passphrase via a key derivation function. No cloud storage. No external key management.

#### Scenario: Key derivation
- GIVEN a user passphrase
- WHEN key is derived
- THEN a deterministic encryption key is produced
- AND the passphrase is not stored

#### Scenario: Key isolation
- GIVEN an encryption key in memory
- WHEN process memory inspected
- THEN key is not exposed in logs, errors, or exports

## ACCEPTANCE CRITERIA
- Per-type policy enforced
- FACT never encrypted
- INTERPRETATION/LESSON/IDENTITY always encrypted
- Keys never leave process
- All golden master tests pass