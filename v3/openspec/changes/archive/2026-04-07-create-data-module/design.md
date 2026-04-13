## Context

`_old_data.py` provides `Race`, `Unit`, `Model`, `Equipment`, `Team`, and `Costs` dataclasses that load army data by reading TOML files directly via the `pyconfs` library and wrapping them in `munch.Munch` objects. This is fragile (no validation), uses deprecated dependencies, and is hard to test.

The new `armies.py` introduces `get_army(army_name)` which returns a fully validated `ArmyConfig` Pydantic model. All army data (units, models, equipment, race metadata) is now accessible as typed Python objects.

The goal is a clean `data.py` that exposes the same query-level functionality as `_old_data.py` but built on the new schema system.

## Goals / Non-Goals

**Goals:**
- Provide `get_units`, `get_models`, `get_equipment`, `get_race` (and similar) functions in `data.py` that return typed objects from `ArmyConfig`.
- Support listing all available army names.
- Match the functional surface area that other modules rely on from `_old_data.py` (filtering units/models/equipment by army name).

**Non-Goals:**
- Recreating the LaTeX rendering (`write_info`, `generate_neat_dict`) — those belong in a rendering layer, not in data access.
- Recreating `Team` with its fund management — that is application logic, not data access.
- Removing or modifying `_old_data.py` (left for a separate cleanup task).
- Migrating callers of `_old_data.py` in this change.

## Decisions

### Decision: Module-level functions, not a class hierarchy

`_old_data.py` wraps everything in `Race`, `Unit`, `Model` dataclasses. In `data.py`, we expose plain functions (`get_units`, `get_models`, etc.) that return the Pydantic models from the schema directly.

**Rationale:** The schema models (`UnitConfig`, `ModelConfig`, `EquipmentConfig`) already capture the data structure. Wrapping them in another class layer adds complexity without benefit. Callers work with the typed models directly.

**Alternative considered:** Mirror the old class hierarchy as thin wrappers — rejected because it duplicates types and couples `data.py` tightly to the old design.

### Decision: `ArmyName` as the filter key

All query functions accept an `ArmyName` (the literal type from `type_aliases.py`) to filter results. Each `UnitConfig`, `ModelConfig`, and `EquipmentConfig` already carries a `race: ArmyName` field for this purpose.

**Rationale:** Consistent with the schema and avoids ad-hoc string filtering.

### Decision: Return dicts keyed by identifier string

Functions return `dict[str, UnitConfig]` (etc.) keyed by the internal identifier (TOML key), matching the old `munch.Munch` interface shape. This keeps callers familiar.

## Risks / Trade-offs

- [Risk] `_old_data.py` callers may depend on mutable `munch.Munch` attribute access (dot notation) → Mitigation: Pydantic models also support attribute access; breaking only happens if callers mutate objects.
- [Risk] Some behavior in `_old_data.py` (e.g., `available_upgrades`, equipment limit logic) is complex and stateful → Mitigation: That logic stays out of `data.py` and belongs to application logic; we only expose pure data access here.
