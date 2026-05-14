## Why

Army building currently requires repetitive chained method calls when performing the same action on multiple models in a unit. For example, upgrading all four models in an infantry unit requires four separate `.upgrade_unit()` calls. Adding convenience methods reduces boilerplate and makes the builder API more ergonomic, particularly in build scripts and interactive configuration.

## What Changes

Four new methods on `ArmyList`:

- `.upgrade_full_unit(unit_key, upgrade_model_name, race_config)` — Replace all models in a unit with an upgrade model (e.g., upgrade all infantry to elite infantry in one call)
- `.upgrade_all_models(unit_key, equipment_name, race_config)` — Add the same equipment upgrade to all models in a unit (validates all models can take the upgrade before applying)
- `.duplicate_unit(unit_key)` — Add a copy of an existing unit to the army list (enables "build once, replicate" workflows)
- `.delete_unit(unit_key)` — Remove a unit from the army list by key (completes CRUD operations)

All methods are chainable, fail-fast on validation errors, and delegate to existing methods under the hood.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `team-builder`: Add four convenience methods to `ArmyList` for bulk operations (upgrade all models in a unit, duplicate units, delete units) to reduce boilerplate in army assembly workflows.

## Impact

- **Code**: `src/spf/armies/build.py` (ArmyList class)
- **API**: Adds four new public methods to ArmyList
- **Tests**: Unit tests for each method covering success cases and validation failures

## Non-goals

- Batch operations across multiple units
- API changes to existing methods
- Builder fluent interface helpers beyond method chaining
