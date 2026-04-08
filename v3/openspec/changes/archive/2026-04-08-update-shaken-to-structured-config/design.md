## Context

The `ShakenConfig` Pydantic model already exists and `UnitConfig.shaken` is already typed as `ShakenConfig | None`. The TOML race files still have `shaken = "<plain string>"` which will now fail validation. This change migrates four TOML files to match the schema.

## Goals / Non-Goals

**Goals:**
- Convert all `shaken = "<string>"` values in unit sections of abomination, goblin, ogre, and ork TOML files to `[units.<id>.shaken]` structured sections
- Remove empty `shaken = ""` entries entirely
- Preserve the semantic content of each string in the structured fields

**Non-Goals:**
- Updating legacy-format race files (dwarf, elf, darkelf, gnome, general)
- Changing any Python code

## Decisions

### Parse strings into structured fields using these rules

Given the source strings, apply this mapping:

| String content | Structured field |
|---|---|
| "Movement/Speed set to `<speed>`" | `speed = "<speed>"` |
| "Movement order: `[a,b,c]`" | `movement_order = ["a", "b", "c"]` |
| "May not fire weapons" / "may not use fire orders" / "cannot use weapons" | omit `fire_order` (default `"Can't use weapons"` applies) |
| "you may use fire orders" | `fire_order = "Normal"` |
| No speed mentioned | infer from unit type: biological → `"slow"`, mechanical → `"still"` |
| No movement mentioned | infer from unit type: biological → `["-", "-", "flee"]`, mechanical → `["-", "-", "-"]` |
| Any remaining text not covered above | `comment = "<remaining text>"` |

**Rationale**: `speed` and `movement_order` are required fields — every `[units.<id>.shaken]` section must include both. The only optional field is `fire_order`, which defaults to `"Can't use weapons"` and can be omitted when fire is not allowed.

### TOML format: use `[units.<id>.shaken]` section (not inline table)

The structured shaken config spans multiple fields. A named section is more readable than an inline table and consistent with other nested configs in these files.

### ork.toml empty strings: convert to structured section with inferred defaults

`shaken = ""` means the shaken behavior wasn't documented, but the unit does have shaken rules. Convert to a `[units.<id>.shaken]` section with `speed` and `movement_order` inferred from unit type (biological or mechanical). Do not remove.

## Risks / Trade-offs

- **Parsing ambiguity**: Some strings don't follow a strict format (e.g., `"Movement order: [- - -]."` uses spaces instead of commas). These are handled case-by-case during migration.
- **Under-specified strings**: `ogre.toml` has `shaken = "May not fire weapons"` with no speed or movement (broadside_wagon, artillery_wagon), and `ork.toml` has `"Speed set to still, cannot use weapons"` with no movement (ork_char_b1). Since `speed` and `movement_order` are required, these must be inferred from unit type (mechanical in all three cases).

## Migration Plan

1. Edit each TOML file unit by unit, replacing the string with a structured section
2. Run `uv run spf race show <race>` for each race to verify validation passes
3. Run `uv run pytest` to confirm no regressions
