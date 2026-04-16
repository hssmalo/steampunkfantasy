## Context

The `spf.armies` module currently has three thin dataclasses (`Army`, `ArmyUnit`, `ArmyModel`) that carry config references but perform no computation. Every consumer — display, validation, cost calculation — passes `race_config` as a second argument to free functions. Game rules for equipment replacement, special-rule stacking, and assault-stat modification exist in the TOML schema but are not evaluated anywhere.

The change introduces a two-tier architecture: a **build-time** layer for assembling and mutating army lists (renamed `ArmyList`/`ArmyUnit`/`ArmyModel`, moved to `build.py`), and a **resolved** layer (`Army`/`Unit`/`Model`) that is fully self-contained after construction.

## Goals / Non-Goals

**Goals:**
- `ArmyList.resolve(race_config) -> Army` produces a fully enriched army; all downstream code operates on resolved types only
- `Model` correctly applies equipment replacement (Rule A), special stacking, and Stacker-based assault modifications
- `Unit.cost()` and `Army.cost()` are the authoritative cost calculations; no `race_config` needed
- Build-time mutation API (`add_unit`, `upgrade_model`, etc.) becomes methods on `ArmyList`/`ArmyUnit`/`ArmyModel`
- `io.load_army()` returns resolved `Army` transparently

**Non-Goals:**
- Markdown/LaTeX export
- Changes to TOML file format (beyond `Stacker.append → extend`)
- Changes to JSON serialization format

## Decisions

### D1: Two-tier naming — `ArmyList` (build) vs `Army` (resolved)

The current `Army` name is reused for the resolved type, and the build-time assembly class becomes `ArmyList`. This is the least surprising name for consumers: after `load_army()` you get an `Army`; when building manually you work with an `ArmyList`.

**Alternative considered**: Keep `Army` for build-time, introduce `ResolvedArmy`. Rejected — callers almost always want the resolved form; it should get the simple name.

### D2: Build-time layer in `build.py`, not exposed from `__init__`

`ArmyList`, `ArmyUnit`, `ArmyModel` live in `spf.armies.build`. They are importable for callers that construct armies in code, but not re-exported from `spf.armies`. This keeps the default import surface focused on the resolved API.

**Alternative considered**: Keep all classes in their current files. Rejected — mixing build-time and resolved types in the same module creates ambiguity.

### D3: `race_config` passed explicitly to every mutation method

`ArmyList.add_unit(name, race_config)`, `ArmyModel.upgrade(name, race_config)`, etc. all take `race_config` as an explicit parameter rather than storing it on the object.

**Alternative considered**: Store `race_config` on `ArmyList`. Rejected — would make `ArmyList` impure data (can't compare, harder to serialize) and couples the build object to a specific config instance.

### D4: Equipment discard — Rule A

When `ArmyModel` has any upgrade equipment (cost ≠ None), all default equipment (cost = None) is discarded. `Model.equipment` returns `upgrade_equipment if upgrade_equipment else default_equipment`.

**Rationale**: The TOML schema has no `replaces` field on `EquipmentConfig`, so there is no slot-level conflict relationship. Rule A is the simplest consistent rule and matches the game design intent (upgrades supersede the default loadout).

### D5: `Model.cost()` is intrinsic only; `Unit.cost()` is authoritative

`Model.cost()` sums upgrade equipment costs without applying the `upgrade_all` multiplier. `Unit.cost()` implements the full `upgrade_all` logic (per-model pricing × unit size). `Army.cost()` sums `unit.cost()`. The three-level hierarchy is additive at the unit boundary, not the model boundary.

**Rationale**: `upgrade_all=False` is a unit-level pricing concept — a model cannot correctly compute its own cost contribution without knowing how many models are in its unit.

### D6: Stacker errors raised at `Model.assault()` call time

Invalid stacking operations (e.g., `add` on a `Die` string, `add` on `ap="N/A"`) raise `ValueError` when `Model.assault()` is called, not at TOML load time.

**Rationale**: `Stacker` is a generic type and doesn't know its field semantics at construction. The per-field semantics are enforced in `Model.assault()` where field types are known. This produces clear, actionable errors pointing at the offending equipment.

### D7: `ArmyModel.config: ModelConfig` retained

`ArmyModel` keeps its `config` field for build-time validation (`upgrade_model` checks slot requirements against `config.equipment_limit` and `config.type`).

**Alternative considered**: Strip config from `ArmyModel`, validate only at resolve time. Rejected — early validation at mutation time gives better error messages closer to the call site.

### D8: Stacking order — Unit config → Model config → Equipment

For `unit_specials`: `unit.config.special | model.config.unit_special | equip.unit_special` (later entries win). For `model_specials`: `model.config.special | equip.model_special`. Equipment iteration order matches `Model.equipment` order.

## Risks / Trade-offs

- **Breaking rename** (`Army` → `ArmyList`): Any external code importing `Army` from `spf.armies` will break. Mitigated by updating all internal call sites in the same change; there are no known external consumers.

- **`unit_cost()` free function removed**: External callers using `from spf.armies import unit_cost` will break. Mitigated by `Unit.cost()` being a direct drop-in with identical semantics.

- **`validate_army()` moves to `ArmyList`**: Currently called in `io.load_army()`. After this change, it is called before `.resolve()`. The validation surface is unchanged; only the call site moves.

- **`Stacker.extend` rename**: No valid TOML files use `Stacker.append`; the rename is safe. Legacy (invalid) TOML files for darkelf/dwarf/gnome may need updating eventually.

## Migration Plan

All changes are within the `spf` package. Steps:
1. Rename `Stacker.append → extend` in `schemas/race.py`
2. Create `armies/build.py` with `ArmyList`, `ArmyUnit`, `ArmyModel` and their methods (migrating logic from current free functions)
3. Rewrite `armies/model.py` → `Model` resolved type
4. Rewrite `armies/unit.py` → `Unit` resolved type
5. Rewrite `armies/army.py` → `Army` resolved type with `ArmyList.resolve()` implementation
6. Update `armies/io.py` — `load_army()` returns `Army`, `save_army()` accepts `ArmyList`
7. Update `armies/__init__.py` exports
8. Update `frontends/cli/army.py` and any other consumers
9. Update / add tests

No database migrations or deployment steps required.

## Open Questions

- Should `Model.assault()` be a `@property` (since it's a pure computation from stored data) or a method? Currently specified as a method; this can be decided during implementation.
- Does `Unit` need an `armor` property (from `UnitConfig.armor`) for display purposes? Not required by this change but may be needed for future export work.
