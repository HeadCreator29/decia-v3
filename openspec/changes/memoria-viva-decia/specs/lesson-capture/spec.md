# Delta for Lesson Capture

## ADDED Requirements

### Requirement: Lesson Schema
The system MUST store lessons with: id, date, trigger_id (decision/prediction ref), expected, actual, delta, lesson, future_considerations, confidence.

#### Scenario: Auto-generated lesson from prediction outcome
- GIVEN a prediction reaches CONFIRMED or FAILED status
- WHEN outcome is observed
- THEN a lesson is auto-generated with trigger_id linking to the prediction
- AND expected, actual, and delta are populated

#### Scenario: Manual lesson creation
- GIVEN a user identifies a takeaway
- WHEN lesson is manually created
- THEN all fields are populated including future_considerations
- AND confidence is set

### Requirement: Lesson Trigger Linkage
A lesson MUST reference its trigger via trigger_id pointing to a decision or prediction id.

#### Scenario: Trigger validation
- GIVEN a lesson with trigger_id
- WHEN trigger_id is validated
- THEN it references an existing decision or prediction
- AND the lesson is linked to that memory

#### Scenario: Orphan trigger
- GIVEN a lesson with invalid trigger_id
- WHEN validation runs
- THEN the lesson is flagged as having an unresolved trigger
- AND confidence is reduced

### Requirement: Delta Calculation
The delta MUST represent the difference between expected and actual outcomes.

#### Scenario: Positive delta
- GIVEN expected=80%, actual=95%
- WHEN delta is calculated
- THEN delta is positive (+15%)
- AND future_considerations reflect the improvement

## ACCEPTANCE CRITERIA
- Lessons link to decisions/predictions via trigger_id
- Auto-generation from prediction resolutions works
- Manual creation supported
- All golden master tests pass