## MODIFIED Requirements

### Requirement: Save army to disk
The system SHALL provide a function to serialize an `Army` to a JSON file identified by an army name. The file path SHALL be derived as `config.paths.armies / f"{army_name}.json"`. Only structural data (race name, nick, unit names, model names, upgrades) SHALL be written; embedded config objects SHALL NOT be serialized. The `nick` field SHALL always be written to the JSON output.

#### Scenario: Saving an army creates a JSON file
- **WHEN** `save_army(army, army_name)` is called with a valid `Army` and an army name
- **THEN** a JSON file is created at `config.paths.armies / f"{army_name}.json"` containing the army's race, nick, unit names, model names, and upgrade lists

#### Scenario: Saving creates parent directories
- **WHEN** `save_army(army, army_name)` is called and `config.paths.armies` does not exist
- **THEN** the directory is created and the file is written successfully

### Requirement: Load army from disk
The system SHALL provide a function to deserialize an `Army` from a JSON file identified by an army name. The file path SHALL be derived as `config.paths.armies / f"{army_name}.json"`. It SHALL rehydrate embedded config objects from the race TOML via `get_race()`. The `nick` key MUST be present in the JSON; if it is missing a `KeyError` SHALL be raised.

#### Scenario: Loading a saved army round-trips correctly
- **WHEN** an `Army` is saved with `save_army(army, army_name)` and then reloaded with `load_army(army_name)`
- **THEN** the reloaded `Army` equals the original `Army`, including its `nick`

#### Scenario: Loading a file with an unknown race raises an error
- **WHEN** `load_army(army_name)` is called and the JSON contains an unknown race name
- **THEN** a `ValueError` is raised describing the unknown race

#### Scenario: Loading a missing army raises an error
- **WHEN** `load_army(army_name)` is called and no file exists for that name
- **THEN** a `FileNotFoundError` is raised

#### Scenario: Loading a file without nick raises an error
- **WHEN** `load_army(army_name)` is called and the JSON file has no `nick` key
- **THEN** a `KeyError` is raised
