## Why

`src/spf/armies/data.py` currently co-locates three data classes (`Army`, `ArmyUnit`, `ArmyModel`) and all associated builder/validation functions in a single file. As the army data models grow more complex, this file will become difficult to navigate and maintain. Splitting it now, before complexity increases, establishes a clean module structure.

## What Changes

- `src/spf/armies/data.py` is deleted and replaced by three focused modules:
  - `src/spf/armies/model.py` — `ArmyModel` dataclass and model-level functions (`available_equipment`, `upgrade_model`, slot/requirement helpers)
  - `src/spf/armies/unit.py` — `ArmyUnit` dataclass and unit-level functions (`available_models`, `upgrade_unit`, `unit_cost`, `unit_points`)
  - `src/spf/armies/army.py` — `Army` dataclass and army-level functions (`add_unit`, `total_cost`, `validate_army`)
- `src/spf/armies/__init__.py` re-exports everything currently public, keeping external imports unchanged (**no breaking change**)

## Non-goals

- No changes to public API, behavior, or data semantics
- No new capabilities or logic added during this refactor
- No changes to TOML schemas or race configs

## Capabilities

### New Capabilities

_(none — this is a pure structural refactor)_

### Modified Capabilities

_(none — no spec-level behavior changes)_

## Impact

- `src/spf/armies/data.py` replaced by `army.py`, `unit.py`, `model.py`
- `src/spf/armies/__init__.py` updated to re-export public symbols
- Any internal imports of `spf.armies.data` updated to the new modules
- Tests referencing `spf.armies.data` updated to import from new paths (or from `spf.armies` directly)
