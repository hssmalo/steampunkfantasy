# Special Lookup Spec

## Purpose

Defines the behaviour of the `spf special show` command, which searches all races for units, models, and equipment that carry a given special key.

## Requirements

### Requirement: Special key is constrained to known values
The `special show` command SHALL accept only valid special keys — members of `UnitSpecial`, `ModelSpecial`, or `AssaultSpecial`. The CLI SHALL enumerate all valid choices so the user can discover them without reading source code.

#### Scenario: Valid special key accepted
- **WHEN** the user runs `spf special show "Immunity"`
- **THEN** the command executes without error

#### Scenario: Invalid special key rejected
- **WHEN** the user runs `spf special show "NotASpecial"`
- **THEN** cyclopts rejects the input before execution and lists valid choices

### Requirement: Races loaded from filesystem
The command SHALL derive the race list from `races.list_races()`. Races whose TOML files fail validation SHALL be silently skipped.

#### Scenario: Valid races included
- **WHEN** a race TOML is valid and the special key appears in it
- **THEN** that race appears in the output

#### Scenario: Invalid races skipped
- **WHEN** a race TOML fails `pydantic.ValidationError`
- **THEN** the race is omitted from output and no error is shown

### Requirement: Output grouped by race, race omitted when no matches
For each race that has at least one match, the command SHALL print the race display name as a header, followed by one line per match. Races with no matches SHALL NOT appear in the output.

#### Scenario: Race with matches shown
- **WHEN** a race contains a unit, model, or equipment with the queried special key
- **THEN** the race display name is printed as a header and each match appears on its own line below it

#### Scenario: Race with no matches omitted
- **WHEN** a race has no unit, model, or equipment matching the special key
- **THEN** the race produces no output at all

### Requirement: All match locations searched
The command SHALL search all locations where each special type can appear:
- `UnitSpecial`: `units.special`, `models.unit_special`, `equipment.unit_special`
- `ModelSpecial`: `models.special`, `equipment.model_special`
- `AssaultSpecial`: `models.assault.special`, `equipment.assault.special`

A special key that belongs to multiple categories (e.g. "Fog" in both `UnitSpecial` and `ModelSpecial`) SHALL be searched in all applicable locations.

#### Scenario: Unit-level special found
- **WHEN** a unit's `special` dict contains the queried key
- **THEN** a line beginning with `Unit:` and the unit name appears in the output

#### Scenario: Model assault special found
- **WHEN** a model's `assault.special` dict contains the queried key
- **THEN** a line beginning with `Model:` and the model name appears in the output

#### Scenario: Equipment special found
- **WHEN** an equipment item's `unit_special` or `model_special` dict contains the queried key
- **THEN** a line beginning with `Equipment:` and the equipment name appears in the output

#### Scenario: Dual-category special searched in both categories
- **WHEN** the queried key belongs to both `UnitSpecial` and `ModelSpecial`
- **THEN** the command searches both `units.special` / `models.unit_special` / `equipment.unit_special` AND `models.special` / `equipment.model_special`
