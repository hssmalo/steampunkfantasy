## Why

The current army module exposes raw `ArmyModel`/`ArmyUnit`/`Army` objects that carry config references but compute nothing — every downstream consumer (display, validation, export) must re-derive effective state by threading `race_config` through all call sites. Game rules like equipment replacement, special-rule stacking, and assault-stat accumulation are not captured anywhere, making them impossible to implement consistently as the codebase grows.

## What Changes

- **BREAKING**: `Army` renamed to `ArmyList`; existing `Army` name now refers to the new resolved type
- New `armies/build.py` module containing `ArmyList`, `ArmyUnit`, `ArmyModel` (build-time assembly layer)
- New resolved types `Army`, `Unit`, `Model` replacing the current thin dataclasses as the public API
- Free functions `add_unit`, `upgrade_unit`, `upgrade_model` converted to methods on `ArmyList`/`ArmyUnit`/`ArmyModel`
- `ArmyList.resolve(race_config) -> Army` produces the fully enriched army; `io.load_army()` calls this automatically
- `Model` computes effective equipment (Rule A: defaults discarded when upgrades present), stacked specials, and full resolved `AssaultConfig` via `assault()` method
- `Unit` and `Army` expose `cost()` methods; no `race_config` needed after resolution
- `Stacker.append` renamed to `Stacker.extend`; invalid stacking operations raise clear errors

## Capabilities

### New Capabilities
- `resolved-army`: Resolved `Army` / `Unit` / `Model` types with self-contained properties (`equipment`, `unit_specials`, `model_specials`, `assault()`, `cost()`) that require no `race_config` after construction

### Modified Capabilities
- `army-module-structure`: Module layout changes — new `build.py`, resolved types in `model.py`/`unit.py`/`army.py`
- `team-builder`: Build-time API moves from free functions to methods on `ArmyList`/`ArmyUnit`/`ArmyModel`
- `team-model`: `ArmyModel`/`ArmyUnit` contracts updated; `ArmyModel.config` retained for build-time validation
- `unit-cost`: `unit_cost()` free function replaced by `Unit.cost()` method with identical `upgrade_all` semantics
- `army-io`: `load_army()` return type changes from `ArmyList` to `Army`; `save_army()` still accepts `ArmyList`

## Non-goals

- Markdown / LaTeX document generation (planned but out of scope)
- Changes to TOML schema structure (only the `Stacker.append → extend` rename)
- Changing serialization format (JSON stays thin — names only)

## Impact

- `src/spf/armies/` — new `build.py`, rewritten `model.py`, `unit.py`, `army.py`, `io.py`, `__init__.py`
- `src/spf/schemas/race.py` — `Stacker` field rename
- `src/spf/frontends/cli/army.py` — updated to use resolved `Army`
- All existing tests for army module
