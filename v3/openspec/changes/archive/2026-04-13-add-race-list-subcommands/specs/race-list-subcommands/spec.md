## ADDED Requirements

### Requirement: Cost has a human-readable string representation
`Cost` SHALL implement `__str__` returning the string `f"{mp:2d}mp {cp:2d}cp {xp:2d}xp {ip:2d}ip"` where each currency value is right-aligned in a 2-character field.

#### Scenario: Cost with non-zero values
- **WHEN** `str(Cost(mp=5, cp=12, xp=0, ip=3))` is evaluated
- **THEN** the result is `" 5mp 12cp  0xp  3ip"`

#### Scenario: Cost with all-zero values
- **WHEN** `str(Cost())` is evaluated
- **THEN** the result is `" 0mp  0cp  0xp  0ip"`

---

### Requirement: `spf race units` lists units for a race
The CLI SHALL provide a `units` subcommand under `spf race` that prints one line per unit showing the unit name and its cost. Each line SHALL use the format `f"- {name:<24} {cost_str}"`. If a unit has `cost = None` the cost column SHALL display `"  -mp   -cp   -xp   -ip"`.

#### Scenario: Race with units that have costs
- **WHEN** `spf race units goblin` is run for a race whose units have defined costs
- **THEN** each unit appears on its own line with name left-padded to 24 characters and cost formatted via `Cost.__str__()`

#### Scenario: Unit with no cost defined
- **WHEN** a unit in the race has `cost = None`
- **THEN** the cost column shows the dash placeholder instead of a numeric cost

---

### Requirement: `spf race models` lists models for a race
The CLI SHALL provide a `models` subcommand under `spf race` that prints one line per model showing the model name and its cost, using the same format as `units`.

#### Scenario: Race with models
- **WHEN** `spf race models goblin` is run
- **THEN** each model appears on its own line with name and cost

---

### Requirement: `spf race equipment` lists equipment for a race
The CLI SHALL provide an `equipment` subcommand under `spf race` that prints one line per equipment item showing the equipment name and its cost, using the same format as `units`.

#### Scenario: Race with equipment
- **WHEN** `spf race equipment goblin` is run
- **THEN** each equipment item appears on its own line with name and cost

---

### Requirement: `spf race things` combines units, models, and equipment
The CLI SHALL provide a `things` subcommand under `spf race` that outputs units, then models, then equipment for the given race, each section preceded by a bold section header (`Units`, `Models`, `Equipment`).

#### Scenario: Combined output order
- **WHEN** `spf race things goblin` is run
- **THEN** the output shows a `Units` header followed by all units, then a `Models` header followed by all models, then an `Equipment` header followed by all equipment
