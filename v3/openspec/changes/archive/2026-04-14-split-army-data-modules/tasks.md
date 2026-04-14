## 1. Create New Module Files

- [x] 1.1 Create `src/spf/armies/model.py` with `ArmyModel` dataclass and all model-level private helpers (`_remaining_slots`, `_satisfies_requirement`, `_unsatisfied_groups`, `_format_failed_group`, `_satisfies_requires`, `_resolve_model`) and public functions (`available_equipment`, `upgrade_model`)
- [x] 1.2 Create `src/spf/armies/unit.py` with `ArmyUnit` dataclass and unit-level private helpers (`_make_default_team_model`, `_make_default_team_unit`, `_resolve_unit`) and public functions (`available_models`, `upgrade_unit`, `unit_cost`, `unit_points`); import from `model.py`
- [x] 1.3 Create `src/spf/armies/army.py` with `Army` dataclass and army-level public functions (`add_unit`, `total_cost`, `validate_army`); import from `unit.py` and `model.py`

## 2. Update Package Root

- [x] 2.1 Update `src/spf/armies/__init__.py` to re-export all public names (`ArmyModel`, `ArmyUnit`, `Army`, `add_unit`, `upgrade_unit`, `upgrade_model`, `available_models`, `available_equipment`, `unit_cost`, `unit_points`, `total_cost`, `validate_army`) from the new modules

## 3. Update Internal Imports

- [x] 3.1 Update `src/spf/armies/io.py` to import from the new modules (or from `spf.armies`) instead of `spf.armies.data`
- [x] 3.2 Delete `src/spf/armies/data.py`

## 4. Update Tests

- [x] 4.1 Update `tests/armies/test_data.py` imports to use `from spf.armies import …` instead of `from spf.armies.data import …`
- [x] 4.2 Update `tests/armies/test_io.py` imports to use `from spf.armies import …`
- [x] 4.3 Update `tests/test_display.py` imports to use `from spf.armies import …`

## 5. Verify

- [x] 5.1 Run `uv run pytest` and confirm all tests pass
- [x] 5.2 Run `uv run ruff check src/` and `uv run ruff format src/` with no errors
- [x] 5.3 Run `uv run pyright` with no new type errors
- [x] 5.4 Run `uv run typos` with no new spelling errors
- [x] 5.5 Run `uv run spf race show goblin` to confirm CLI still works end-to-end
