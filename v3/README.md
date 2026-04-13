# SteamPunkFantasy

Use [`uv`](https://docs.astral.sh/uv/getting-started/installation/) for Python management.

## Command line interface

Run the `spf` command line interface (CLI):

```console
uv run spf --help
```

## Show and Validate a Race File

List all races:

```console
uv run spf race list
```

Validate and show one race:

```console
uv run spf race show goblin
```

You can also filter down to specific units, models, or equipment:

```console
uv run spf race show goblin units.goblin_infantry
uv run spf race show goblin models.goblin_infantry
uv run spf race show goblin equipment.goblin_bow
```

There are also commands for a high-level overview of a race:

```console
uv run spf race things ork
uv run spf race units ork
uv run spf race models ork
uv run spf race equipment ork
``

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
