## Context

Army JSON files are hand-edited by users and frequently contain placeholder entries (empty string names, typos, stale unit keys). The current `_build_army` function does raw `dict` lookups on `cfg.units` and `cfg.models`, which raise bare `KeyError: ''` tracebacks — giving no indication of which unit index or model slot is wrong, or what valid names exist.

The fix is contained to one function in `armies/io.py` plus a small CLI error-handling addition in `army.py`.

## Goals / Non-Goals

**Goals:**
- Replace silent `KeyError` crashes with descriptive `ValueError` messages that identify the offending entry by position (index) and value (name).
- Follow the same message style already used elsewhere in the codebase (e.g. `validate_army`).
- Catch all name-resolution failures — unknown unit name, unknown model name — in a single validation pass before constructing any `ArmyUnit` or `ArmyModel`.
- Ensure the CLI `show_army` command catches `ValueError` and prints a user-friendly error.

**Non-Goals:**
- JSON schema validation (structural errors like missing keys, wrong types).
- Fuzzy matching / "did you mean" suggestions.
- Changes to `validate_army` behavior (that runs after construction and covers rule violations).

## Decisions

### Decision: Validate-then-build, not catch-on-crash
**Chosen:** Add a `_validate_army_data` step inside `_build_army` that iterates all units/models and collects unknown-name errors before constructing objects.

**Alternative:** Wrap individual `cfg.units[...]` lookups in try/except and re-raise with context.

**Rationale:** The validate-then-build pattern mirrors `validate_army` already in the codebase and produces all errors at once rather than stopping at the first bad entry. This is the Pydantic-style behavior the user asked for.

### Decision: Raise `ValueError`, not a custom exception class
**Chosen:** Raise `ValueError` with a multi-line message listing all problems found.

**Alternative:** Introduce a custom `ArmyLoadError` exception.

**Rationale:** The existing `load_army` already raises `ValueError` for invalid armies (from `validate_army`). Keeping the same exception type avoids adding a new public API surface and stays consistent.

### Decision: Keep validation separate from `validate_army`
`validate_army` checks rule violations (wrong model replacements, equipment requirements) on a fully-constructed `Army`. Name-resolution errors happen before construction, so they belong in `_build_army`, not `validate_army`.

## Risks / Trade-offs

- [Risk] A single `ValueError` message containing many errors may be long → Mitigation: list errors bullet-by-bullet (same style as `validate_army`), each on its own line.
- [Risk] Adding a pre-pass over data duplicates iteration → Accepted: the data is tiny (dozens of units at most); performance is not a concern.
