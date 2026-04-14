## Context

`EquipmentConfig` currently has two optional cost fields: `cost` (unit-level, paid once) and `model_cost` (per-model, multiplied by model count). The distinction is implicit — readers must know which field is set to understand the pricing semantics. The `unit_cost` function in `data.py` currently uses only `cost`; `model_cost` is stored in the schema but not yet applied in cost calculations, meaning TOML files with `model_cost` entries are not correctly priced today.

## Goals / Non-Goals

**Goals:**
- Replace the two-field approach with `cost` (always the numeric value) + `upgrade_all: bool | None` (the semantics flag)
- Correct the `unit_cost` calculation so per-model costs are multiplied by model count
- Migrate all valid TOML files that use `model_cost`

**Non-Goals:**
- Migrating invalid (legacy-format) TOML files
- Changing any other schema fields or cost types
- Changing how default (no-cost) equipment behaves

## Decisions

### `upgrade_all: bool | None` with `None` treated as `False`

**Decision**: `None` and `False` both mean per-model cost; `True` means unit-level cost applied once.

**Rationale**: Default equipment has neither `cost` nor `upgrade_all`. Forcing `upgrade_all = false` on all paid-per-model equipment would be verbose without adding information. `None` naturally extends "unspecified" to mean the common case (per-model), keeping TOML files minimal. This avoids a three-way enum while remaining expressive.

**Alternative considered**: A required boolean on all equipment with a `cost`. Rejected because it forces boilerplate on the majority case and changes the default-equipment rule unnecessarily.

### Keep field named `cost` (not `unit_cost` / `base_cost`)

**Decision**: The renamed target field is still called `cost`, same as existing unit and model cost fields.

**Rationale**: Consistency across the schema — all pricing uses `cost`. The `upgrade_all` flag carries the semantics; the cost value itself needs no rename.

### Multiply `cost` by number of models when `upgrade_all` is not `True`

**Decision**: In `unit_cost`, when processing equipment upgrades, multiply the equipment `cost` by the count of models in the unit if `upgrade_all` is `False` or `None`.

**Rationale**: This matches the original intent of `model_cost` — the upgrade is priced per model. Using the actual model count (from `unit.models`) rather than a nominal size ensures accuracy if units have varying effective sizes.

**Alternative considered**: Multiply by `unit.config.size`. Rejected because size is a categorical value and the number of models in the unit (from `unit.models`) is the correct runtime count.

## Risks / Trade-offs

- **Silent pricing bug fixed**: TOML files using `model_cost` were previously silently underpriced (cost was not applied). Migrating them may change calculated army costs. → Accepted: correct behavior is the goal.
- **BREAKING schema change**: Any TOML files outside the valid set that use `model_cost` will fail to load after the change. → Mitigated by scope: only valid files are in scope; legacy files already fail validation.

## Migration Plan

1. Update `EquipmentConfig` in `race.py`: remove `model_cost`, add `upgrade_all: bool | None = None`
2. Update `unit_cost` in `data.py`: multiply equipment cost by model count when `upgrade_all` is not `True`
3. Update validation logic (`available_equipment`, `validate_army`) to use `cost` (unchanged — they already check `cost`)
4. Migrate `races/elf.toml`, `races/ork.toml`, `races/ogre.toml`: replace `model_cost.<x>` with `cost.<x>` and add `upgrade_all = false`
5. Run `uv run pytest` and `uv run spf race show` on each valid race to verify

Rollback: revert schema and TOML changes; no database or external state is affected.
