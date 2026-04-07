## 1. Data Structures

- [x] 1.1 Define `TeamModel` frozen dataclass with fields: `name: str`, `config: ModelConfig`, `upgrades: tuple[str, ...]`
- [x] 1.2 Define `TeamUnit` frozen dataclass with fields: `name: str`, `config: UnitConfig`, `models: tuple[TeamModel, ...]`
- [x] 1.3 Define `Team` frozen dataclass with fields: `army: ArmyName`, `units: tuple[TeamUnit, ...]`
- [x] 1.4 Add a `_make_default_team_model(model_name, army_config) -> TeamModel` helper that creates a `TeamModel` with empty `upgrades`
- [x] 1.5 Add a `_make_default_team_unit(unit_name, army_config) -> TeamUnit` helper that creates a `TeamUnit` from a unit's default models list

## 2. Cost Helpers

- [x] 2.1 Add a `_add_cost(a: Cost, b: Cost | None) -> Cost` helper that sums two `Cost` values field-by-field (treating `None` as zero)
- [x] 2.2 Implement `total_cost(team: Team, army_config: ArmyConfig) -> Cost` summing unit base costs, upgrade model costs, and upgrade equipment costs

## 3. Requires Validation Helper

- [x] 3.1 Implement `_remaining_slots(model: TeamModel, army_config: ArmyConfig) -> dict[EquipmentHolder, int]` computing available holder slots (limit minus usage by default + upgrade equipment)
- [x] 3.2 Implement `_satisfies_requirement(req: Requirement, model: TeamModel, remaining_slots: dict) -> bool` checking a single `Requirement` (type check or holder-slot check)
- [x] 3.3 Implement `_satisfies_requires(requires: list[list[Requirement]], model: TeamModel, army_config: ArmyConfig) -> bool` evaluating the full CNF: all outer groups must have at least one satisfied inner requirement

## 4. Builder Functions

- [x] 4.1 Implement `add_unit(team: Team, unit_name: str, army_config: ArmyConfig) -> Team` — validate unit exists, create `TeamUnit` with defaults, return new `Team`
- [x] 4.2 Add `_resolve_unit(team, unit_key: tuple[str, int]) -> TeamUnit` and `_resolve_model(unit, model_key: tuple[str, int]) -> TeamModel` helpers that look up by `(name, occurrence_index)` and raise `KeyError` if not found
- [x] 4.3 Implement `upgrade_unit(team: Team, unit_key: tuple[str, int], model_key: tuple[str, int], upgrade_model_name: str, army_config: ArmyConfig) -> Team` — use resolve helpers, validate `replaces`, return new `Team` with replaced model
- [x] 4.4 Implement `upgrade_model(team: Team, unit_key: tuple[str, int], model_key: tuple[str, int], equipment_name: str, army_config: ArmyConfig) -> Team` — use resolve helpers, validate cost non-None, validate requires, return new `Team` with equipment added to `upgrades`

## 5. Query Functions

- [x] 5.1 Implement `available_models(team: Team, unit_key: tuple[str, int], model_key: tuple[str, int], army_config: ArmyConfig) -> list[ModelConfig]` — use resolve helpers, return models whose `replaces` includes the target model's name
- [x] 5.2 Implement `available_equipment(team: Team, unit_key: tuple[str, int], model_key: tuple[str, int], army_config: ArmyConfig) -> list[EquipmentConfig]` — use resolve helpers, return equipment with non-None cost and satisfied requires

## 6. Validation

- [x] 6.1 Implement `validate_team(team: Team, army_config: ArmyConfig) -> list[str]` — collect all violations: illegal model replacements and unsatisfied equipment requires across all units and models

## 7. Tests

- [x] 7.1 Write tests for `TeamModel`, `TeamUnit`, `Team` construction (default state, immutability)
- [x] 7.2 Write tests for `_add_cost` and `total_cost` (empty team, unit cost, upgrade model cost, upgrade equipment cost)
- [x] 7.3 Write tests for `_satisfies_requires` (type requirement, holder requirement, CNF evaluation)
- [x] 7.4 Write tests for `add_unit` (valid, unknown unit name)
- [x] 7.5 Write tests for `upgrade_unit` (valid replacement, invalid replaces, unknown key)
- [x] 7.6 Write tests for `upgrade_model` (valid upgrade, no-cost equipment, unsatisfied requires, unknown key)
- [x] 7.7 Write tests for `available_models` and `available_equipment` (filtering logic)
- [x] 7.8 Write tests for `validate_team` (valid team, multiple violations reported)
