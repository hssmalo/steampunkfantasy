# Spec: Army Load Validation

## Purpose

<!-- TBD: describe the purpose of this capability -->

## Requirements

### Requirement: Validate unit names during army loading
The system SHALL check that every unit name in the army JSON exists in the race config before constructing `ArmyUnit` objects. If any unit name is not found, the system SHALL raise a `ValueError` that identifies the offending unit by its zero-based index in the `units` array and by its name value (even if empty). All invalid unit names SHALL be collected and reported together.

#### Scenario: Unknown unit name raises ValueError
- **WHEN** `load_army` is called and a unit entry has a name not present in the race config
- **THEN** a `ValueError` is raised with a message identifying the unit index and the invalid name

#### Scenario: Empty string unit name raises ValueError
- **WHEN** `load_army` is called and a unit entry has `"name": ""`
- **THEN** a `ValueError` is raised with a message such as `Unit #1 (name ''): unknown unit name`

#### Scenario: Multiple invalid units reported together
- **WHEN** `load_army` is called and several unit entries have unknown names
- **THEN** a single `ValueError` is raised listing all offending units

### Requirement: Validate model names during army loading
The system SHALL check that every model name within each unit entry exists in the race config before constructing `ArmyModel` objects. If any model name is not found, the system SHALL raise a `ValueError` that identifies the unit (by index and name) and the offending model (by its zero-based index within the unit and its name value). All invalid model names SHALL be collected and reported together with unit-name errors.

#### Scenario: Unknown model name raises ValueError
- **WHEN** `load_army` is called and a model entry within a unit has a name not present in the race config
- **THEN** a `ValueError` is raised with a message identifying the unit index, unit name, model index, and invalid model name

#### Scenario: Empty string model name raises ValueError
- **WHEN** `load_army` is called and a model entry has `"name": ""`
- **THEN** a `ValueError` is raised with a message such as `Unit #1 ('ork_boyz') / model #0 (name ''): unknown model name`

#### Scenario: Mix of unit and model errors reported together
- **WHEN** `load_army` is called and the JSON contains both unknown unit names and unknown model names
- **THEN** a single `ValueError` is raised listing all errors, unit errors before model errors

### Requirement: Validate equipment upgrades during army loading
The system SHALL check that every equipment upgrade on every model satisfies that equipment's requires constraints. If an upgrade's requires are not satisfied, the system SHALL raise a `ValueError` that identifies the unit name, model name, equipment name, AND the specific OR-groups that were not satisfied. Each failing group SHALL be described by the constraint alternatives it offered (e.g., `"type:Infantry or type:Grunt"`) and, for slot-count constraints, SHALL include the available slot count (e.g., `"Hands:2 (have 0)"`). All validation errors SHALL be collected and reported together.

#### Scenario: Equipment with unsatisfied type requirement reports the type group
- **WHEN** `load_army` is called and a model has an upgrade whose type OR-group is not satisfied
- **THEN** a `ValueError` is raised with a message such as `Unit 'ork_infantry', model 'ork_elite_infantry': equipment 'clockwork_power_spear' requires not satisfied: needs type:Infantry or type:Grunt`

#### Scenario: Equipment with unsatisfied slot requirement reports slot and available count
- **WHEN** `load_army` is called and a model has an upgrade whose slot OR-group is not satisfied
- **THEN** a `ValueError` is raised with a message that includes the slot name, required count, and available count, e.g. `needs Hands:2 (have 0)`

#### Scenario: Equipment with multiple failing groups reports all of them
- **WHEN** `load_army` is called and a model has an upgrade whose requires has two or more unsatisfied OR-groups
- **THEN** the error message lists all failing groups, separated by `"; "`

#### Scenario: Equipment with all requirements satisfied produces no error
- **WHEN** `load_army` is called and all equipment upgrades satisfy their requires
- **THEN** no error is raised for those upgrades

### Requirement: CLI show command handles load ValueError
The system SHALL catch `ValueError` raised by `load_army` in the `show_army` CLI command and print a user-friendly error message to stderr, then exit with status code 1, without printing a Python traceback.

#### Scenario: show_army prints error on invalid army
- **WHEN** `spf army show <name>` is called and the army JSON contains unknown unit or model names
- **THEN** the CLI prints a red error message to stderr and exits with code 1
