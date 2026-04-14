## Why

The `spf race` command currently only provides `list` (overview of all races) and `show` (full dump of a race). There is no quick way to browse just the units, models, or equipment for a given race — and no human-readable cost representation. Adding focused subcommands and a consistent cost format makes army planning faster.

## What Changes

- Add `spf race units <race>` — lists all units for the race with name and cost
- Add `spf race models <race>` — lists all models for the race with name and cost
- Add `spf race equipment <race>` — lists all equipment for the race with name and cost
- Add `spf race things <race>` — combined view: units, models, and equipment in one output
- Add `Cost.__str__()` returning `"{mp:2d}mp {cp:2d}cp {xp:2d}xp {ip:2d}ip"` for consistent display

## Capabilities

### New Capabilities

- `race-list-subcommands`: Four new `spf race` subcommands (`units`, `models`, `equipment`, `things`) and a `__str__` method on `Cost`

### Modified Capabilities

<!-- No existing spec-level requirements are changing -->

## Impact

- `src/spf/frontends/cli/race.py` — new command functions registered with `add_commands`
- `src/spf/schemas/type_aliases.py` — `Cost.__str__()` added
- No new dependencies; no breaking changes to existing commands

## Non-goals

- Filtering or sorting items by cost or name
- Displaying full unit/model/equipment details (that remains the job of `show`)
- Modifying the TOML schema or validation logic
