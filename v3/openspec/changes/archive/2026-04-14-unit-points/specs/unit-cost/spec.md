## ADDED Requirements

### Requirement: Compute total cost for a single unit
The system SHALL provide a `unit_cost(unit, race_config)` function in `src/spf/armies/data.py` that returns the total `Cost` for one `ArmyUnit`: the unit's base cost plus any upgrade model costs plus any upgrade equipment costs.

#### Scenario: Unit with only base cost
- **WHEN** `unit_cost(unit, race_config)` is called for a unit with no model or equipment upgrades
- **THEN** it returns the unit's base `config.cost`

#### Scenario: Unit with upgrade model
- **WHEN** a unit contains a model whose name differs from the default model name at that slot
- **THEN** `unit_cost` adds that model's `config.cost` to the base unit cost

#### Scenario: Unit with equipment upgrade
- **WHEN** a model in the unit has one or more entries in its `upgrades` tuple
- **THEN** `unit_cost` adds each equipment's `cost` (from `race_config.equipment`) to the running total

#### Scenario: total_cost delegates to unit_cost
- **WHEN** `total_cost(army, race_config)` is called
- **THEN** it returns the sum of `unit_cost(unit, race_config)` for every unit in the army

### Requirement: Compute points value for a unit
The system SHALL provide a `unit_points(unit, race_config)` function in `src/spf/armies/data.py` that returns an `int` equal to `mp + cp + xp + 3 * ip` of the unit's total cost.

#### Scenario: Points formula applied
- **WHEN** `unit_points(unit, race_config)` is called
- **THEN** it returns `unit_cost(unit, race_config).mp + unit_cost(unit, race_config).cp + unit_cost(unit, race_config).xp + 3 * unit_cost(unit, race_config).ip`

#### Scenario: Zero-cost unit yields zero points
- **WHEN** a unit has no cost components (all are zero)
- **THEN** `unit_points` returns `0`
