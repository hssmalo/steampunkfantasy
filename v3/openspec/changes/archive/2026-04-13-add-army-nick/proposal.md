## Why

Armies have no human-friendly identifier beyond their race. A nickname lets players refer to their army by a memorable name (e.g., "The Iron Claws") without affecting any game rules or calculations.

## What Changes

- Add a required `nick` field to the `Army` dataclass in `src/spf/armies/data.py`
- Persist `nick` to/from JSON army files (missing key on load is an error)
- Display the nickname in the `spf army show` rule header
- Update `armies/demo.json` with a sample nickname

## Capabilities

### New Capabilities

<!-- None: this is a pure data-field extension, no new capability areas are introduced -->

### Modified Capabilities

- `army-io`: Army serialization/deserialization must read and write the required `nick` field
- `army-display`: The army header shown by `print_army` must include the nickname

## Impact

- `src/spf/armies/data.py`: `Army` dataclass gains a required `nick: str` field (no default)
- `src/spf/armies/io.py`: `save_army` writes `nick`; `load_army` reads `nick` (errors if missing); `print_army` shows `nick` in the rule header
- `armies/demo.json`: Updated with a `nick` value
- All existing call sites constructing `Army` must supply `nick`

## Non-goals

- Enforcing uniqueness or length limits on the nickname
- Migrating other existing army JSON files (only `demo.json` is updated)
