## Why

The `shaken` field on `UnitConfig` has been migrated from a plain string to a structured `ShakenConfig` type in the Python schema. The TOML data files for abomination, goblin, ogre, and ork races still use the old string format and need to be updated to match.

## What Changes

- Convert `shaken = "<string>"` entries in `units.*` sections of `abomination.toml`, `goblin.toml`, `ogre.toml`, and `ork.toml` to structured `[units.<id>.shaken]` sections
- Remove `shaken = ""` entries (empty strings) entirely — these units have no shaken config
- Omit `fire_order` from structured config when the string says fire orders can't be used or doesn't mention them (the default `"Don't use"` applies)
- Omit `speed` when it defaults to `"still"`
- Preserve any non-default movement orders explicitly

## Capabilities

### New Capabilities
<!-- None — this is a pure data migration -->

### Modified Capabilities
<!-- None — the Python schema (`ShakenConfig`) is already updated; this change only migrates data files to match -->

## Impact

- `races/abomination.toml`, `races/goblin.toml`, `races/ogre.toml`, `races/ork.toml` — data changes only
- No Python code changes needed (schema already updated)
- Running `uv run spf show-race <race>` will fail until TOML files are migrated

## Non-goals

- Updating legacy-format race files (dwarf, elf, darkelf, gnome, general)
- Changing any game rules or unit stats
- Modifying the Python schema (already done)
