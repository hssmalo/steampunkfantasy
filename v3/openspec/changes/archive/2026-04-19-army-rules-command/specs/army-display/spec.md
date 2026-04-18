## MODIFIED Requirements

### Requirement: CLI command to display an army
The system SHALL provide CLI commands under the `army` subgroup to load an army from a file and display it. The `army show` command SHALL display the cost-focused overview. The `army rules` command SHALL display the rules-reference view using `print_army_rules`.

#### Scenario: army show command displays a saved army
- **WHEN** the user runs `spf army show <army-name>`
- **THEN** the army is loaded and printed using `print_army`

#### Scenario: army rules command displays rules reference
- **WHEN** the user runs `spf army rules <army-name>`
- **THEN** the army is loaded and printed using `print_army_rules`

#### Scenario: army rules with unknown file reports an error
- **WHEN** the user runs `spf army rules <army-name>` and the file does not exist
- **THEN** an error message is shown and the process exits with a non-zero status
