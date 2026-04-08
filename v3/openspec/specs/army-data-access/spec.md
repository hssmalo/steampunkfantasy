# Spec: army-data-access

## Purpose

TBD - Provides data access functions for retrieving army configuration data (races, units, models, equipment) from TOML data files.

## Requirements

### Requirement: List available army names
The system SHALL provide a function to list all valid army names (i.e., the available TOML data files in the data directory).

#### Scenario: List army names returns all configured armies
- **WHEN** `list_armies()` is called
- **THEN** it returns a collection of `ArmyName` strings corresponding to each TOML file in the data directory

### Requirement: Get race metadata for an army
The system SHALL provide a function to retrieve race metadata for a given army name. The TOML data files SHALL represent unit `shaken` config as a structured `[units.<id>.shaken]` section rather than a plain string.

#### Scenario: Valid army name returns RaceConfig with structured shaken
- **WHEN** `get_race(army_name)` is called with a valid army name
- **THEN** it returns a `RaceConfig` where each unit's `shaken` field is either `None` or a `ShakenConfig` object (not a plain string)

#### Scenario: Invalid army name raises an error
- **WHEN** `get_race(army_name)` is called with an unknown army name
- **THEN** it raises a `ValueError` describing the valid options

### Requirement: Get units for an army
The system SHALL provide a function to retrieve all units belonging to a given army.

#### Scenario: Valid army name returns unit mapping
- **WHEN** `get_units(army_name)` is called with a valid army name
- **THEN** it returns a `dict[str, UnitConfig]` keyed by unit identifier, containing only units whose `race` field matches `army_name`

#### Scenario: Units are filtered by race
- **WHEN** `get_units(army_name)` is called
- **THEN** only units where `unit.race == army_name` are included in the result

### Requirement: Get models for an army
The system SHALL provide a function to retrieve all models belonging to a given army.

#### Scenario: Valid army name returns model mapping
- **WHEN** `get_models(army_name)` is called with a valid army name
- **THEN** it returns a `dict[str, ModelConfig]` keyed by model identifier, containing only models whose `race` field matches `army_name`

### Requirement: Get equipment for an army
The system SHALL provide a function to retrieve all equipment belonging to a given army.

#### Scenario: Valid army name returns equipment mapping
- **WHEN** `get_equipments(army_name)` is called with a valid army name
- **THEN** it returns a `dict[str, EquipmentConfig]` keyed by equipment identifier, containing only equipment whose `race` field matches `army_name`

### Requirement: Get full army configuration
The system SHALL provide a function to retrieve the complete, validated `ArmyConfig` for a given army.

#### Scenario: Valid army name returns full ArmyConfig
- **WHEN** `get_army(army_name)` is called (re-exported from `armies.py`)
- **THEN** it returns the full `ArmyConfig` containing all races, units, models, and equipment

#### Scenario: Missing TOML file raises an error
- **WHEN** `get_army(army_name)` is called for an army with no corresponding TOML file
- **THEN** it raises an appropriate error indicating the file is not found

### Requirement: Support Regeneration unit special
The system SHALL accept `"Regeneration"` as a valid `UnitSpecial` key in unit special dicts.

#### Scenario: Regeneration key validates
- **WHEN** a TOML unit entry contains `[units.xxx.special]` with a `"Regeneration"` key
- **THEN** it parses without a validation error

### Requirement: Support Hans Sverre's second favorite rule unit special
The system SHALL accept `"Hans Sverre's second favorite rule"` as a valid `UnitSpecial` key in unit special dicts.

#### Scenario: Hans Sverre's second favorite rule key validates
- **WHEN** a TOML unit entry contains `[units.xxx.special]` with a `"Hans Sverre's second favorite rule"` key
- **THEN** it parses without a validation error
