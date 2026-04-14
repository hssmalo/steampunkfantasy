## 1. Schema Update

- [x] 1.1 Remove `model_cost` field from `EquipmentConfig` in `src/spf/schemas/race.py`
- [x] 1.2 Add `upgrade_all: bool | None = None` field to `EquipmentConfig` in `src/spf/schemas/race.py`

## 2. Cost Calculation Logic

- [x] 2.1 Update `unit_cost` in `src/spf/armies/data.py` to multiply equipment `cost` by `len(unit.models)` when `upgrade_all` is `False` or `None`
- [x] 2.2 Update `unit_cost` to apply equipment `cost` exactly once when `upgrade_all` is `True`

## 3. TOML File Migration

- [x] 3.1 In `races/ork.toml`, replace `model_cost.*` with `cost.*` and add `upgrade_all = false` for affected equipment entries
- [x] 3.2 In `races/ogre.toml`, replace `model_cost.*` with `cost.*` and add `upgrade_all = false` for affected equipment entries
- [x] 3.3 In `races/elf.toml`, replace `model_cost.*` with `cost.*` and add `upgrade_all = false` for affected equipment entries

## 4. Verification

- [x] 4.1 Run `uv run pytest` and confirm all tests pass
- [x] 4.2 Run `uv run ruff check src/` and `uv run ruff format src/` and fix any issues
- [x] 4.3 Run `uv run pyright` and fix any type errors
- [x] 4.4 Run `uv run typos` and fix any spelling issues
- [x] 4.5 Run `uv run spf race show` for each valid race (abomination, elf, goblin, ogre, ork) and confirm output is correct
