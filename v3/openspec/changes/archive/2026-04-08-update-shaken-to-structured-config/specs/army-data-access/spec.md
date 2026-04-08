## MODIFIED Requirements

### Requirement: Get race metadata for an army
The system SHALL provide a function to retrieve race metadata for a given army name. The TOML data files SHALL represent unit `shaken` config as a structured `[units.<id>.shaken]` section rather than a plain string.

#### Scenario: Valid army name returns RaceConfig with structured shaken
- **WHEN** `get_race(army_name)` is called with a valid army name
- **THEN** it returns a `RaceConfig` where each unit's `shaken` field is either `None` or a `ShakenConfig` object (not a plain string)

#### Scenario: Invalid army name raises an error
- **WHEN** `get_race(army_name)` is called with an unknown army name
- **THEN** it raises a `ValueError` describing the valid options
