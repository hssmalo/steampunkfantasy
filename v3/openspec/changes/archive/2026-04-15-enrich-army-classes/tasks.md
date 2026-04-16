## 1. Schema: Rename Stacker.append → Stacker.extend

- [x] 1.1 Rename `append` field to `extend` in `Stacker` class in `src/spf/schemas/race.py`
- [x] 1.2 Verify no valid TOML race files reference `append` in a Stacker context (run `uv run spf race list` to confirm valid races load cleanly)

## 2. Build-time layer: Create armies/build.py

- [x] 2.1 Create `src/spf/armies/build.py` with `ArmyModel` dataclass (name, config: ModelConfig, upgrades: tuple[str, ...]) and `ArmyModel.upgrade(equipment_name, race_config) -> ArmyModel` method (logic from current `upgrade_model` free function)
- [x] 2.2 Add `ArmyUnit` dataclass (name, config: UnitConfig, models: tuple[ArmyModel, ...]) with `ArmyUnit.upgrade_model(model_key, equipment_name, race_config) -> ArmyUnit` and `ArmyUnit.upgrade_unit(model_key, upgrade_model_name, race_config) -> ArmyUnit` methods
- [x] 2.3 Add `ArmyList` dataclass (race, nick, units: tuple[ArmyUnit, ...]) with `add_unit`, `upgrade_unit`, `upgrade_model` methods (logic from current free functions in `army.py`) and a `resolve(race_config) -> Army` stub (implement after resolved layer exists)
- [x] 2.4 Move `_resolve_unit`, `_resolve_model`, `_make_default_team_unit`, `_make_default_team_model` helpers into `build.py`
- [x] 2.5 Move slot/requirement helpers (`_remaining_slots`, `_unsatisfied_groups`, `_satisfies_requires`, `_format_failed_group`) into `build.py` (still needed for build-time validation)
- [x] 2.6 Move `available_models`, `available_equipment`, `validate_army` into `build.py` as module-level functions (they still take `ArmyList`/`ArmyUnit`/`ArmyModel` and `race_config`)

## 3. Resolved layer: Model

- [x] 3.1 Rewrite `src/spf/armies/model.py` — replace `ArmyModel` with resolved `Model` dataclass: `name: str`, `config: ModelConfig`, `default_equipment: tuple[EquipmentConfig, ...]`, `upgrade_equipment: tuple[EquipmentConfig, ...]`
- [x] 3.2 Add `Model.equipment` property (Rule A: return `upgrade_equipment` if non-empty, else `default_equipment`)
- [x] 3.3 Add `Model.unit_specials` property (merge `config.unit_special` then each `equip.unit_special` in equipment order)
- [x] 3.4 Add `Model.model_specials` property (merge `config.special` then each `equip.model_special` in equipment order)
- [x] 3.5 Add `Model.cost()` method (sum `equip.cost` for all `upgrade_equipment`)
- [x] 3.6 Add `Model.assault()` method: start from `config.assault`, apply each `EquipmentAssaultConfig` in `equipment` order using Stacker semantics (`add` for int/Angles[int] element-wise, `replace` for any type, `extend` for lists). Merge `assault.special` dicts. Raise `ValueError` with equipment name for: `add`/`extend` on `Die`/`DieResult` fields; `add` on `ap` when current value is `"N/A"`

## 4. Resolved layer: Unit

- [x] 4.1 Rewrite `src/spf/armies/unit.py` — replace `ArmyUnit` with resolved `Unit` dataclass: `name: str`, `config: UnitConfig`, `models: tuple[Model, ...]`
- [x] 4.2 Add `Unit.unit_specials` property (merge `config.special` then each `model.unit_specials` in model order)
- [x] 4.3 Add `Unit.cost()` method: base `config.cost` + upgrade model costs + equipment costs with `upgrade_all` logic (multiply by `len(models)` when `upgrade_all is False`, flat otherwise)

## 5. Resolved layer: Army + ArmyList.resolve()

- [x] 5.1 Rewrite `src/spf/armies/army.py` — replace `Army` with resolved `Army` dataclass: `race: RaceName`, `nick: str`, `units: tuple[Unit, ...]`
- [x] 5.2 Add `Army.cost()` method (`sum(unit.cost() for unit in units, Cost())`)
- [x] 5.3 Implement `ArmyList.resolve(race_config) -> Army` in `build.py`: for each `ArmyUnit` → `Unit`, for each `ArmyModel` → `Model` (resolving `default_equipment` from `config.equipment` names and `upgrade_equipment` from `upgrades` names via `race_config.equipment`)

## 6. Update IO layer

- [x] 6.1 Update `src/spf/armies/io.py`: `load_army()` builds `ArmyList` (using helpers from `build.py`), calls `.resolve(race_config)`, returns resolved `Army`. Update return type annotation.
- [x] 6.2 Update `save_army()` to accept `ArmyList` (build-time type). Serialization format unchanged (names only).
- [x] 6.3 Update `print_army()` to use resolved `Army`: call `unit.cost().to_points()` and `army.cost()` instead of free functions; use `model.equipment` for equipment display

## 7. Update __init__.py and CLI

- [x] 7.1 Rewrite `src/spf/armies/__init__.py`: export `Army`, `Unit`, `Model`, `ArmyList`, `available_models`, `available_equipment`, `validate_army`. Do NOT export `ArmyUnit`, `ArmyModel`.
- [x] 7.2 Update `src/spf/frontends/cli/army.py`: `show_army()` no longer needs `cfg = races.get_race(army.race)` for `print_army` (army is now self-contained); `list_armies()` loads without validate, still passes through unchanged
- [x] 7.3 Remove old free functions from `army.py` (`add_unit`, `upgrade_unit`, `upgrade_model`, `available_models`, `available_equipment`, `total_cost`, `validate_army`) now that they are methods or moved to `build.py`
- [x] 7.4 Remove old free functions from `unit.py` (`unit_cost`, `_make_default_team_unit`, `_make_default_team_model`) now that they are moved to `build.py` or replaced by `Unit.cost()`

## 8. Tests and quality checks

- [x] 8.1 Update or replace existing tests for `ArmyModel`/`ArmyUnit`/`Army` to cover the new `Model`/`Unit`/`Army` resolved types
- [x] 8.2 Add tests for `Model.equipment` property (Rule A: defaults discarded when upgrades present)
- [x] 8.3 Add tests for `Model.unit_specials` and `Model.model_specials` (stacking order, key override)
- [x] 8.4 Add tests for `Model.assault()`: Stacker `add` (scalar int, element-wise Angles), `replace`, `extend`; error cases (add on Die/DieResult, add on ap="N/A")
- [x] 8.5 Add tests for `Unit.cost()` covering `upgrade_all=True`, `upgrade_all=False` (×unit size), and base cost
- [x] 8.6 Add tests for `ArmyList.resolve()` (equipment resolved, structure preserved)
- [x] 8.7 Run `uv run pytest` — all tests pass
- [x] 8.8 Run `uv run ruff check src/` and `uv run ruff format src/` — no issues
- [x] 8.9 Run `uv run pyright` — no type errors
- [x] 8.10 Run `uv run typos` — no spelling issues
