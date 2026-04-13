## 1. Cost string representation

- [x] 1.1 Add `__str__` to `Cost` in `src/spf/schemas/type_aliases.py` returning `f"{self.mp:2d}mp {self.cp:2d}cp {self.xp:2d}xp {self.ip:2d}ip"`

## 2. CLI subcommands

- [x] 2.1 Add private helper `_cost_str(cost: t.Cost | None) -> str` in `src/spf/frontends/cli/race.py` that returns `str(cost)` or the dash placeholder `"  -mp   -cp   -xp   -ip"` when cost is None
- [x] 2.2 Add `_print_units(race_config)` helper that prints one line per unit using `f"- {unit.name:<24} {_cost_str(unit.cost)}"`
- [x] 2.3 Add `_print_models(race_config)` helper that prints one line per model using the same format
- [x] 2.4 Add `_print_equipment(race_config)` helper that prints one line per equipment item using the same format
- [x] 2.5 Add `list_units(race_name)` command function that loads the race and calls `_print_units`
- [x] 2.6 Add `list_models(race_name)` command function that loads the race and calls `_print_models`
- [x] 2.7 Add `list_equipment(race_name)` command function that loads the race and calls `_print_equipment`
- [x] 2.8 Add `list_things(race_name)` command function that loads the race and calls all three print helpers with `[bold]Units[/]`, `[bold]Models[/]`, `[bold]Equipment[/]` section headers
- [x] 2.9 Register all four commands in `add_commands()` with names `"units"`, `"models"`, `"equipment"`, `"things"`

## 3. Quality checks

- [x] 3.1 Run `uv run pytest` and confirm all tests pass
- [x] 3.2 Run `uv run ruff check src/` and fix any lint issues
- [x] 3.3 Run `uv run ruff format src/` and apply formatting
- [x] 3.4 Run `uv run pyright` and resolve any type errors
- [x] 3.5 Run `uv run typos` and fix any spelling issues
- [x] 3.6 Smoke-test `uv run spf race units goblin`, `uv run spf race models goblin`, `uv run spf race equipment goblin`, and `uv run spf race things goblin`
