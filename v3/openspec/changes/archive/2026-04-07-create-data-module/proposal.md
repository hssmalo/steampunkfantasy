## Why

The codebase has legacy data access code in `_old_data.py` that reads army data directly from TOML files using the deprecated `pyconfs`/`munch` libraries. A new, structured army loading system exists in `armies.py` backed by validated Pydantic schemas in `schemas/army.py`. The new `data.py` module will expose the same data querying capabilities using the new army infrastructure.

## What Changes

- **New file** `src/spf/data.py` providing functions to query army data (units, models, equipments, races) using `ArmyConfig` from the new schema system.
- Legacy `_old_data.py` functionality is reimplemented on top of `get_army()` from `armies.py`, replacing raw TOML manipulation with typed model access.
- No changes to existing files; `_old_data.py` remains intact for now.

## Capabilities

### New Capabilities

- `army-data-access`: Functions for listing and retrieving units, models, and equipment from an army, using the validated `ArmyConfig` schema.

### Modified Capabilities

_(none)_

## Impact

- `src/spf/data.py` — new file
- Depends on `src/spf/armies.py` and `src/spf/schemas/army.py`
- No breaking changes; purely additive
