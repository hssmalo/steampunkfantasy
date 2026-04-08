## Context

`Army` is a frozen dataclass with a `race` name string and a tuple of `ArmyUnit` objects. Each `ArmyUnit` and `ArmyModel` carries a `config` reference (the full `UnitConfig`/`ModelConfig` from the race TOML). These config references are runtime objects — they cannot be meaningfully serialized.

The config schema already has a `PathsConfig` with `races` and `templates`. Adding `armies` there is the natural extension.

## Goals / Non-Goals

**Goals:**
- Serialize an `Army` to JSON with only the primitive/structural fields (race, unit names, model names, upgrades)
- Deserialize JSON back to a live `Army` by rehydrating from the race TOML
- Add `armies_path` to config for the default save/load directory
- Pretty-print an `Army` to stdout using `rich` tables

**Non-Goals:**
- Cloud or remote storage
- Binary formats or formats other than JSON
- Versioned migration of saved files

## Decisions

### D1: Serialize only structural data, not embedded configs

`ArmyModel.config` and `ArmyUnit.config` hold full config objects from TOML. These are **not** serialized — on load, we call the existing `races.get_race()` to rehydrate them. This keeps files small and avoids duplicating TOML data.

JSON shape:
```json
{
  "race": "goblin",
  "units": [
    {
      "name": "goblin-gang",
      "models": [
        {"name": "goblin", "upgrades": []},
        {"name": "goblin-with-net", "upgrades": ["extra-sword"]}
      ]
    }
  ]
}
```

**Alternatives considered:** Serialize full config inline → rejected: files become huge and can diverge from TOML source of truth.

### D2: Convert `armies.py` to a package and add IO as a submodule

`src/spf/armies.py` is refactored into a `src/spf/armies/` package:
- `armies/data.py` — the existing data structures and builder functions (moved verbatim)
- `armies/io.py` — new `save_army(army, army_name)` / `load_army(army_name)` functions; path derived internally as `config.paths.armies / f"{army_name}.json"`
- `armies/__init__.py` — empty package marker; all callers import directly from `spf.armies.data`

IO is a shell concern and lives in its own submodule, consistent with "Functional Core, Imperative Shell".

### D3: New `display` module for rich rendering

Rendering is also a shell concern. `src/spf/display.py` will contain `print_army(army, race_config)` using `rich.table.Table`.

### D4: `armies_path` added to `PathsConfig`

Extends the existing `PathsConfig` pydantic model with a `armies: Path` field. The default value is set in the TOML config file as `{project_path}/armies/`.

## Risks / Trade-offs

- [Stale saves] If a race TOML is modified after an army was saved, rehydration may fail or produce wrong results → Mitigation: run `validate_team()` after loading and surface any errors to the user.
- [Model name collisions] Unit names are not unique if the same unit is added twice; the JSON preserves list order which is sufficient for reconstruction.
