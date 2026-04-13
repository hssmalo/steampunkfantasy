## 1. Core Data Functions

- [x] 1.1 Add `unit_cost(unit: ArmyUnit, race_config: RaceConfig) -> t.Cost` to `src/spf/armies/data.py`, accumulating unit base cost + upgrade model costs + upgrade equipment costs
- [x] 1.2 Add `unit_points(unit: ArmyUnit, race_config: RaceConfig) -> int` to `src/spf/armies/data.py` implementing `mp + cp + xp + 3 * ip`
- [x] 1.3 Refactor `total_cost` to delegate to `unit_cost` per unit to eliminate duplication

## 2. Army Display

- [x] 2.1 Import `unit_points` in `src/spf/armies/io.py`
- [x] 2.2 Update `print_army()` to append ` (N pts)` after each unit name in the bullet line

## 3. Quality Checks

- [x] 3.1 Run `uv run pytest` and confirm all tests pass
- [x] 3.2 Run `uv run ruff check src/` and fix any lint errors
- [x] 3.3 Run `uv run ruff format src/` and confirm formatting
- [x] 3.4 Run `uv run pyright` and confirm no type errors
- [x] 3.5 Run `uv run typos` and confirm no spelling issues
