## Why

Two bugs in `build.py` cause `validate_army` (and `available_equipment`) to produce false slot-count failures when models have upgrade equipment — specifically, Rule A (defaults discarded when upgrades present) is not applied in slot accounting, and validation checks each upgrade against remaining slots that already include that upgrade's own consumption.

## What Changes

- Fix `_remaining_slots` to count only upgrade equipment (never defaults) when computing available slots, consistently applying Rule A at the accounting layer
- Fix `validate_army` to validate each upgrade sequentially against a partial model that excludes the upgrade being checked, mirroring the build-time `upgrade()` semantics
- `available_equipment` is corrected as a side effect of the `_remaining_slots` fix: models with hand-consuming defaults will now correctly show upgrades as available

## Non-goals

- No changes to the TOML schema or army JSON format
- No changes to the resolved `Model.equipment` property (already implements Rule A correctly)
- No changes to error message format or wording

## Capabilities

### New Capabilities

_(none)_

### Modified Capabilities

- `team-builder`: Slot accounting in `_remaining_slots` and the `validate_army` sequential-checking contract both have spec-level behavior that is currently unspecified or incorrect
- `army-load-validation`: The scenario describing "unsatisfied slot requirement" in `validate_army` implicitly assumed correct slot counting; the fix changes what counts as a valid army

## Impact

- `src/spf/armies/build.py` — `_remaining_slots` and `validate_army`
- Tests for `validate_army`, `available_equipment`, and `upgrade_model` with models that have default equipment
