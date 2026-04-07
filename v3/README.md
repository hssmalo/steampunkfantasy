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
