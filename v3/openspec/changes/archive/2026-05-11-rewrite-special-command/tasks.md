## 1. Type Guards

- [x] 1.1 Add `frozenset` constants for each special category using `get_args(t.XxxSpecial.__value__)`
- [x] 1.2 Implement `is_unit_special(key: str) -> TypeIs[t.UnitSpecial]`
- [x] 1.3 Implement `is_model_special(key: str) -> TypeIs[t.ModelSpecial]`
- [x] 1.4 Implement `is_assault_special(key: str) -> TypeIs[t.AssaultSpecial]`

## 2. Match Collection

- [x] 2.1 Implement `_collect_matches(race, special_key) -> list[tuple[str, str]]`
- [x] 2.2 Add `if is_unit_special` block: search `units.special`, `models.unit_special`, `equipment.unit_special`
- [x] 2.3 Add `if is_model_special` block: search `models.special`, `equipment.model_special`
- [x] 2.4 Add `if is_assault_special` block: search `models.assault.special`, `equipment.assault.special`

## 3. Command Rewrite

- [x] 3.1 Change `special_key` parameter type to `t.UnitSpecial | t.ModelSpecial | t.AssaultSpecial`
- [x] 3.2 Replace hardcoded `possible_races` with `races.list_races()` loop, catching `pydantic.ValidationError`
- [x] 3.3 Use `race.races[race_name].name` for display name
- [x] 3.4 Call `_collect_matches()` and skip race if result is empty
- [x] 3.5 Print race header and formatted match lines (label + value)
- [x] 3.6 Remove `possible_races` list and all `# To Do` comments

## 4. Verification

- [x] 4.1 Run `uv run ruff format src/` and `uv run ruff check src/`
- [x] 4.2 Run `uv run pyright`
- [x] 4.3 Run `uv run typos`
- [x] 4.4 Run `uv run pytest`
- [x] 4.5 Smoke-test: `uv run spf special show Immunity` and confirm output groups by race with no empty headers
- [x] 4.6 Smoke-test: `uv run spf special show --help` and confirm ~60 choices are listed
