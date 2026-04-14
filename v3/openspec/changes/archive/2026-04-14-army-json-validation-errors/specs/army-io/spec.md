## MODIFIED Requirements

### Requirement: Load army from disk
The system SHALL provide a function to deserialize an `Army` from a JSON file identified by an army name. The file path SHALL be derived as `config.paths.armies / f"{army_name}.json"`. It SHALL rehydrate embedded config objects from the race TOML via `get_race()`. The `nick` key MUST be present in the JSON; if it is missing a `KeyError` SHALL be raised. Before constructing any `ArmyUnit` or `ArmyModel`, the system SHALL validate that all unit names and model names in the JSON exist in the race config; if any are unknown, a `ValueError` SHALL be raised listing all invalid entries (unit index, unit name, model index, model name as applicable).

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

#### Scenario: Loading a file with an unknown unit name raises a descriptive error
- **WHEN** `load_army(army_name)` is called and a unit entry has a name not present in the race config
- **THEN** a `ValueError` is raised with a message identifying the unit index and the invalid name

#### Scenario: Loading a file with an unknown model name raises a descriptive error
- **WHEN** `load_army(army_name)` is called and a model entry has a name not present in the race config
- **THEN** a `ValueError` is raised with a message identifying the unit, model index, and the invalid model name
