## Context

The `Army` dataclass in `src/spf/armies/data.py` represents a player's assembled force. It currently holds a race name and a tuple of units. Army JSON files are saved/loaded via `src/spf/armies/io.py`, which also provides `print_army` for rich console display. There is no way to give an army a human-friendly name.

## Goals / Non-Goals

**Goals:**
- Add a required `nick: str` field to `Army` — every army must have a nickname
- Persist `nick` through the JSON round-trip (save → load preserves the nickname)
- Show `nick` in the `spf army show` rule header alongside the race name

**Non-Goals:**
- Enforcing uniqueness, length limits, or character restrictions on the nickname
- Migrating all existing army JSON files (only `demo.json` is updated)

## Decisions

**Required field, no default**

`Army` is a frozen dataclass. `nick: str` is declared without a default, making it a required keyword argument. This ensures every `Army` object always has an explicit nickname — callers cannot accidentally omit it. All existing construction sites (primarily tests and `load_army`) must be updated to pass `nick`.

Alternative considered: `nick: str = ""`. Rejected per user requirement to enforce the field explicitly, preventing silent omissions.

**Serialization: always write `nick`, error on missing key at load**

`save_army` always emits `"nick"` in the JSON. `load_army` reads `data["nick"]` (direct key access, not `.get()`), so loading a JSON file without a `nick` key raises a `KeyError`. This enforces the contract: any valid army file must carry a nickname. The one existing file (`demo.json`) is updated as part of this change.

**Display: nick in the rule header**

`print_army` currently renders `stdout.rule(f"{cfg.races[army.race].name} Army")`. It will be updated to `stdout.rule(f"{army.nick} — {cfg.races[army.race].name} Army")` so the nickname appears prominently at the top of the output.

## Risks / Trade-offs

- All `Army(...)` construction sites must be updated. The field has no default, so missing it is a `TypeError` at runtime — this is intentional (fail loudly).
- Existing army JSON files without `"nick"` will fail to load with a `KeyError`. Acceptable because only `demo.json` exists and it is updated in this change.
