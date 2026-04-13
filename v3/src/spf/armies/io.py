"""Save, load, and display Army objects."""

import json
from pathlib import Path
from typing import Any

from rich.table import Table

from spf.armies.data import Army, ArmyModel, ArmyUnit, total_cost, validate_team
from spf.config import config
from spf.console import stdout
from spf.races import get_race
from spf.schemas.race import RaceConfig


def list_armies() -> list[Path]:
    """List all army files."""
    return sorted(config.paths.armies.rglob("*.json"))


def save_army(army: Army, army_name: str, tournament: str | None = None) -> None:
    """Serialize army to JSON at config.paths.armies / {army_name}.json."""
    path = config.paths.armies / (tournament or "") / f"{army_name}.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    data: dict[str, Any] = {
        "race": army.race,
        "nick": army.nick,
        "units": [
            {
                "name": unit.name,
                "models": [
                    {"name": model.name, "upgrades": list(model.upgrades)}
                    for model in unit.models
                ],
            }
            for unit in army.units
        ],
    }
    path.write_text(json.dumps(data, indent=2))


def load_army(army_name: str, tournament: str | None = None) -> Army:
    """Deserialize army from JSON at config.paths.armies / {army_name}.json."""
    path = config.paths.armies / (tournament or "") / f"{army_name}.json"
    if not path.exists():
        msg = f"No army file found for '{army_name}' at {path}"
        raise FileNotFoundError(msg)
    data: dict[str, Any] = json.loads(path.read_text())
    cfg = get_race(data["race"])
    army = _build_army(data, cfg)
    errors = validate_team(army, cfg)
    if errors:
        msg = f"Loaded army '{army_name}' is invalid:\n" + "\n".join(errors)
        raise ValueError(msg)
    return army


def print_army(army: Army, cfg: RaceConfig) -> None:
    """Pretty-print an army to the console using rich."""
    stdout.rule(f"{army.nick} \u2014 {cfg.races[army.race].name} Army")
    for unit in army.units:
        table = Table(title=f"Unit: {unit.config.name}", show_header=True)
        table.add_column("Model")
        table.add_column("Equipment")
        for model in unit.models:
            upgrades = ", ".join([*model.config.equipment, *model.upgrades])
            table.add_row(model.name, upgrades)
        stdout.print(table)
    cost = total_cost(army, cfg)
    stdout.print(
        f"[dim]Total cost:[/]  MP={cost.mp}  CP={cost.cp}  XP={cost.xp}  IP={cost.ip}",
        highlight=False,
    )


def _build_army(data: dict[str, Any], cfg: RaceConfig) -> Army:
    """Reconstruct an Army from deserialized JSON data and a live RaceConfig."""
    units = tuple(
        ArmyUnit(
            name=unit_data["name"],
            config=cfg.units[unit_data["name"]],
            models=tuple(
                ArmyModel(
                    name=model_data["name"],
                    config=cfg.models[model_data["name"]],
                    upgrades=tuple(model_data["upgrades"]),
                )
                for model_data in unit_data["models"]
            ),
        )
        for unit_data in data["units"]
    )
    return Army(race=data["race"], nick=data["nick"], units=units)
