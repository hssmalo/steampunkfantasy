# Spec: Team Builder

## Purpose

Defines the functional API for assembling and querying a player's team. All operations return new immutable `Team` instances (functional core). The builder provides functions to add units, upgrade models, add equipment, query available options, compute costs, and validate the team.

## Requirements

### Requirement: add_unit adds a unit with default models and equipment to a team
`add_unit(team, unit_name, army_config) -> Team` SHALL return a new `Team` with a new `TeamUnit` appended. The new unit's models SHALL be the unit's default `UnitConfig.models` list, each as a `TeamModel` with empty `upgrades`. The unit name SHALL exist in the army config.

#### Scenario: Adding a valid unit appends it to the team
- **WHEN** `add_unit` is called with a valid unit name
- **THEN** the returned team SHALL have one more unit than the input team
- **THEN** the new unit's models SHALL match the unit's default models list

#### Scenario: Adding the same unit twice results in two separate TeamUnit instances
- **WHEN** `add_unit` is called twice with the same unit name
- **THEN** the returned team SHALL contain two independent `TeamUnit` instances for that unit

#### Scenario: Adding an unknown unit name raises ValueError
- **WHEN** `add_unit` is called with a unit name not in the army config
- **THEN** a `ValueError` SHALL be raised

### Requirement: upgrade_unit replaces a default model with an upgrade model in a unit
`upgrade_unit(team, unit_key, model_key, upgrade_model_name, army_config) -> Team` SHALL return a new `Team` where the model identified by `model_key: tuple[str, int]` within the unit identified by `unit_key: tuple[str, int]` is replaced by a new `TeamModel` for `upgrade_model_name`. The replacement model's `ModelConfig.replaces` list SHALL include the name of the model being replaced. `unit_key` is `(unit_name, occurrence_index)` where `occurrence_index` counts among units with that name; likewise `model_key` is `(model_name, occurrence_index)` within the resolved unit.

#### Scenario: Valid model replacement succeeds
- **WHEN** `upgrade_unit` is called with a model whose `replaces` includes the target model's name
- **THEN** the returned team SHALL have the replacement model at the position identified by `model_key`

#### Scenario: Invalid replacement raises ValueError
- **WHEN** `upgrade_unit` is called with a model whose `replaces` does NOT include the target model's name
- **THEN** a `ValueError` SHALL be raised

#### Scenario: Unknown unit or model key raises KeyError
- **WHEN** `upgrade_unit` is called with a `unit_key` or `model_key` that does not exist in the team
- **THEN** a `KeyError` SHALL be raised

### Requirement: upgrade_model adds an equipment upgrade to a model
`upgrade_model(team, unit_key, model_key, equipment_name, army_config) -> Team` SHALL return a new `Team` where `equipment_name` is appended to the `upgrades` of the `TeamModel` identified by `unit_key: tuple[str, int]` and `model_key: tuple[str, int]`. The equipment SHALL have a non-`None` cost. The equipment's `requires` constraints SHALL be satisfied by the model (see `available_equipment`).

#### Scenario: Valid equipment upgrade is added
- **WHEN** `upgrade_model` is called with equipment that has a cost and whose requires are satisfied
- **THEN** the equipment key SHALL appear in the model's `upgrades` in the returned team

#### Scenario: Equipment without cost raises ValueError
- **WHEN** `upgrade_model` is called with equipment that has `cost = None`
- **THEN** a `ValueError` SHALL be raised

#### Scenario: Equipment with unsatisfied requires raises ValueError
- **WHEN** `upgrade_model` is called with equipment whose `requires` are not satisfied by the model
- **THEN** a `ValueError` SHALL be raised

### Requirement: available_models returns models that can replace a given model in a unit
`available_models(team, unit_key, model_key, army_config) -> list[ModelConfig]` SHALL return all models from the army whose `replaces` list includes the name of the model identified by `unit_key: tuple[str, int]` and `model_key: tuple[str, int]`.

#### Scenario: Returns only models with matching replaces
- **WHEN** `available_models` is called for a model
- **THEN** only models whose `replaces` list contains that model's name SHALL be returned

#### Scenario: Returns empty list when no replacements exist
- **WHEN** no army model has a `replaces` field matching the target model
- **THEN** an empty list SHALL be returned

### Requirement: available_equipment returns equipment upgrades valid for a model
`available_equipment(team, unit_key, model_key, army_config) -> list[EquipmentConfig]` SHALL return all army equipment that: (1) has a non-`None` cost, AND (2) has its `requires` constraints satisfied by the model. Satisfaction is determined by the model's `type` list (for `type` requirements) and remaining equipment holder slots (for holder requirements). Remaining slots = `EquipmentLimit.limit` minus the count of current equipment (defaults + upgrades) using that holder.

#### Scenario: Returns only equipment with cost
- **WHEN** `available_equipment` is called
- **THEN** equipment with `cost = None` SHALL NOT be included in the result

#### Scenario: Requires CNF is correctly evaluated
- **WHEN** equipment has `requires = [[A], [B, C]]`
- **THEN** the equipment SHALL be included only if A is satisfied AND at least one of B or C is satisfied

#### Scenario: Type requirement is checked against model types
- **WHEN** equipment requires `type:Infantry`
- **THEN** it SHALL only be returned for models whose `type` list includes `"Infantry"`

#### Scenario: Holder requirement checks remaining slot capacity
- **WHEN** equipment requires `Hands:1` and the model has no remaining Hands slots
- **THEN** that equipment SHALL NOT be included in the result

### Requirement: total_cost returns the sum of all costs in a team
`total_cost(team, army_config) -> Cost` SHALL return the sum of: base unit costs (from `UnitConfig.cost`), upgrade model costs (from `ModelConfig.cost` for models in `TeamModel` that replaced a default), and upgrade equipment costs (from `EquipmentConfig.cost` for each entry in `TeamModel.upgrades`). Units or models with `cost = None` SHALL contribute zero cost.

#### Scenario: Empty team has zero cost
- **WHEN** `total_cost` is called on a team with no units
- **THEN** the result SHALL be `Cost(mp=0, cp=0, xp=0, ip=0)`

#### Scenario: Base unit cost is included
- **WHEN** a unit with a non-None cost is added
- **THEN** its cost SHALL be reflected in `total_cost`

#### Scenario: Upgrade model cost is included
- **WHEN** a model upgrade is applied
- **THEN** the replacement model's cost SHALL be added to `total_cost`

#### Scenario: Upgrade equipment cost is included
- **WHEN** an equipment upgrade is added to a model
- **THEN** the equipment's cost SHALL be added to `total_cost`

### Requirement: validate_team returns a list of all rule violations
`validate_team(team, army_config) -> list[str]` SHALL return a list of human-readable error strings describing every rule violation found in the team. An empty list means the team is valid. Violations checked SHALL include: model replacement validity (`replaces`), equipment requires satisfaction, and equipment-with-no-cost being used as upgrade.

#### Scenario: Valid team returns empty list
- **WHEN** `validate_team` is called on a team with no rule violations
- **THEN** the result SHALL be an empty list

#### Scenario: All violations are reported, not just the first
- **WHEN** a team has multiple violations
- **THEN** `validate_team` SHALL return one error string per violation

#### Scenario: Invalid model replacement is reported
- **WHEN** a `TeamModel` in a unit has a model that does not have the replaced model in its `replaces` list
- **THEN** a validation error describing the illegal replacement SHALL be included

#### Scenario: Unsatisfied equipment requires is reported
- **WHEN** a `TeamModel` has an upgrade equipment whose `requires` are not satisfied
- **THEN** a validation error describing the unsatisfied requirement SHALL be included
