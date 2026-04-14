## Why

`spf army show` renders army data using rich `Table` objects, which is visually inconsistent with other display commands (e.g. `spf race things ork`) that use plain f-string bullet lists. Aligning the output style makes the CLI feel cohesive and predictable.

## What Changes

- Replace the rich `Table`-based rendering in `print_army` with a plain f-string bullet list format
- Army name displayed in bold at the top (matching the section headers in `spf race things`)
- Each unit is a top-level bullet point; each model is a sub-bullet with equipment in parentheses
- Total cost line uses the existing `Cost.__str__()` method instead of manual field interpolation

## Capabilities

### New Capabilities
<!-- None: this is a pure restyle of an existing capability -->

### Modified Capabilities
- `army-display`: The rendered format of `spf army show` changes from rich tables to a plain f-string list

## Impact

- `src/spf/armies/io.py` — `print_army` function rewritten; `rich.table.Table` import removed
- No changes to data structures, CLI command signatures, or other commands

## Non-goals

- Changing any other army commands (`list`, builder commands)
- Changing how race commands display data
- Adding new information to the army display (costs per unit/model, etc.)
