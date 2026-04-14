## Why

When loading army JSON files, errors like unknown unit names or blank model entries surface as cryptic Python `KeyError` tracebacks instead of actionable validation messages. Users manually editing JSON files deserve clear, Pydantic-style error messages that identify exactly which unit or model is invalid and why.

## What Changes

- `_build_army` in `armies/io.py` will catch `KeyError` lookups for unknown unit/model names and raise a structured `ValueError` with a descriptive message identifying the offending entry (index + name).
- `load_army` will propagate these structured errors, or wrap them into a consolidated validation report.
- Empty string names (`""`) and other non-existent keys will produce messages like: `Unit #2 (name ''): unknown unit name. Did you mean one of: ork_boyz, ork_char_b1?`
- Model-level errors follow the same pattern: `Unit 'ork_boyz' / model #1 (name ''): unknown model name.`
- **RENAME** `validate_team` → `validate_army` in `armies/data.py`, `armies/io.py`, and tests (`team` is a legacy name).

## Capabilities

### New Capabilities
- `army-load-validation`: Structured validation errors during army JSON loading, with per-unit and per-model error messages that identify the offending entry by index and name.

### Modified Capabilities
- `army-io`: Loading requirement extended — unknown unit/model names now raise `ValueError` with descriptive messages instead of bare `KeyError`.
- `team-builder`: Rename `validate_team` → `validate_army` to align with current naming conventions.

## Impact

- `src/spf/armies/data.py` — rename `validate_team` → `validate_army`
- `src/spf/armies/io.py` — `_build_army` function; update import and call site for rename
- `src/spf/frontends/cli/army.py` — `show_army` error handling (must catch `ValueError` in addition to `FileNotFoundError`)
- `tests/armies/test_data.py` — update import and all test function names/calls
- `openspec/specs/army-io/spec.md` — delta spec for new loading scenarios
- `openspec/specs/team-builder/spec.md` — delta spec for rename
- No new dependencies required

## Non-goals

- Not adding JSON schema validation (e.g., jsonschema) — we keep it pure Python/Pydantic-free
- Not validating the JSON structure itself (missing keys, wrong types) — only name-resolution errors
- Not suggesting fuzzy-matched corrections (did-you-mean) unless trivially available from the race config
