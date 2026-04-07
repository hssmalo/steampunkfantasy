# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
# Run CLI
uv run spf --help
uv run spf show-army goblin

# Run tests
uv run pytest
uv run pytest tests/test_data.py::test_list_armies_includes_known_armies  # single test

# Lint and format
uv run ruff check src/
uv run ruff format src/

# Type checking
uv run ty check src/

# Check typos
uv run typos
```

## Architecture

**SteamPunkFantasy (spf)** is a tabletop hex-based wargame army management tool. It reads army definitions from TOML files and validates/displays them.

### Data flow

`data/[army].toml` → `configaroo.Configuration` → Pydantic model (`ArmyConfig`) → accessed via `spf.armies`

- `configs/spf.toml` — application config (paths to data and templates directories)
- `data/*.toml` — one file per army (goblin, elf, dwarf, etc.), each with `races`, `units`, `models`, and `equipments` sections
- `src/spf/config.py` — loads `configs/spf.toml` using `configaroo`, parsed into `SteamPunkFantasyConfig`
- `src/spf/armies.py` — data access layer; reads and validates army TOML files against `ArmyConfig`
- `src/spf/data.py` — public API re-exporting from `armies.py` (prefer importing from here)
- `src/spf/schemas/army.py` — Pydantic models for `ArmyConfig`, `UnitConfig`, `ModelConfig`, `EquipmentConfig`, etc.
- `src/spf/schemas/type_aliases.py` — domain type aliases (`ArmyName`, `Size`, `Cost`, `ModelType`, etc.) plus `ParsedEquipmentLimit` and `ParsedRequirement` which use `BeforeValidator` to parse `"Hands:2"` style strings
- `src/spf/frontends/cli/main.py` — Cyclopts CLI commands; currently `show-army` and `show-config`

### Key concepts

- **Army TOML files** are single-race: a single file defines units/models/equipment for one race. `get_units(army_name)` filters by `race == army_name`.
- **Equipment limits** use `"Holder:count"` syntax (e.g. `"Hands:2"`, `"Grenades:∞"`), parsed by `_parse_equipment_limit`.
- **Requirements** use `"key:value"` syntax (e.g. `"Hands:2"`, `"type:Infantry"`), parsed by `_parse_requirement`.
- **Stacker** — generic Pydantic model for equipment stat modifiers; supports `add`, `replace`, and `append` operations on base model stats.
- **Angles** — a `list[T]` representing [front, front left/right, back left/right, back] directional values.
- All Pydantic models use `extra="forbid"` (via `StrictModel`) to catch typos in TOML.
- `ArmyName` is a `Literal` type — add new armies there when adding new TOML files.
