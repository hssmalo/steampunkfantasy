## 1. Refactor: armies package

- [x] 1.1 Create `src/spf/armies/` directory with an empty `__init__.py`
- [x] 1.2 Move `src/spf/armies.py` to `src/spf/armies/data.py` (adjust its internal imports if needed)
- [x] 1.3 Update all imports of `spf.armies` in `src/` and `tests/` to import directly from `spf.armies.data`
- [x] 1.4 Delete the now-replaced `src/spf/armies.py`

## 2. Dependencies and Config

- [x] 2.1 Add `rich` as a runtime dependency in `pyproject.toml`
- [x] 2.2 Add `armies: Path` field to `PathsConfig` in `src/spf/schemas/config.py`
- [x] 2.3 Add `armies` entry to `configs/spf.toml` pointing to `{project_path}/armies`

## 3. Army IO Module

- [x] 3.1 Create `src/spf/armies/io.py` with `save_army(army: Army, army_name: str) -> None`
- [x] 3.2 Derive save path as `config.paths.armies / f"{army_name}.json"` inside `save_army`
- [x] 3.3 Implement JSON serialization (race, unit names, model names, upgrades only — no config objects)
- [x] 3.4 Ensure `save_army` creates `config.paths.armies` if it doesn't exist
- [x] 3.5 Implement `load_army(army_name: str) -> Army` deriving path as `config.paths.armies / f"{army_name}.json"`
- [x] 3.6 Rehydrate config objects from race TOML via `get_race()` in `load_army`
- [x] 3.7 Add validation call after loading: run `validate_team()` and raise on errors

## 4. Army Display Module

- [x] 4.1 Create `src/spf/display.py` with `print_army(army: Army, race_config: RaceConfig) -> None`
- [x] 4.2 Render race name as a title using `rich`
- [x] 4.3 Render each unit as a `rich` table with columns for model name and equipment upgrades
- [x] 4.4 Render total cost (MP/CP/XP/IP) using `armies.total_cost()`

## 5. CLI Commands

- [x] 5.1 Add `show-army` command to `src/spf/frontends/cli/main.py` that loads and displays an army from the armies path
- [x] 5.2 Handle missing file with a user-friendly error message and non-zero exit

## 6. Tests

- [x] 6.1 Write tests for `save_army` / `load_army` round-trip in `tests/armies/test_io.py`
- [x] 6.2 Write tests for unknown race and missing file error paths
- [x] 6.3 Write tests for `print_army` output (at minimum assert it doesn't crash)

## 7. Quality Checks

- [x] 7.1 Run `uv run ruff format src/ tests/`
- [x] 7.2 Run `uv run ruff check src/ tests/`
- [x] 7.3 Run `uv run pyright`
- [x] 7.4 Run `uv run pytest`
- [x] 7.5 Run `uv run typos`
