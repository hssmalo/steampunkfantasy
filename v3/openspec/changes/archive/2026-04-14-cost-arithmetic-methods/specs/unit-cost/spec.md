## MODIFIED Requirements

### Requirement: Compute points value for a unit
The system SHALL provide a `unit_points(unit, race_config)` function in `src/spf/armies/data.py` that returns an `int` equal to `unit_cost(unit, race_config).to_points()`.

#### Scenario: Points formula applied
- **WHEN** `unit_points(unit, race_config)` is called
- **THEN** it returns `unit_cost(unit, race_config).to_points()`

#### Scenario: Zero-cost unit yields zero points
- **WHEN** a unit has no cost components (all are zero)
- **THEN** `unit_points` returns `0`
