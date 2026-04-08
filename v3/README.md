# SteamPunkFantasy

Use [`uv`](https://docs.astral.sh/uv/getting-started/installation/) for Python management.

## Command line interface

Run the `spf` command line interface (CLI):

```console
uv run spf --help
```

## Show and Validate a Race File

```console
uv run spf show-race goblin
```

You can also filter down to specific units, models, or equipments:

```console
uv run spf show-race goblin units.goblin_infantry
uv run spf show-race goblin models.goblin_infantry
uv run spf show-race goblin equipments.goblin_bow
```

## List and Show Army Files

Armies are teams created from a race. List all armies:

```console
uv run spf army list
```

Show the units, models, and equipment in a given army:

```console
uv run spf army show demo
```

# Development

There is a prompt available to update TOML files. You can ask your coding assistant:

> Follow the instructions in @MIGRATE_TOML.md to update @races/elf.toml
