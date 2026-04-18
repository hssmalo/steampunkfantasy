# Spec: Army IO

## Purpose

Provides serialization and deserialization of `Army` objects to and from JSON files on disk, enabling armies to be saved and reloaded across sessions.

## Requirements

### Requirement: Save army to disk
The system SHALL provide `save_army(army_list, army_name, tournament?) -> None` that serializes an `ArmyList` (build-time type) to JSON. The file path SHALL be derived as `config.paths.armies / f"{army_name}.json"`. The serialization format is unchanged: race name, nick, unit names, model names, and upgrade name lists. Resolved `EquipmentConfig` objects are NOT serialized; only the upgrade name strings from `ArmyModel.upgrades` are written.

#### Scenario: Saving an army list creates a JSON file
- **WHEN** `save_army(army_list, army_name)` is called with a valid `ArmyList`
- **THEN** a JSON file is created at the expected path containing race, nick, unit names, model names, and upgrade lists

#### Scenario: Saving creates parent directories
- **WHEN** `save_army(army_list, army_name)` is called and the parent directory does not exist
- **THEN** the directory is created and the file is written successfully

### Requirement: Load army from disk
The system SHALL provide `load_army(army_name, tournament?, *, validate) -> Army` that deserializes an army from JSON and returns a fully resolved `Army` (not `ArmyList`). It SHALL call `ArmyList.resolve(race_config)` internally after building the `ArmyList`. The file path SHALL be derived as `config.paths.armies / f"{army_name}.json"`. The `nick` key MUST be present in the JSON; if it is missing a `KeyError` SHALL be raised. Before constructing any `ArmyUnit` or `ArmyModel`, the system SHALL validate that all unit names and model names in the JSON exist in the race config; if any are unknown, a `ValueError` SHALL be raised listing all invalid entries (unit index, unit name, model index, model name as applicable). The `validate` parameter continues to control whether `validate_army()` is called before resolving.

#### Scenario: Loading a saved army round-trips correctly
- **WHEN** an `ArmyList` is saved with `save_army(army_list, army_name)` and reloaded with `load_army(army_name)`
- **THEN** the reloaded `Army` contains the same race, nick, unit names, model names, and upgrade names as the original `ArmyList`

#### Scenario: Loading returns a resolved Army, not ArmyList
- **WHEN** `load_army(army_name)` is called
- **THEN** the return value SHALL be an instance of `Army` (resolved tier)
- **THEN** all models in the returned army SHALL have `default_equipment` and `upgrade_equipment` populated

#### Scenario: Loading a file with an unknown race raises an error
- **WHEN** `load_army(army_name)` is called and the JSON contains an unknown race name
- **THEN** a `ValueError` is raised describing the unknown race

#### Scenario: Loading a missing army raises an error
- **WHEN** `load_army(army_name)` is called and no file exists for that name
- **THEN** a `FileNotFoundError` is raised

#### Scenario: Loading a file without nick raises an error
- **WHEN** `load_army(army_name)` is called and the JSON file has no `nick` key
- **THEN** a `KeyError` is raised

#### Scenario: Loading a file with an unknown unit name raises a descriptive error
- **WHEN** `load_army(army_name)` is called and a unit entry has a name not present in the race config
- **THEN** a `ValueError` is raised identifying the unit index and the invalid name

#### Scenario: Loading a file with an unknown model name raises a descriptive error
- **WHEN** `load_army(army_name)` is called and a model entry has a name not present in the race config
- **THEN** a `ValueError` is raised identifying the unit, model index, and the invalid model name

### Requirement: Armies path in config
The system SHALL expose an `armies` path in the `PathsConfig` configuration, pointing to the project's `armies/` directory by default.

#### Scenario: Config provides armies path
- **WHEN** the application config is loaded
- **THEN** `config.paths.armies` is a `Path` pointing to the configured armies directory
