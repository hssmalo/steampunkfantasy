## 1. Implement convenience methods

- [x] 1.1 Implement `.upgrade_full_unit()` in `src/spf/armies/build.py` (loop through model slots, call existing `.upgrade_unit()`)
- [x] 1.2 Implement `.upgrade_all_models()` in `src/spf/armies/build.py` (validate all models first, then apply)
- [x] 1.3 Implement `.duplicate_unit()` in `src/spf/armies/build.py` (find unit, append copy)
- [x] 1.4 Implement `.delete_unit()` in `src/spf/armies/build.py` (find unit, remove from tuple)

## 2. Add docstrings and type hints

- [x] 2.1 Add docstrings to all four methods explaining parameters, return value, and error conditions
- [x] 2.2 Verify type hints are correct (should use existing patterns in the file)

## 3. Write unit tests

- [x] 3.1 Write tests for `.upgrade_full_unit()` (success case, all models upgraded, failure cases)
- [x] 3.2 Write tests for `.upgrade_all_models()` (success case, all models upgraded, failure cases)
- [x] 3.3 Write tests for `.duplicate_unit()` (copy created, independent from original, KeyError on missing unit)
- [x] 3.4 Write tests for `.delete_unit()` (unit removed, KeyError on missing unit)

## 4. Quality checks

- [x] 4.1 Run type checker: `uv run pyright`
- [x] 4.2 Run linter: `uv run ruff check src/`
- [x] 4.3 Run formatter: `uv run ruff format src/`
- [x] 4.4 Run tests: `uv run pytest tests/armies/`
- [x] 4.5 Run spell checker: `uv run typos`
