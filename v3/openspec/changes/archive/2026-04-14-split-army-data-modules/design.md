## Context

`src/spf/armies/data.py` is ~354 lines containing three frozen dataclasses (`ArmyModel`, `ArmyUnit`, `Army`) plus ~20 helper and public functions. A planned expansion of the army data models will significantly grow this file. Splitting now keeps each module focused and makes future additions easier to locate and review.

The existing `src/spf/armies/__init__.py` already acts as the package entry point. External callers (CLI commands, tests) currently import from `spf.armies` or `spf.armies.data`. The `spf.armies.data` path will be intentionally removed; callers using it will be migrated as part of this change.

## Goals / Non-Goals

**Goals:**
- Split `data.py` into `model.py`, `unit.py`, `army.py` with a logical grouping of classes and functions
- Preserve all existing public symbols via `__init__.py` re-exports
- Update all internal `from spf.armies.data import …` references to the new modules

**Non-Goals:**
- No behavioral changes, no API additions, no logic moves between functions
- No changes to TOML schemas, race configs, or display/IO layers

## Decisions

### Module boundaries follow data ownership

Each module owns its primary dataclass and the functions that operate on it:

| Module | Class | Functions |
|---|---|---|
| `model.py` | `ArmyModel` | `_remaining_slots`, `_satisfies_requirement`, `_unsatisfied_groups`, `_format_failed_group`, `_satisfies_requires`, `_resolve_model`, `available_equipment`, `upgrade_model` |
| `unit.py` | `ArmyUnit` | `_make_default_team_model`, `_make_default_team_unit`, `_resolve_unit`, `available_models`, `upgrade_unit`, `unit_cost`, `unit_points` |
| `army.py` | `Army` | `add_unit`, `total_cost`, `validate_army` |

`unit.py` imports from `model.py`; `army.py` imports from both. This matches the natural dependency direction: `ArmyModel` → `ArmyUnit` → `Army`.

**Alternative considered — keep a single `data.py`:** Simpler short-term, but deferred cost grows as the file expands. Rejected.

**Alternative considered — one `models/` sub-package:** Adds a nesting level without benefit at current scale. Rejected.

### `__init__.py` re-exports everything currently public

`__init__.py` will explicitly re-export all public names so that `from spf.armies import Army` continues to work. The `spf.armies.data` sub-module path is intentionally removed — all existing callers (`io.py`, tests, CLI) are updated to import from `spf.armies` directly.

## Risks / Trade-offs

- **Circular imports** — `unit.py` calls functions from `model.py`, and `army.py` calls both. Import order must follow the dependency direction. Mitigation: enforce `model → unit → army`; no back-references.
- **Test import churn** — tests currently importing `from spf.armies.data import …` need updating. Mitigation: migrate all test imports to `from spf.armies import …` which is stable long-term.

## Migration Plan

1. Create `model.py`, `unit.py`, `army.py` with contents moved from `data.py`
2. Update `__init__.py` to re-export all public names from the new modules
3. Delete `data.py`
4. Update any remaining internal references to `spf.armies.data`
5. Run tests and type-checker to verify no regressions
