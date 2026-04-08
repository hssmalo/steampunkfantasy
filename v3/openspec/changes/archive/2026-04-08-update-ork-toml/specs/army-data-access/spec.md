## ADDED Requirements

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
