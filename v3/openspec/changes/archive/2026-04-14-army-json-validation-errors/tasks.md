## 1. Rename `validate_team` → `validate_army`

- [x] 1.1 Rename the function `validate_team` to `validate_army` in `src/spf/armies/data.py`
- [x] 1.2 Update the import and call site in `src/spf/armies/io.py`
- [x] 1.3 Update the import and all usages/function names in `tests/armies/test_data.py`

## 2. Validation in `_build_army`

- [x] 2.1 Add `_validate_army_data(data, cfg)` helper in `src/spf/armies/io.py` that iterates all unit entries and collects errors for unknown unit names (by index + name value)
- [x] 2.2 Extend the same helper to iterate model entries within each valid-enough unit and collect errors for unknown model names (by unit index, unit name, model index, model name value)
- [x] 2.3 Call `_validate_army_data` at the start of `_build_army`; if errors is non-empty, raise `ValueError` with a joined multi-line message

## 3. CLI error handling

- [x] 3.1 In `src/spf/frontends/cli/army.py`, extend the `show_army` try/except to also catch `ValueError` and print a red error message to stderr, then exit with code 1

## 4. Tests

- [x] 4.1 Add a test that loading an army JSON with a blank unit name (`""`) raises `ValueError` with the unit index in the message
- [x] 4.2 Add a test that loading an army JSON with a blank model name raises `ValueError` with the unit and model index in the message
- [x] 4.3 Add a test that multiple bad entries produce a single `ValueError` listing all of them
- [x] 4.4 Verify existing `load_army` tests still pass (round-trip, missing file, unknown race)

## 5. Quality checks

- [x] 5.1 Run `uv run pytest`
- [x] 5.2 Run `uv run ruff check src/` and `uv run ruff format src/`
- [x] 5.3 Run `uv run pyright`
- [x] 5.4 Run `uv run typos`
- [x] 5.5 Manually verify `uv run spf army show 2025/geir_arne` prints a clean error instead of a traceback
