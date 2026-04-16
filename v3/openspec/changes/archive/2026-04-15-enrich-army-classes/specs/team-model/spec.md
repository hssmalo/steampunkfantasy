## MODIFIED Requirements

### Requirement: ArmyModel represents a model instance within an army unit during building
An `ArmyModel` SHALL be an immutable data structure (in `spf.armies.build`) holding the model's name, its `ModelConfig`, and the set of equipment upgrade keys the player added. Default equipment (from `ModelConfig.equipment`) SHALL NOT be stored in `upgrades`. `ArmyModel` carries `config: ModelConfig` to support build-time validation of slot requirements.

#### Scenario: ArmyModel created with defaults
- **WHEN** an `ArmyModel` is created for a model key
- **THEN** `upgrades` SHALL be an empty tuple

#### Scenario: ArmyModel stores upgrade keys separately
- **WHEN** an equipment upgrade is added to an `ArmyModel`
- **THEN** the key SHALL appear in `upgrades` and not in `config.equipment`

### Requirement: ArmyUnit represents a unit instance within an army list during building
An `ArmyUnit` SHALL be an immutable data structure (in `spf.armies.build`) holding the unit's name, its `UnitConfig`, and a tuple of `ArmyModel` instances. The models tuple MAY differ from the unit's default `models` list due to model upgrades.

#### Scenario: ArmyUnit created with default models
- **WHEN** an `ArmyUnit` is created for a unit name
- **THEN** its models SHALL correspond to the unit's `UnitConfig.models` list in order

#### Scenario: ArmyUnit allows upgrade model replacements
- **WHEN** a default model in an `ArmyUnit` is replaced by an upgrade model
- **THEN** the replacement `ArmyModel` SHALL appear at the same index as the replaced model

### Requirement: ArmyList represents a player's army during building
An `ArmyList` SHALL be an immutable data structure (in `spf.armies.build`) holding the race name, a nick, and a tuple of `ArmyUnit` instances. Multiple `ArmyUnit` instances with the same unit name SHALL be permitted.

#### Scenario: Empty army list is valid
- **WHEN** an `ArmyList` is created with no units
- **THEN** it SHALL have an empty units tuple

#### Scenario: ArmyList permits duplicate unit types
- **WHEN** two `ArmyUnit` instances with the same unit name are added
- **THEN** both SHALL appear in `ArmyList.units`

### Requirement: Cost is represented as a multi-dimensional point total
A `Cost` SHALL have integer fields `mp`, `cp`, `xp`, and `ip` (all defaulting to 0). Cost addition SHALL sum each field independently. The existing `Cost` model from `spf.schemas.type_aliases` SHALL be reused.

#### Scenario: Adding zero costs is an identity operation
- **WHEN** a zero `Cost` is added to any `Cost`
- **THEN** the result SHALL equal the original `Cost`

#### Scenario: Costs sum field by field
- **WHEN** two `Cost` values are added
- **THEN** each field (`mp`, `cp`, `xp`, `ip`) in the result SHALL be the sum of the corresponding fields
