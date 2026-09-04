# Delta for Prediction Tracking

## ADDED Requirements

### Requirement: Prediction Schema
The system MUST store predictions with: id, date, prediction_text, horizons[{label, timeframe, target_date}], confidence, reasons[], status (OPEN|CONFIRMED|FAILED|PARTIAL|CANCELLED), review_date, outcome, learning, related_memory_ids[].

#### Scenario: Creating a multi-horizon prediction
- GIVEN a conversation generates a forecast
- WHEN PREDICTION_CREATE intent fires
- THEN prediction includes short, medium, and long horizons
- AND status is OPEN

#### Scenario: Confirming a prediction
- GIVEN a prediction with status OPEN
- WHEN target_date passes and outcome is observed
- THEN status transitions to CONFIRMED or FAILED
- AND outcome and learning fields are populated

### Requirement: Prediction Horizon Tracking
Each prediction MUST include at least 3 horizons: short (days-weeks), medium (months), long (years, up to 2035). Each horizon MUST have label, timeframe, and target_date.

#### Scenario: Horizon validation
- GIVEN a prediction with horizons
- WHEN horizons are validated
- THEN short timeframe < medium timeframe < long timeframe
- AND target_dates are within valid range

#### Scenario: Long-horizon prediction
- GIVEN a prediction about 2035
- WHEN created
- THEN long horizon has target_date within 2035 range
- AND confidence is appropriately calibrated

### Requirement: Prediction Status Lifecycle
Status MUST transition: OPEN → CONFIRMED|FAILED|PARTIAL|CANCELLED. Review_date MUST be set on status change.

#### Scenario: Prediction refuted
- GIVEN a prediction with status OPEN
- WHEN evidence contradicts the prediction
- THEN status becomes FAILED
- AND review_date is set to current date

## ACCEPTANCE CRITERIA
- Predictions stored with 3 horizons
- Status transitions audited
- Target dates validated
- All golden master tests pass