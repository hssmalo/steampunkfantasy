## Why

Army compositions are currently ephemeral — created in memory and lost when the session ends. Users need a way to persist armies to disk and reload them, enabling workflows where armies are saved between sessions and shared with others.

## What Changes

- Add JSON serialization/deserialization for `Army` objects
- Add `save_army(army, path)` and `load_army(path)` functions
- Add `armies_path` to the application config (defaults to `{project_path}/armies/`)
- Add `rich`-based pretty-printing for armies to the CLI
- Add `rich` as a project dependency

## Capabilities

### New Capabilities
- `army-io`: Save and load armies to/from JSON files on disk
- `army-display`: Pretty-print armies to the console using the `rich` library

### Modified Capabilities
<!-- No existing spec-level requirements are changing -->

## Impact

- **Code**: `Army` model gains serialization methods; new IO module added; config extended with `armies_path`
- **Dependencies**: `rich` added as a runtime dependency
- **CLI**: New or updated commands to save, load, and display armies
- **Non-goals**: No cloud sync, no binary/other serialization formats, no import from external tools
