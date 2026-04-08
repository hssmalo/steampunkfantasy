## ADDED Requirements

### Requirement: Save army to disk
The system SHALL provide a function to serialize an `Army` to a JSON file identified by an army name. The file path SHALL be derived as `config.paths.armies / f"{army_name}.json"`. Only structural data (race name, unit names, model names, upgrades) SHALL be written; embedded config objects SHALL NOT be serialized.

#### Scenario: Saving an army creates a JSON file
- **WHEN** `save_army(army, army_name)` is called with a valid `Army` and an army name
- **THEN** a JSON file is created at `config.paths.armies / f"{army_name}.json"` containing the army's race, unit names, model names, and upgrade lists

#### Scenario: Saving creates parent directories
- **WHEN** `save_army(army, army_name)` is called and `config.paths.armies` does not exist
- **THEN** the directory is created and the file is written successfully

### Requirement: Load army from disk
The system SHALL provide a function to deserialize an `Army` from a JSON file identified by an army name. The file path SHALL be derived as `config.paths.armies / f"{army_name}.json"`. It SHALL rehydrate embedded config objects from the race TOML via `get_race()`.

#### Scenario: Loading a saved army round-trips correctly
- **WHEN** an `Army` is saved with `save_army(army, army_name)` and then reloaded with `load_army(army_name)`
- **THEN** the reloaded `Army` equals the original `Army`

#### Scenario: Loading a file with an unknown race raises an error
- **WHEN** `load_army(army_name)` is called and the JSON contains an unknown race name
- **THEN** a `ValueError` is raised describing the unknown race

#### Scenario: Loading a missing army raises an error
- **WHEN** `load_army(army_name)` is called and no file exists for that name
- **THEN** a `FileNotFoundError` is raised

### Requirement: Armies path in config
The system SHALL expose an `armies` path in the `PathsConfig` configuration, pointing to the project's `armies/` directory by default.

#### Scenario: Config provides armies path
- **WHEN** the application config is loaded
- **THEN** `config.paths.armies` is a `Path` pointing to the configured armies directory
