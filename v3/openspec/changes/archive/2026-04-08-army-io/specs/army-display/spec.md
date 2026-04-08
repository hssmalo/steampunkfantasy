## ADDED Requirements

### Requirement: Pretty-print an army to the console
The system SHALL provide a function to display an `Army` in a human-readable, richly formatted layout using the `rich` library.

#### Scenario: Display renders army name and race
- **WHEN** `print_army(army, race_config)` is called
- **THEN** the output includes the army's race name as a heading

#### Scenario: Display renders each unit with its models
- **WHEN** `print_army(army, race_config)` is called
- **THEN** each unit in the army is shown with all its models and any equipment upgrades

#### Scenario: Display renders total cost
- **WHEN** `print_army(army, race_config)` is called
- **THEN** the total MP/CP/XP/IP cost of the army is shown in the output

### Requirement: CLI command to display an army
The system SHALL provide a CLI command to load an army from a file and display it using the rich formatter.

#### Scenario: show-army command displays a saved army
- **WHEN** the user runs `spf show-army <filename>`
- **THEN** the army is loaded from the armies path and printed to the console using `print_army`

#### Scenario: show-army with unknown file reports an error
- **WHEN** the user runs `spf show-army <filename>` and the file does not exist
- **THEN** an error message is shown and the process exits with a non-zero status
