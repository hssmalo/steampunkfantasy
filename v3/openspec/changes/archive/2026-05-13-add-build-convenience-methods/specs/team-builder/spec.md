# Delta Spec: Team Builder Convenience Methods

## ADDED Requirements

### Requirement: upgrade_full_unit replaces all models in a unit with an upgrade model

`ArmyList.upgrade_full_unit(unit_key, upgrade_model_name, race_config) -> ArmyList` SHALL return a new `ArmyList` where all models within the identified unit are replaced by the same `upgrade_model_name`. This is a convenience wrapper that calls `upgrade_unit()` sequentially for each model slot in the unit. The `upgrade_model_name`'s `ModelConfig.replaces` field SHALL match the name of each model being replaced, or a `ValueError` SHALL be raised.

#### Scenario: All models are successfully upgraded to the same upgrade model
- **WHEN** `upgrade_full_unit` is called with a unit containing four identical models and a valid upgrade model
- **THEN** all four model slots shall be replaced by the upgrade model
- **THEN** the result shall be identical to calling `upgrade_unit` four times in sequence

#### Scenario: Upgrade fails if any model cannot be replaced
- **WHEN** `upgrade_full_unit` is called with an upgrade model whose `replaces` field does not match the models in the unit
- **THEN** a `ValueError` SHALL be raised
- **THEN** the army list shall remain unchanged (fail-fast)

#### Scenario: Unknown unit key raises KeyError
- **WHEN** `upgrade_full_unit` is called with a `unit_key` that does not exist
- **THEN** a `KeyError` SHALL be raised

### Requirement: upgrade_all_models adds equipment upgrade to all models in a unit

`ArmyList.upgrade_all_models(unit_key, equipment_name, race_config) -> ArmyList` SHALL return a new `ArmyList` where the same `equipment_name` is appended to the `upgrades` of all models in the identified unit. The method SHALL apply the equipment to each model sequentially by calling `upgrade_model()` for each model slot. Equipment validation follows the same rules as `ArmyList.upgrade_model()`: equipment SHALL have a non-`None` cost and its `requires` SHALL be satisfied by each model at the time of upgrade.

#### Scenario: Equipment is added to all models
- **WHEN** `upgrade_all_models` is called with valid equipment
- **THEN** the equipment key SHALL be appended to all models' `upgrades`
- **THEN** the result is identical to calling `upgrade_model()` sequentially for each model slot

#### Scenario: Equipment without cost raises ValueError
- **WHEN** `upgrade_all_models` is called with equipment that has `cost = None`
- **THEN** a `ValueError` SHALL be raised

#### Scenario: Raises ValueError if a model cannot take the equipment
- **WHEN** `upgrade_all_models` is called with equipment whose `requires` are not satisfied by a model
- **THEN** a `ValueError` SHALL be raised on the first model that cannot accept the equipment
- **THEN** because the data structure is immutable, no changes are visible to the caller

#### Scenario: Unknown unit key raises KeyError
- **WHEN** `upgrade_all_models` is called with a `unit_key` that does not exist
- **THEN** a `KeyError` SHALL be raised

### Requirement: duplicate_unit adds a copy of an existing unit to the army list

`ArmyList.duplicate_unit(unit_key) -> ArmyList` SHALL return a new `ArmyList` with a copy of the identified unit appended. The duplicate shall be an independent `ArmyUnit` instance with the same name, config, and models as the original.

#### Scenario: Duplicating a unit appends an independent copy
- **WHEN** `duplicate_unit` is called on a unit
- **THEN** the returned army list shall have one more unit
- **THEN** the new unit shall have the same name, config, and model structure as the original
- **THEN** the original and copy shall be independent instances

#### Scenario: Modifying the duplicate does not affect the original
- **WHEN** a unit is duplicated and then the duplicate is upgraded
- **THEN** the original unit shall remain unchanged

#### Scenario: Unknown unit key raises KeyError
- **WHEN** `duplicate_unit` is called with a `unit_key` that does not exist
- **THEN** a `KeyError` SHALL be raised

### Requirement: delete_unit removes a unit from the army list

`ArmyList.delete_unit(unit_key) -> ArmyList` SHALL return a new `ArmyList` with the identified unit removed.

#### Scenario: Deleting a unit removes it from the list
- **WHEN** `delete_unit` is called on an army list containing three units
- **THEN** the returned army list shall have one fewer unit
- **THEN** the identified unit shall no longer be in the list

#### Scenario: Unknown unit key raises KeyError
- **WHEN** `delete_unit` is called with a `unit_key` that does not exist
- **THEN** a `KeyError` SHALL be raised
