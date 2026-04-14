## MODIFIED Requirements

### Requirement: Compute total cost for a single unit
The system SHALL provide a `unit_cost(unit, race_config)` function in `src/spf/armies/data.py` that returns the total `Cost` for one `ArmyUnit`: the unit's base cost plus any upgrade model costs plus any upgrade equipment costs. Equipment cost is applied once per unit when `upgrade_all` is `True`, or multiplied by the number of models in the unit when `upgrade_all` is `False` or `None`.

#### Scenario: Unit with only base cost
- **WHEN** `unit_cost(unit, race_config)` is called for a unit with no model or equipment upgrades
- **THEN** it returns the unit's base `config.cost`

#### Scenario: Unit with upgrade model
- **WHEN** a unit contains a model whose name differs from the default model name at that slot
- **THEN** `unit_cost` adds that model's `config.cost` to the base unit cost

#### Scenario: Unit with equipment upgrade where upgrade_all is True
- **WHEN** a model in the unit has an equipment upgrade whose `upgrade_all` is `True`
- **THEN** `unit_cost` adds that equipment's `cost` exactly once to the running total, regardless of how many models are in the unit

#### Scenario: Unit with equipment upgrade where upgrade_all is False or None
- **WHEN** a model in the unit has an equipment upgrade whose `upgrade_all` is `False` or `None`
- **THEN** `unit_cost` adds that equipment's `cost` multiplied by the total number of models in the unit

#### Scenario: total_cost delegates to unit_cost
- **WHEN** `total_cost(army, race_config)` is called
- **THEN** it returns the sum of `unit_cost(unit, race_config)` for every unit in the army
