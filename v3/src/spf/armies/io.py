"""Save, load, and display Army objects."""

import json
from pathlib import Path
from typing import Any

from spf.armies.data import (
    Army,
    ArmyModel,
    ArmyUnit,
    total_cost,
    unit_points,
    validate_army,
)
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
    errors = validate_army(army, cfg)
    if errors:
        msg = f"Loaded army '{army_name}' is invalid:\n" + "\n".join(errors)
        raise ValueError(msg)
    return army


def print_army(army: Army, cfg: RaceConfig) -> None:
    """Pretty-print an army to the console."""
    stdout.rule(f"{army.nick} ({cfg.races[army.race].name})")
    for unit in army.units:
        pts = unit_points(unit, cfg)
        stdout.print(
            f"[bold]{unit.config.name}[/] [yellow]({pts} pts)[/]", highlight=False
        )
        for model in unit.models:
            all_equipment = [*model.config.equipment, *model.upgrades]
            equip_str = f" ({', '.join(all_equipment)})" if all_equipment else ""
            stdout.print(f"  - {model.name}{equip_str}", highlight=False)
    cost = total_cost(army, cfg)
    stdout.print(f"\n[dim]Total cost:[/]  {cost}", highlight=False)


def _validate_army_data(data: dict[str, Any], cfg: RaceConfig) -> list[str]:
    """Collect name-resolution errors from raw JSON data before construction."""
    errors: list[str] = []
    for unit_idx, unit_data in enumerate(data["units"]):
        unit_name = unit_data["name"]
        if unit_name not in cfg.units:
            errors.append(f"Unit #{unit_idx} (name {unit_name!r}): unknown unit name")
            continue
        for model_idx, model_data in enumerate(unit_data["models"]):
            model_name = model_data["name"]
            if model_name not in cfg.models:
                errors.append(
                    f"Unit #{unit_idx} ({unit_name!r}) / model #{model_idx}"
                    f" (name {model_name!r}): unknown model name"
                )
                continue
            errors.extend(
                f"Unit #{unit_idx} ({unit_name!r}) / model #{model_idx}"
                f" ({model_name!r}): unknown equipment {upgrade!r}"
                for upgrade in model_data["upgrades"]
                if upgrade not in cfg.equipment
            )
    return errors


def _build_army(data: dict[str, Any], cfg: RaceConfig) -> Army:
    """Reconstruct an Army from deserialized JSON data and a live RaceConfig."""
    errors = _validate_army_data(data, cfg)
    if errors:
        msg = "Army JSON contains invalid entries:\n" + "\n".join(errors)
        raise ValueError(msg)
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
