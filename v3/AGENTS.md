# Agent Guidance

**SteamPunkFantasy (spf)** is a tabletop hex-based wargame army management tool. It reads information about races from TOML files in `races/` and validates/displays them.

> **Note:** Not all TOML files in races are valid, some still use a legacy format. Run `uv run spf race list` to get a list of the currently valid TOML files.

## Commands

The `spf` CLI can be used to inspect units, models, and equipment in the TOML files.

```console
uv run spf --help
uv run spf race show goblin  # Validates TOML file, here races/goblin.toml

# List all things (units, models, equipment)
uv run spf race things goblin

# See all details for a given unit, model, or equipment
uv run spf race show goblin units.goblin_infantry
uv run spf race show goblin models.goblin_infantry
uv run spf race show goblin equipment.goblin_bow
```

The project uses uv and Python 3.13+. Quality gates (Pytest, Ruff, Pyright, and Typos) are
run through [`just`](https://github.com/casey/just). Prefer the `just` recipes over the
underlying commands:

```console
just            # Run all quality gates (same as `just check`)
just check      # fmt-check, lint, typecheck, spell, test — stops on first failure

just fmt        # Auto-format with ruff
just fmt-check  # Check formatting without writing changes
just lint       # Lint with ruff
just typecheck  # Type-check with pyright
just spell      # Spell-check with typos
just test       # Run the test suite (accepts extra pytest args, e.g. `just test -k foo`)
just fix        # Auto-fix lint issues, then reformat
just validate   # Validate all the TOML files via the spf CLI
```

Run `just check` before committing. The underlying tools (`uv run pytest`, `uv run ruff`,
`uv run pyright`, `uv run typos`) can still be invoked directly when needed.
