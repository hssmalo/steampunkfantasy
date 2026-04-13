## MODIFIED Requirements

### Requirement: Pretty-print an army to the console
The system SHALL provide a function to display an `Army` in a human-readable layout using f-string bullet lists (not rich tables). The army name SHALL be displayed in bold at the top. Each unit SHALL be a top-level bullet point with its point value in parentheses after the unit name. Each model SHALL be a sub-bullet point with its combined equipment (defaults and upgrades) listed in parentheses on the same line, omitted when there is no equipment. The total cost line SHALL use `Cost.__str__()`.

#### Scenario: Display renders army nick and race name in header
- **WHEN** `print_army(army, race_config)` is called
- **THEN** the output includes a rule header showing the army's nick and race name in the format `"<nick> — <Race> Army"`

#### Scenario: Display renders army name in bold
- **WHEN** `print_army(army, race_config)` is called
- **THEN** the army nick is displayed in bold above the unit list

#### Scenario: Display renders each unit as a top-level bullet with points
- **WHEN** `print_army(army, race_config)` is called
- **THEN** each unit appears as a `- <unit name> (N pts)` bullet point where N is the unit's points value

#### Scenario: Display renders each model as a sub-bullet
- **WHEN** `print_army(army, race_config)` is called
- **THEN** each model appears indented as `  - <model name>` under its unit

#### Scenario: Model with equipment shows it in parentheses
- **WHEN** a model has default equipment or upgrades
- **THEN** the combined equipment names are shown in parentheses on the same line as the model name

#### Scenario: Model with no equipment omits parentheses
- **WHEN** a model has no default equipment and no upgrades
- **THEN** no parentheses appear on the model line

#### Scenario: Display renders total cost using Cost.__str__()
- **WHEN** `print_army(army, race_config)` is called
- **THEN** the total cost is shown using the `Cost.__str__()` format
