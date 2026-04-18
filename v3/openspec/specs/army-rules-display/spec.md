# Spec: Army Rules Display

## Purpose

TBD — Provides a rules-reference console view of a loaded `Army`, showing specials, assault profiles, and equipment stats in a bulleted layout.

## Requirements

### Requirement: Render rules reference view of an army
The system SHALL provide a `print_army_rules(army)` function that displays a fully resolved `Army` as a rules-reference bulleted list to the console. The army nick and race name SHALL appear in a rule header. Each unit SHALL be a top-level bullet showing unit name and total cost. Unit specials SHALL be listed as a nested sub-bullet under the unit (omitted when empty). Each model SHALL be a nested bullet under its unit showing the model name and incremental upgrade cost (omitted when zero). Model specials SHALL be listed as a nested sub-sub-bullet under the model (omitted when empty). Each equipment item SHALL be listed with its name and cost (omitted when no cost). The resolved assault profile SHALL be shown for each model. Any equipment with a range profile SHALL have its range stats shown as an additional sub-bullet.

#### Scenario: Unit line shows name and total cost
- **WHEN** `print_army_rules(army)` is called
- **THEN** each unit appears as `- <unit name> (<N> pts)` where N is the unit's total point cost

#### Scenario: Unit specials appear as nested sub-bullet
- **WHEN** a unit has one or more specials
- **THEN** they appear as an indented sub-bullet `  - Specials: <name>: <value>, ...` below the unit line

#### Scenario: Unit with no specials omits specials line
- **WHEN** a unit has no specials
- **THEN** no specials line appears under the unit

#### Scenario: Model line shows name and upgrade cost when nonzero
- **WHEN** a model has a nonzero upgrade cost
- **THEN** it appears as `  - <model name> (<N> pts)` indented under its unit

#### Scenario: Model line omits cost when zero
- **WHEN** a model has zero upgrade cost
- **THEN** it appears as `  - <model name>` without a cost suffix

#### Scenario: Model specials appear as nested sub-bullet
- **WHEN** a model has one or more model-level specials
- **THEN** they appear as an indented sub-sub-bullet `    - Specials: <name>: <value>, ...` below the model line

#### Scenario: Model with no model-level specials omits specials line
- **WHEN** a model has no model-level specials
- **THEN** no model specials line appears under the model

#### Scenario: Equipment is listed with name and cost
- **WHEN** a model has effective equipment items
- **THEN** each item appears as `    - <equipment name> (<N> pts)` or `    - <equipment name>` when cost is absent

#### Scenario: Assault profile is shown for each model
- **WHEN** `print_army_rules(army)` is called
- **THEN** each model has a compact assault line showing strength, deflection, damage, and AP values

#### Scenario: Range weapon stats shown for equipment with range profile
- **WHEN** a model's effective equipment includes an item with a range profile
- **THEN** a range stats line appears showing range distance, damage, and AP for that weapon

#### Scenario: Equipment with no range profile omits range stats
- **WHEN** an equipment item has no range profile
- **THEN** no range stats line is shown for it

#### Scenario: Total cost shown at bottom
- **WHEN** `print_army_rules(army)` is called
- **THEN** the total army cost appears at the bottom using `Cost.__str__()`
