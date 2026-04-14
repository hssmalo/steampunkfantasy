## ADDED Requirements

### Requirement: TeamModel represents a model instance within a team unit
A `TeamModel` SHALL be an immutable data structure holding the model's key, its `ModelConfig`, and the set of equipment upgrade keys the player added. Default equipment (from `ModelConfig.equipment`) SHALL NOT be stored in `upgrades`.

#### Scenario: TeamModel created with defaults
- **WHEN** a `TeamModel` is created for a model key
- **THEN** `upgrades` SHALL be an empty tuple

#### Scenario: TeamModel stores upgrade keys separately
- **WHEN** an equipment upgrade is added to a `TeamModel`
- **THEN** the key SHALL appear in `upgrades` and not in `config.equipment`

### Requirement: TeamUnit represents a unit instance within a team
A `TeamUnit` SHALL be an immutable data structure holding the unit's key, its `UnitConfig`, and a tuple of `TeamModel` instances. The models tuple MAY differ from the unit's default `models` list due to upgrades.

#### Scenario: TeamUnit created with default models
- **WHEN** a `TeamUnit` is created for a unit key
- **THEN** its models SHALL correspond to the unit's `UnitConfig.models` list in order

#### Scenario: TeamUnit allows upgrade model replacements
- **WHEN** a default model in a `TeamUnit` is replaced by an upgrade model
- **THEN** the replacement `TeamModel` SHALL appear at the same index as the replaced model

### Requirement: Team represents a player's assembled force for one army
A `Team` SHALL be an immutable data structure holding the army name and a tuple of `TeamUnit` instances. A `Team` SHALL belong to exactly one army (one `ArmyName`). Multiple `TeamUnit` instances with the same unit key SHALL be permitted (same unit type fielded multiple times).

#### Scenario: Empty team is valid
- **WHEN** a `Team` is created with no units
- **THEN** it SHALL have an empty units tuple and a valid army name

#### Scenario: Team permits duplicate unit types
- **WHEN** two `TeamUnit` instances with the same unit key are added
- **THEN** both SHALL appear in `Team.units`

### Requirement: Cost is represented as a multi-dimensional point total
A `Cost` SHALL have integer fields `mp`, `cp`, `xp`, and `ip` (all defaulting to 0). Cost addition SHALL sum each field independently. The existing `Cost` model from `spf.schemas.type_aliases` SHALL be reused.

#### Scenario: Adding zero costs is an identity operation
- **WHEN** a zero `Cost` is added to any `Cost`
- **THEN** the result SHALL equal the original `Cost`

#### Scenario: Costs sum field by field
- **WHEN** two `Cost` values are added
- **THEN** each field (`mp`, `cp`, `xp`, `ip`) in the result SHALL be the sum of the corresponding fields
