## Context

The `Army` dataclass already holds all data required for a rules reference view: resolved `Unit` objects carry `unit_specials`, `Model` objects carry `model_specials`, a resolved `assault()` method, and `equipment` which may include an `EquipmentRangeConfig` in the `.range` field. No new data loading or schema changes are needed.

The current `print_army` function in `spf/armies/io.py` provides a cost-focused overview. The new view requires a different rendering pass over the same `Army` object.

## Goals / Non-Goals

**Goals:**
- New `army rules` CLI subcommand registered alongside `army show`
- New `print_army_rules` display function in `spf/armies/io.py`
- Show specials, assault, and range weapon profiles per model

**Non-Goals:**
- No changes to army loading, validation, saving, or the `army show` format
- No new schema fields or data sources

## Decisions

### Decision: Add `print_army_rules` to `io.py` rather than a new module

The existing `print_army` lives in `io.py` and the module already imports all needed types (`Army`, `stdout`). Keeping both functions together avoids an extra module for a single function. If display logic grows, extraction is straightforward later.

*Alternatives considered:* a separate `display.py` — adds indirection with no current benefit.

### Decision: Access range attacks from `model.equipment` directly

Range attacks are on `EquipmentConfig.range` (an `EquipmentRangeConfig | None`). The `model.equipment` property already returns the effective equipment (upgrades override defaults). Iterating `model.equipment` and checking `.range is not None` is sufficient to collect all range weapons without any new resolver.

*Alternatives considered:* adding a `range_attacks()` method on `Model` — not needed yet, premature abstraction.

### Decision: Show assault stats inline after model specials

The `model.assault()` method returns a fully resolved `AssaultConfig`. Display it as a compact one-liner under the model bullet (e.g. `Assault: STR 3/4 d6, DEF 2/3 d4, DMG d6, AP 1`). Range weapons appear as additional sub-sub-bullets if present.

### Decision: Cost display for models uses `model.cost()` (upgrade cost only)

`model.cost()` returns only the upgrade equipment cost (no base unit cost). This matches the user request: "model name and cost" where cost is the incremental upgrade cost. If zero, omit the cost display.

## Risks / Trade-offs

- [Assault format verbosity] → Keep the display compact; `AssaultConfig` has many fields. A concise single-line format avoids overwhelming the output.
- [Unit specials vs model specials overlap] → `unit_specials` is already the stacked union across all models. Display it once at the unit level; `model_specials` at the model level. No deduplication needed.

## Open Questions

None — all required data is available in the resolved `Army` object.
