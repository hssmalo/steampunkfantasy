## MODIFIED Requirements

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
