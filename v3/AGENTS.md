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

The project uses uv and Python 3.13+. Additionally, it uses Pytest, Ruff, Pyright, and Typos for testing and linting:

```
# Run tests
uv run pytest

# Lint and format
uv run ruff check src/
uv run ruff format src/

# Type checking
uv run pyright

# Spell checking
uv run typos
```
