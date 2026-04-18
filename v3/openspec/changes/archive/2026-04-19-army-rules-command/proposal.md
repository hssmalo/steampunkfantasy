## Why

The existing `army show` command gives a compact cost-focused overview of an army. Players also need a rules reference view that shows all combat stats, specials, and weapon profiles per unit so they can quickly look up what each unit and model can do during a game.

## What Changes

- Add `uv run spf army rules <army-name>` CLI command
- The command loads the same `Army` object as `army show` but formats it for rules reference rather than cost overview
- Display structure (per unit):
  - Top-level bullet: unit name + total cost
  - Nested sub-bullet: unit specials (if any)
  - Nested sub-bullet per model: model name + model cost
    - Model specials (if any)
    - Each equipment item with cost (if any)
    - Assault stats for the model
    - Range weapon stats for any equipment that has a range profile

## Capabilities

### New Capabilities

- `army-rules-display`: CLI command and formatter that renders a full rules-reference view of a loaded `Army`, including specials, assault profiles, and range weapon profiles for each model

### Modified Capabilities

- `army-display`: Add the `army rules` subcommand registration alongside the existing `army show` subcommand

## Non-goals

- No changes to how armies are loaded, validated, or saved
- No changes to the `army show` display format
- No new data beyond what is already in `Army` / `EquipmentConfig`

## Impact

- New display function in `spf/armies/io.py` (or a dedicated module)
- New CLI command registered in `spf/frontends/cli/army.py`
- No schema, data-access, or persistence changes
