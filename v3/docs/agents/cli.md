# The `spf` CLI

The `spf` CLI reads race definitions from TOML files in `races/` and
validates/displays them. Use it to inspect units, models, and equipment.

> **Note:** Not all TOML files in `races/` are valid — some still use a legacy
> format. Run `uv run spf race list` to get the list of currently valid TOML
> files.

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
