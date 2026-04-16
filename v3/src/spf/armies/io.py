"""Save, load, and display Army objects."""

import json
from pathlib import Path
from typing import Any

from spf.armies.army import Army
from spf.armies.build import ArmyList, ArmyModel, ArmyUnit, validate_army
from spf.config import config
from spf.console import stdout
from spf.races import get_race
from spf.schemas.race import RaceConfig


def list_armies() -> list[Path]:
    """List all army files."""
    return sorted(config.paths.armies.rglob("*.json"))


def save_army(army: ArmyList, army_name: str, tournament: str | None = None) -> None:
    """Serialize ArmyList to JSON at config.paths.armies / {army_name}.json."""
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


def load_army(
    army_name: str, tournament: str | None = None, *, validate: bool = True
) -> Army:
    """Deserialize and resolve an Army from JSON.

    Builds an ArmyList, optionally validates it, then calls resolve() to return
    a fully resolved Army. No race_config is needed after this call.
    """
    path = config.paths.armies / (tournament or "") / f"{army_name}.json"
    if not path.exists():
        msg = f"No army file found for '{army_name}' at {path}"
        raise FileNotFoundError(msg)
    data: dict[str, Any] = json.loads(path.read_text())
    cfg = get_race(data["race"])
    army_list = _build_army_list(data, cfg)
    if validate:
        errors = validate_army(army_list, cfg)
        if errors:
            msg = f"Loaded army '{army_name}' is invalid:\n" + "\n".join(errors)
            raise ValueError(msg)
    return army_list.resolve(cfg)


def print_army(army: Army) -> None:
    """Pretty-print a resolved Army to the console."""
    stdout.rule(f"{army.nick} ({army.race.title()})")
    for unit in army.units:
        pts = unit.cost().to_points()
        stdout.print(
            f"[bold]{unit.config.name}[/] [yellow]({pts} pts)[/]", highlight=False
        )
        for model in unit.models:
            equip_names = [e.name for e in model.equipment]
            equip_str = f" ({', '.join(equip_names)})" if equip_names else ""
            stdout.print(f"  - {model.name}{equip_str}", highlight=False)
    cost = army.cost()
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


def _build_army_list(data: dict[str, Any], cfg: RaceConfig) -> ArmyList:
    """Reconstruct an ArmyList from deserialized JSON data and a live RaceConfig."""
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
    return ArmyList(race=data["race"], nick=data["nick"], units=units)
