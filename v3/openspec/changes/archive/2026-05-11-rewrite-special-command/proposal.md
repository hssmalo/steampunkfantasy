## Why

The `special show` command is a prototype with a hardcoded race list, no type safety on the `special_key` argument, and inconsistent output formatting including a formatting bug. Replacing it properly makes the command discoverable (cyclopts can enumerate valid keys) and statically verifiable.

## What Changes

- Replace hardcoded `possible_races` list with `races.list_races()`, skipping invalid TOML files via `pydantic.ValidationError`
- Change `special_key` parameter from `str` to `UnitSpecial | ModelSpecial | AssaultSpecial` so cyclopts shows all ~60 valid choices
- Add `TypeIs`-based type guard functions (`is_unit_special`, `is_model_special`, `is_assault_special`) for pyright-clean dict lookups
- Extract `_collect_matches()` helper that returns `(label, value)` pairs for a race
- Display race display name (from `race.races[race_name].name`) instead of raw key
- Print race header only when there are matches; skip races with no hits entirely
- Fix formatting bug on equipment line (format spec was inside the string literal)
- Remove `# To Do` comments

## Non-goals

- Moving the type guard functions to `type_aliases.py` (can be done later if needed)
- Changing the schema or adding new special types
- Adding tests for the CLI output format

## Capabilities

### New Capabilities

- `special-lookup`: Cross-race lookup of units, models, and equipment by special rule key, with proper typing and formatted output

### Modified Capabilities

_(none — no existing spec-level behavior changes)_

## Impact

- `src/spf/frontends/cli/special.py` — full rewrite
- No changes to schemas, data files, or other CLI modules
