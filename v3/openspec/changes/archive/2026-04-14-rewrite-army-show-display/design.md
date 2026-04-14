## Context

`print_army` in `src/spf/armies/io.py` currently uses `rich.table.Table` to render units and their models. Other display commands (e.g. `list_things` in `src/spf/frontends/cli/race.py`) use plain f-string bullet lists printed via `stdout.print`. The goal is to unify the visual style.

The existing `Cost.__str__()` method (in `src/spf/schemas/type_aliases.py`) already formats cost with grayed-out zeros — the current `print_army` duplicates this logic manually.

## Goals / Non-Goals

**Goals:**
- Rewrite `print_army` to use f-string bullet lists matching the style of `list_things`
- Remove the `rich.table.Table` import from `io.py`
- Use `Cost.__str__()` for the total cost line

**Non-Goals:**
- Changing command signatures, army data structures, or any other function in `io.py`
- Per-unit or per-model cost breakdown in the output

## Decisions

**Use `stdout.print` with f-strings (not rich renderables)**
`race.py` already establishes this pattern — `[bold]` markup in plain strings, bullet lists with `-` and `  -` indentation. Staying consistent avoids introducing a second visual vocabulary.

**Keep the header rule for army name/race**
`stdout.rule(...)` provides clear visual separation between the army identity and the unit list. It matches the intent of the original table title rows and shouldn't be dropped, only the per-unit table titles change.

**Equipment listed inline in parentheses**
Default equipment (from `model.config.equipment`) and upgrades (from `model.upgrades`) are joined with `, ` and wrapped in `(...)` on the same line as the model name. If a model has no equipment at all the parentheses are omitted.

## Risks / Trade-offs

- [Long equipment lists] → No wrapping is applied; long lines may overflow narrow terminals. Acceptable for now — same limitation exists in race commands.
- [Removing rich Table] → No regression risk; `Table` is not used anywhere else in `io.py`.
