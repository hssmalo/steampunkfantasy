## Context

`spf race` currently exposes `list` (all races overview) and `show` (full configaroo dump). The TOML schema already has `units`, `models`, and `equipments` dicts inside `RaceConfig`, and each entry has a `name` field and an optional `cost: Cost | None`. The `Cost` model lives in `src/spf/schemas/type_aliases.py`.

The CLI entry point is `src/spf/frontends/cli/race.py`; new commands are registered in `add_commands()`.

## Goals / Non-Goals

**Goals:**
- Four new subcommands: `units`, `models`, `equipment`, `things`
- Human-readable cost string via `Cost.__str__()`
- Output style consistent with the existing `list` subcommand (plain f-string lines)

**Non-Goals:**
- Filtering, sorting, or pagination
- Full detail display (use `show` for that)
- Changes to TOML validation or schema structure

## Decisions

### Cost formatting via `__str__`

Add `__str__` to `Cost` in `type_aliases.py` returning `f"{self.mp:2d}mp {self.cp:2d}cp {self.xp:2d}xp {self.ip:2d}ip"`.

**Why not a standalone helper?** A `__str__` method is the idiomatic Python place for a default string representation. It avoids a separate formatting utility and makes cost values printable naturally in f-strings across the codebase.

**Handling `cost: None`**: Units, models, and equipment can have `cost = None`. The display will fall back to a placeholder string `"  -mp   -cp   -xp   -ip"` so column alignment is preserved.

### Command structure

All four commands are plain functions registered in `add_commands()` — no sub-app nesting needed. `things` simply calls the other three display helpers in sequence (units → models → equipment) with a header between sections.

**Why helper functions rather than calling subcommands?** Cyclopts subcommands are CLI entry points, not Python callables designed for reuse. Extracting `_print_units`, `_print_models`, `_print_equipment` as module-private helpers avoids coupling `things` to CLI dispatch internals.

### Output format

Each line: `f"- {name:<24} {cost_str}"` — matches the alignment style of `list_races`. Header lines (for `things`) use `stdout.print` with markup, e.g. `[bold]Units[/]`.

## Risks / Trade-offs

- **`cost = None` display** — using a dash placeholder keeps column widths stable but looks different from `Cost.__str__`. This is acceptable since "no cost defined" is a meaningful data state.
- **`__str__` on a Pydantic model** — Pydantic's `__repr__` is customised; adding `__str__` is safe and won't affect serialisation.
