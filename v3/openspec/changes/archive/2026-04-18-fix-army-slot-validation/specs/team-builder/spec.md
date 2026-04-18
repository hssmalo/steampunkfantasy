## MODIFIED Requirements

### Requirement: available_equipment returns equipment upgrades valid for a model
`available_equipment(army_list, unit_key, model_key, race_config) -> list[EquipmentConfig]` SHALL return all race equipment that has a non-`None` cost AND has its `requires` constraints satisfied by the model. Slot capacity SHALL be computed using only the model's current upgrade equipment; default equipment SHALL NOT consume slots, because Rule A discards defaults whenever any upgrade is added.

#### Scenario: Returns only equipment with cost
- **WHEN** `available_equipment` is called
- **THEN** equipment with `cost = None` SHALL NOT be included in the result

#### Scenario: Requires CNF is correctly evaluated
- **WHEN** equipment has `requires = [[A], [B, C]]`
- **THEN** the equipment SHALL be included only if A is satisfied AND at least one of B or C is satisfied

#### Scenario: Type requirement is checked against model types
- **WHEN** equipment requires `type:Infantry`
- **THEN** it SHALL only be returned for models whose `type` list includes `"Infantry"`

#### Scenario: Holder requirement checks remaining upgrade-only slot capacity
- **WHEN** equipment requires `Hands:1` and the model's upgrade equipment already consumes all Hands slots
- **THEN** that equipment SHALL NOT be included in the result

#### Scenario: Default equipment does not consume slots for availability checks
- **WHEN** a model has default equipment that consumes Hands slots and no current upgrades
- **THEN** `available_equipment` SHALL treat all Hands slots as available (defaults are discarded by Rule A when any upgrade is added)

### Requirement: validate_army returns a list of all rule violations
`validate_army(army_list, race_config) -> list[str]` SHALL return a list of human-readable error strings describing every rule violation. An empty list means the army list is valid. Each upgrade SHALL be validated against the slot capacity remaining after all *previously validated* upgrades on the same model are accounted for; the upgrade being validated SHALL NOT be counted against its own slot check. Slot capacity SHALL be computed using only upgrade equipment (Rule A: defaults are discarded).

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
- **WHEN** an `ArmyModel` has an upgrade equipment whose `requires` are not satisfied given the remaining slots after prior upgrades
- **THEN** a validation error describing the unsatisfied requirement SHALL be included

#### Scenario: Default equipment does not consume slots during validation
- **WHEN** a model has default equipment and upgrade equipment, and the upgrades fit within the model's slot limits without the defaults
- **THEN** `validate_army` SHALL report no slot errors for those upgrades

#### Scenario: Upgrade is not counted against its own slot check
- **WHEN** a model has a single upgrade that exactly fits the model's remaining slots
- **THEN** `validate_army` SHALL report no slot error for that upgrade
