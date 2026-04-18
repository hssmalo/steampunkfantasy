## 1. Display Function

- [x] 1.1 Add `print_army_rules(army: Army) -> None` to `src/spf/armies/io.py`
- [x] 1.2 Render header with army nick and race name using `stdout.rule`
- [x] 1.3 Render each unit as top-level bullet with name and total cost in pts
- [x] 1.4 Render unit specials as nested sub-bullet (skip when empty)
- [x] 1.5 Render each model as nested bullet with name and upgrade cost (omit cost when zero)
- [x] 1.6 Render model specials as nested sub-sub-bullet (skip when empty)
- [x] 1.7 Render each equipment item with name and cost (omit cost when absent)
- [x] 1.8 Render resolved assault profile as compact sub-sub-bullet per model
- [x] 1.9 Render range weapon stats for any equipment with a `.range` profile
- [x] 1.10 Render total army cost at the bottom

## 2. CLI Command

- [x] 2.1 Add `rules_army` function to `src/spf/frontends/cli/army.py` that loads and calls `print_army_rules`
- [x] 2.2 Register `rules_army` as `"rules"` subcommand in `add_commands`
- [x] 2.3 Handle `FileNotFoundError` / `ValueError` with error message and `SystemExit(1)`

## 3. Tests

- [x] 3.1 Add unit tests for `print_army_rules` output format (unit line, model line, specials, assault, range)
- [x] 3.2 Verify missing army file causes exit with non-zero status via CLI

## 4. Quality Checks

- [x] 4.1 Run `uv run ruff check src/` and fix any issues
- [x] 4.2 Run `uv run ruff format src/`
- [x] 4.3 Run `uv run pyright`
- [x] 4.4 Run `uv run pytest`
- [x] 4.5 Run `uv run typos`
- [x] 4.6 Smoke-test `uv run spf army rules <army-name>` with a real army file
