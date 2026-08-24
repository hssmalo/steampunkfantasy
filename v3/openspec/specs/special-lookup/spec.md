# Special Lookup Spec

## Purpose

Defines the behavior of the `spf special show` command, which searches all races for units, models, and equipment that carry a given special key.

## Requirements

### Requirement: Special key is constrained to the registry
The `special show` command SHALL accept only identifiers the Special registry declares (ADR 0024). The registry's key set is the corpus, so the command cannot disagree with the rules data about what a Special is.

#### Scenario: Valid special key accepted
- **WHEN** the user runs `spf special show "immunity"`
- **THEN** the command executes without error

#### Scenario: Invalid special key rejected
- **WHEN** the user runs `spf special show "not_a_special"`
- **THEN** the command reports the key as unknown and suggests near matches from the registry

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
A rule declares where it is legal in its `slots` field, and the command SHALL search the locations belonging to each slot the rule declares:
- `unit`: `units.specials`, `models.unit_specials`, `equipment.unit_specials`
- `model`: `models.specials`, `equipment.model_specials`
- `assault`: `models.assault.specials`, `equipment.assault.specials`
- `range`: `equipment.range.specials`

A rule declaring several slots SHALL be searched in every location those slots cover.

#### Scenario: Unit-level special found
- **WHEN** a unit's `specials` table contains the queried id
- **THEN** a line beginning with `Unit:` and the unit name appears in the output

#### Scenario: Model assault special found
- **WHEN** a model's `assault.specials` table contains the queried id
- **THEN** a line beginning with `Model:` and the model name appears in the output

#### Scenario: Equipment special found
- **WHEN** an equipment item's `unit_specials` or `model_specials` table contains the queried id
- **THEN** a line beginning with `Equipment:` and the equipment name appears in the output

#### Scenario: Multi-slot special searched in every slot it declares
- **WHEN** the queried rule declares both the `unit` and `model` slots
- **THEN** the command searches the locations of both slots

#### Scenario: A holder yields one line per instance
- **WHEN** a holder carries the queried id several times, each instance with its own arguments
- **THEN** each instance produces its own line, because a slot holds N instances rather than one value
