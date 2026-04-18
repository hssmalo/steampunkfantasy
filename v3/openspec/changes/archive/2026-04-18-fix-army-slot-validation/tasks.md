## 1. Fix `_remaining_slots`

- [x] 1.1 Change the iteration in `_remaining_slots` from `(*model.config.equipment, *model.upgrades)` to `model.upgrades` only
- [x] 1.2 Update or add unit tests for `_remaining_slots`: verify that default equipment is excluded from slot accounting regardless of whether upgrades are present

## 2. Fix `validate_army`

- [x] 2.1 Change the validation loop to build a partial `ArmyModel` per upgrade: for upgrade at index `j`, pass `ArmyModel(name=..., config=..., upgrades=team_model.upgrades[:j])` to `_unsatisfied_groups`
- [x] 2.2 Add or update unit tests for `validate_army`: verify a model whose upgrades exactly fill its slots passes; verify a model that truly over-fills its slots still fails

## 3. Verify `available_equipment`

- [x] 3.1 Add a test for `available_equipment` on a model with slot-consuming defaults and no current upgrades: confirm that upgrades requiring those same slots are returned as available

## 4. Integration test

- [x] 4.1 Add a test (or regression fixture) that loads `armies/2025/geir_arne.json` and asserts `validate_army` returns an empty error list

## 5. Quality checks

- [x] 5.1 Run `uv run pytest` and confirm all tests pass
- [x] 5.2 Run `uv run ruff check src/` and `uv run ruff format src/`
- [x] 5.3 Run `uv run pyright` and confirm no new type errors
- [x] 5.4 Run `uv run typos` and confirm no spelling errors
- [x] 5.5 Run `uv run spf army show 2025/geir_arne` and confirm no validation errors
