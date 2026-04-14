## 1. Update validation helper in data.py

- [x] 1.1 Replace `_satisfies_requires` with a new helper `_unsatisfied_groups` that returns the list of OR-groups (list of `Requirement` lists) that failed, instead of a boolean
- [x] 1.2 Update `validate_army` to call `_unsatisfied_groups` and, when the result is non-empty, format each failing group into a human-readable string with slot counts included for holder requirements
- [x] 1.3 Update `upgrade_model` (public API) to use the new helper and include failure detail in its raised `ValueError`

## 2. Update tests in test_data.py

- [x] 2.1 Update existing test(s) that assert on the generic `"requires are not satisfied"` message to match the new detailed message format
- [x] 2.2 Add a test: type-only failing group shows the type alternatives (e.g., `"type:Infantry or type:Grunt"`)
- [x] 2.3 Add a test: slot-count failing group shows holder name, required count, and available count (e.g., `"Hands:2 (have 0)"`)
- [x] 2.4 Add a test: when two OR-groups both fail, both are included in the error separated by `"; "`

## 3. Quality checks

- [x] 3.1 Run `uv run pytest` — all tests pass
- [x] 3.2 Run `uv run ruff check src/` and `uv run ruff format src/` — no errors
- [x] 3.3 Run `uv run pyright` — no type errors
- [x] 3.4 Run `uv run typos` — no spelling issues
- [x] 3.5 Run `uv run spf army show 2025/geir_arne` — error output shows specific failing constraints
