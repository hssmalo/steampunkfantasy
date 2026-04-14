## Why

Equipment currently uses two separate cost fields (`cost` and `model_cost`) to distinguish between a one-time upgrade cost for the whole unit versus a per-model cost, but this split is implicit and the fields are not self-documenting. Replacing them with a single `cost` field plus an explicit `upgrade_all: bool | None` flag makes the semantics clear in the schema and TOML files.

## What Changes

- **BREAKING**: Remove `model_cost` field from `EquipmentConfig` schema
- Add `upgrade_all: bool | None` field to `EquipmentConfig` (default `None`; `None` and `False` both mean per-model, `True` means the cost applies to the whole unit once)
- Update cost calculation logic in `unit_cost` to multiply `cost` by the number of models when `upgrade_all` is not `True`
- Update all valid TOML files (elf.toml, ork.toml, ogre.toml) to replace `model_cost` with `cost` + `upgrade_all = false`

## Non-goals

- Changing how equipment without a cost (default equipment) behaves — no cost, no `upgrade_all` needed
- Changing the `Cost` type or any other schema fields
- Migrating invalid (legacy-format) TOML files

## Capabilities

### New Capabilities

_(none)_

### Modified Capabilities

- `unit-cost`: Equipment cost calculation must now account for `upgrade_all` — when `False` (or `None`), the equipment cost is multiplied by the number of models in the unit; when `True`, it is applied once regardless of model count.

## Impact

- `src/spf/schemas/race.py`: `EquipmentConfig` schema change (remove `model_cost`, add `upgrade_all`)
- `src/spf/armies/data.py`: `unit_cost` and related validation logic must use `upgrade_all` to determine how to apply equipment cost
- `races/elf.toml`, `races/ork.toml`, `races/ogre.toml`: migrate `model_cost` entries to `cost` + `upgrade_all = false`
