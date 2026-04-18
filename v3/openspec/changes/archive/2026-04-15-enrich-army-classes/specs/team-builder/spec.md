## MODIFIED Requirements

### Requirement: add_unit adds a unit with default models and equipment to an army list
`ArmyList.add_unit(unit_name, race_config) -> ArmyList` SHALL return a new `ArmyList` with a new `ArmyUnit` appended. The new unit's models SHALL be the unit's default `UnitConfig.models` list, each as an `ArmyModel` with empty `upgrades`. The unit name SHALL exist in the race config.

#### Scenario: Adding a valid unit appends it to the army list
- **WHEN** `army_list.add_unit(unit_name, race_config)` is called with a valid unit name
- **THEN** the returned army list SHALL have one more unit than the input
- **THEN** the new unit's models SHALL match the unit's default models list

#### Scenario: Adding the same unit twice results in two separate ArmyUnit instances
- **WHEN** `add_unit` is called twice with the same unit name
- **THEN** the returned army list SHALL contain two independent `ArmyUnit` instances for that unit

#### Scenario: Adding an unknown unit name raises ValueError
- **WHEN** `add_unit` is called with a unit name not in the race config
- **THEN** a `ValueError` SHALL be raised

### Requirement: upgrade_unit replaces a default model with an upgrade model in a unit
`ArmyList.upgrade_unit(unit_key, model_key, upgrade_model_name, race_config) -> ArmyList` SHALL return a new `ArmyList` where the model identified by `model_key` within the unit identified by `unit_key` is replaced by a new `ArmyModel` for `upgrade_model_name`. This is also available as `ArmyUnit.upgrade_unit(model_key, upgrade_model_name, race_config) -> ArmyUnit`. The replacement model's `ModelConfig.replaces` SHALL equal the name of the model being replaced.

#### Scenario: Valid model replacement succeeds
- **WHEN** `upgrade_unit` is called with a model whose `replaces` matches the target model's name
- **THEN** the returned army list SHALL have the replacement model at the position identified by `model_key`

#### Scenario: Invalid replacement raises ValueError
- **WHEN** `upgrade_unit` is called with a model whose `replaces` does NOT match the target model's name
- **THEN** a `ValueError` SHALL be raised

#### Scenario: Unknown unit or model key raises KeyError
- **WHEN** `upgrade_unit` is called with a `unit_key` or `model_key` that does not exist
- **THEN** a `KeyError` SHALL be raised

### Requirement: upgrade_model adds an equipment upgrade to a model
`ArmyList.upgrade_model(unit_key, model_key, equipment_name, race_config) -> ArmyList` SHALL return a new `ArmyList` where `equipment_name` is appended to the `upgrades` of the identified `ArmyModel`. This is also available as `ArmyUnit.upgrade_model(model_key, equipment_name, race_config) -> ArmyUnit` and `ArmyModel.upgrade(equipment_name, race_config) -> ArmyModel`. The equipment SHALL have a non-`None` cost and its `requires` SHALL be satisfied by the model.

#### Scenario: Valid equipment upgrade is added
- **WHEN** `upgrade_model` is called with equipment that has a cost and whose requires are satisfied
- **THEN** the equipment key SHALL appear in the model's `upgrades` in the returned army list

#### Scenario: Equipment without cost raises ValueError
- **WHEN** `upgrade_model` is called with equipment that has `cost = None`
- **THEN** a `ValueError` SHALL be raised

#### Scenario: Equipment with unsatisfied requires raises ValueError
- **WHEN** `upgrade_model` is called with equipment whose `requires` are not satisfied by the model
- **THEN** a `ValueError` SHALL be raised

### Requirement: available_models returns models that can replace a given model
`available_models(army_list, unit_key, model_key, race_config) -> list[ModelConfig]` SHALL return all models from the race whose `replaces` field equals the name of the identified model.

#### Scenario: Returns only models with matching replaces
- **WHEN** `available_models` is called for a model
- **THEN** only models whose `replaces` equals that model's name SHALL be returned

#### Scenario: Returns empty list when no replacements exist
- **WHEN** no race model has a `replaces` field matching the target model
- **THEN** an empty list SHALL be returned

### Requirement: available_equipment returns equipment upgrades valid for a model
`available_equipment(army_list, unit_key, model_key, race_config) -> list[EquipmentConfig]` SHALL return all race equipment that has a non-`None` cost AND has its `requires` constraints satisfied by the model.

#### Scenario: Returns only equipment with cost
- **WHEN** `available_equipment` is called
- **THEN** equipment with `cost = None` SHALL NOT be included

#### Scenario: Requires CNF is correctly evaluated
- **WHEN** equipment has `requires = [[A], [B, C]]`
- **THEN** the equipment SHALL be included only if A is satisfied AND at least one of B or C is satisfied

#### Scenario: Type requirement is checked against model types
- **WHEN** equipment requires `type:Infantry`
- **THEN** it SHALL only be returned for models whose `type` list includes `"Infantry"`

#### Scenario: Holder requirement checks remaining slot capacity
- **WHEN** equipment requires `Hands:1` and the model has no remaining Hands slots
- **THEN** that equipment SHALL NOT be included

### Requirement: validate_army returns a list of all rule violations
`validate_army(army_list, race_config) -> list[str]` SHALL return a list of human-readable error strings describing every rule violation. An empty list means the army list is valid.

#### Scenario: Valid army list returns empty list
- **WHEN** `validate_army` is called on an army list with no violations
- **THEN** the result SHALL be an empty list

#### Scenario: All violations are reported, not just the first
- **WHEN** an army list has multiple violations
- **THEN** `validate_army` SHALL return one error string per violation

#### Scenario: Invalid model replacement is reported
- **WHEN** an `ArmyModel` has a model that does not match the `replaces` field
- **THEN** a validation error describing the illegal replacement SHALL be included

#### Scenario: Unsatisfied equipment requires is reported
- **WHEN** an `ArmyModel` has an upgrade equipment whose `requires` are not satisfied
- **THEN** a validation error describing the unsatisfied requirement SHALL be included

## REMOVED Requirements

### Requirement: total_cost returns the sum of all costs in a team
**Reason**: Replaced by `Army.cost()` on the resolved `Army` type. The free function `total_cost(army, race_config)` is removed.
**Migration**: Call `army_list.resolve(race_config).cost()` or use `Army.cost()` on a loaded army.
