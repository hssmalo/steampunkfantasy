## Why

`races/ork.toml` uses the old TOML format with an outer `ork.`-prefixed namespace (e.g. `[ork.units.troll]`) and list-based unit specials, both of which are rejected by the current `RaceConfig` schema. Running `uv run spf show-race ork` raises a validation error.

## What Changes

- Remove the `ork.` prefix from all section headers (`[ork.units.*]` → `[units.*]`, etc.)
- **BREAKING**: Convert `special = [...]` lists on unit entries to TOML table dicts `[units.xxx.special]`
- Add two new `UnitSpecial` literals to the schema: `"Regeneration"` and `"Hans Sverre's second favorite rule"`
- Fix field casing: `size`, `DamageTableName`, and `ModelType` values must match schema Literals exactly
- Fix miscellaneous field errors: `psycic` → `psychic`, `equipments_limit` → `equipment_limit`, `race = "Ork"` → `race = "ork"`, missing `shaken` and `equipments` fields, invalid `ap` string values

## Capabilities

### New Capabilities

_None._

### Modified Capabilities

- `army-data-access`: Two new `UnitSpecial` enum values (`"Regeneration"`, `"Hans Sverre's second favorite rule"`) are added to the schema type to support ork-specific unit abilities.

## Impact

- `races/ork.toml` — primary file being updated
- `src/spf/schemas/type_aliases.py` — `UnitSpecial` Literal extended with two new values

## Non-goals

- Making ork a fully playable race (that requires additional work beyond validation)
- Correcting gameplay text, typos in ability descriptions, or rules interpretation
- Updating any other race TOML files
