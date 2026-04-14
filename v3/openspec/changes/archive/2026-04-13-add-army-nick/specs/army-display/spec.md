## MODIFIED Requirements

### Requirement: Pretty-print an army to the console
The system SHALL provide a function to display an `Army` in a human-readable, richly formatted layout using the `rich` library.

#### Scenario: Display renders army nick and race name in header
- **WHEN** `print_army(army, race_config)` is called
- **THEN** the output includes a rule header showing the army's nick and race name in the format `"<nick> — <Race> Army"`

#### Scenario: Display renders each unit with its models
- **WHEN** `print_army(army, race_config)` is called
- **THEN** each unit in the army is shown with all its models and any equipment upgrades

#### Scenario: Display renders total cost
- **WHEN** `print_army(army, race_config)` is called
- **THEN** the total MP/CP/XP/IP cost of the army is shown in the output
