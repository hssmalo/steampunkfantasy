## MODIFIED Requirements

### Requirement: Compute total cost for a single unit via Unit.cost()
The resolved `Unit` class SHALL provide a `cost() -> Cost` method that returns the total cost for the unit: the unit's base cost plus upgrade model costs plus upgrade equipment costs. For each model's `upgrade_equipment`: if `upgrade_all is False`, the equipment cost is multiplied by `len(unit.models)`; otherwise the equipment cost is added flat. Units or models with `cost = None` SHALL contribute zero cost.

#### Scenario: Unit with only base cost
- **WHEN** `unit.cost()` is called for a unit with no model or equipment upgrades
- **THEN** it returns the unit's base `config.cost` (or `Cost()` if None)

#### Scenario: Unit with upgrade model
- **WHEN** a unit contains a model whose name differs from the default model at that slot
- **THEN** `unit.cost()` adds that model's `config.cost` to the base unit cost

#### Scenario: Unit with equipment upgrade where upgrade_all is True
- **WHEN** a model in the unit has upgrade equipment with `upgrade_all=True`
- **THEN** `unit.cost()` adds that equipment's cost exactly once, regardless of unit size

#### Scenario: Unit with equipment upgrade where upgrade_all is False
- **WHEN** a model in the unit has upgrade equipment with `upgrade_all=False` and the unit has N models
- **THEN** `unit.cost()` adds that equipment's cost multiplied by N

#### Scenario: Army cost equals sum of unit costs
- **WHEN** `army.cost()` is called
- **THEN** it returns the sum of `unit.cost()` for every unit in the army

## REMOVED Requirements

### Requirement: Compute total cost for a single unit (free function)
**Reason**: Replaced by `Unit.cost()` method on the resolved `Unit` type. The free functions `unit_cost(unit, race_config)` and `total_cost(army, race_config)` are removed.
**Migration**: Use `unit.cost()` on a resolved `Unit`; use `army.cost()` on a resolved `Army`.

### Requirement: Compute points value for a unit
**Reason**: `unit_points()` free function removed alongside `unit_cost()`. Points calculation is still available via `unit.cost().to_points()`.
**Migration**: Call `unit.cost().to_points()` directly.
