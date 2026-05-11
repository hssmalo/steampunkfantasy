## Context

`special.py` is a single-file CLI module that lets users query which units, models, and equipment across all races have a given special rule. It was written as a prototype and has three problems: hardcoded race list, untyped `special_key`, and inconsistent output formatting.

The schema defines three distinct special key types (`UnitSpecial`, `ModelSpecial`, `AssaultSpecial`) as `type X = Literal[...]` aliases (Python 3.12 `TypeAliasType`). These map to different fields on different schema objects.

## Goals / Non-Goals

**Goals:**
- `special_key` validated and enumerated by cyclopts at the CLI layer
- Pyright-clean dict lookups without casts
- Race list driven by filesystem, invalid TOMLs silently skipped
- Output grouped by race, race omitted when no matches

**Non-Goals:**
- Relocating type guards to `type_aliases.py`
- Adding new special types or schema changes
- CLI tests for output format

## Decisions

### 1. `special_key` type: `UnitSpecial | ModelSpecial | AssaultSpecial`

Cyclopts resolves a union of `Literal`-backed `TypeAliasType` aliases to a flat list of choices (verified). The ~60 values appear in `--help` as `[choices: ...]`. This makes all valid keys discoverable without any extra cyclopts configuration.

**Alternative considered:** Keep `str` and validate manually inside the function — loses cyclopts enumeration and shifts the error from argument parsing to runtime.

### 2. Type narrowing via `TypeIs`

`get_args(t.UnitSpecial)` returns `()` on a `TypeAliasType` — `.__value__` is required:

```python
_UNIT_SPECIALS = frozenset(get_args(t.UnitSpecial.__value__))

def is_unit_special(key: str) -> TypeIs[t.UnitSpecial]:
    return key in _UNIT_SPECIALS
```

Within `if is_unit_special(special_key):`, pyright narrows `special_key` to `UnitSpecial`, making lookups into `dict[UnitSpecial, str]` type-safe with no casts.

Three separate `if` blocks (not `elif`) because "Fog" appears in both `UnitSpecial` and `ModelSpecial` — `elif` would silently miss the second match category.

**Alternative considered:** `cast()` at each dict lookup — works at runtime but loses static safety and is verbose.

### 3. Match collection extracted to `_collect_matches()`

Returns `list[tuple[str, str]]` — `(label, value)` pairs. Separation makes the per-race loop readable: collect, skip if empty, then print.

Label format: `"Unit:      <name>"`, `"Model:     <name>"`, `"Equipment: <name>"` — left-aligned prefix, name in a fixed-width field.

### 4. Race enumeration

`races.list_races()` reads from the filesystem. Each race is loaded with `races.get_race()`; `pydantic.ValidationError` is caught and the race skipped (matching the pattern in `race.py`'s `list_races()`). Display name comes from `race.races[race_name].name`.

## Risks / Trade-offs

- **`.__value__` is an implementation detail of `TypeAliasType`**: If Python changes how `TypeAliasType` works, the frozenset construction breaks. Mitigation: this is internal to `special.py` and easy to fix if it ever changes; the alternative is manually duplicating the string sets.
- **~60 choices in `--help`**: Long but still useful. Cyclopts wraps them; the user can pipe to grep. No mitigation needed.
- **"Fog" dual-category**: Currently handled by separate `if` blocks. If future specials also span categories, the same pattern holds automatically.
