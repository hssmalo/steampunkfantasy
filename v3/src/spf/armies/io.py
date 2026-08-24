"""Save, load, and display Army objects."""

import json
from pathlib import Path
from typing import Any

from configaroo import Configuration
from rich.markup import escape

from spf.armies.army import Army
from spf.armies.build import (
    ArmyList,
    ArmyModel,
    ArmyUnit,
    nick_error,
    validate_army,
)
from spf.config import config
from spf.console import stdout
from spf.races import get_race
from spf.render.specials import special_lines
from spf.schemas.army_pack import ArmyPackConfig
from spf.schemas.race import RaceConfig


def list_armies() -> list[Path]:
    """List all army files."""
    return sorted(config.paths.armies.rglob("*.json"))


def save_army(army: ArmyList, *, army_name: str, tournament: str | None = None) -> None:
    """Serialize ArmyList to JSON at config.paths.armies / {army_name}.json."""
    path = config.paths.armies / (tournament or "") / f"{army_name}.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    data: dict[str, Any] = {
        "race": army.race,
        "nick": army.nick,
        "units": [
            {
                "name": unit.name,
                **({"nick": unit.nick} if unit.nick is not None else {}),
                "models": [
                    {
                        "name": model.name,
                        "upgrades": list(model.upgrades),
                        **({"nick": model.nick} if model.nick is not None else {}),
                    }
                    for model in unit.models
                ],
            }
            for unit in army.units
        ],
    }
    path.write_text(json.dumps(data, indent=2) + "\n")


def _load_army_at(path: Path, *, label: str, validate: bool) -> Army:
    """Deserialize and resolve an Army from the JSON file at `path`.

    Builds an ArmyList, optionally validates it, then calls resolve() to return
    a fully resolved Army. No race_config is needed after this call. `label`
    names the Army in error messages — the load name for `load_army`, or the
    Army's Pack position for `load_pack_armies`.
    """
    if not path.exists():
        msg = f"No army file found for {label} at {path}"
        raise FileNotFoundError(msg)
    data: dict[str, Any] = json.loads(path.read_text())
    cfg = get_race(data["race"])
    army_list = _build_army_list(data, cfg=cfg)
    if validate:
        errors = validate_army(army_list, race_config=cfg)
        if errors:
            msg = f"Loaded army {label} is invalid:\n" + "\n".join(errors)
            raise ValueError(msg)
    return army_list.resolve(cfg)


def load_army(
    army_name: str, *, tournament: str | None = None, validate: bool = True
) -> Army:
    """Deserialize and resolve an Army from JSON.

    Builds an ArmyList, optionally validates it, then calls resolve() to return
    a fully resolved Army. No race_config is needed after this call.
    """
    path = config.paths.armies / (tournament or "") / f"{army_name}.json"
    return _load_army_at(path, label=f"'{army_name}'", validate=validate)


def get_army_pack(path: Path) -> ArmyPackConfig:
    """Read an Army Pack Index from `path`."""
    return (
        Configuration.from_file(path)
        .add_envs({}, prefix="SPF_")
        .parse_dynamic()
        .convert_model(ArmyPackConfig)
    )


def load_pack_armies(
    index: ArmyPackConfig, *, base_dir: Path
) -> list[tuple[str | None, Army]]:
    """Load every Army an Army Pack Index names, resolved against `base_dir`.

    Army references resolve relative to the Index's own directory (mirroring
    ADR 0018's Rulebook Sections), so `base_dir` is the Index's parent, not
    `config.paths.armies`. A failure names both the Army and its 1-based
    position, as a human counts down the Index file — a player silently
    missing from the Pack is failed at a table, so the whole build fails
    rather than skipping the Army (ADR 0018).
    """
    armies: list[tuple[str | None, Army]] = []
    for position, entry in enumerate(index.armies, start=1):
        path = base_dir / f"{entry.army}.json"
        try:
            army = _load_army_at(path, label=f"'{entry.army}'", validate=True)
        except (FileNotFoundError, ValueError) as err:
            msg = (
                f"Army {position} ({entry.army!r}) in the Army Pack Index"
                f" could not be loaded: {err}"
            )
            raise type(err)(msg) from None
        armies.append((entry.label, army))
    return armies


def print_army(army: Army) -> None:
    """Pretty-print a resolved Army to the console."""
    stdout.rule(f"{army.nick} ({army.race.title()})")
    for unit in army.units:
        cost = unit.cost()
        pts = cost.to_points()
        stdout.print(
            f"[bold]{unit.display_name}[/] - {cost} [yellow]({pts} pts)[/]",
            highlight=False,
        )
        for model in unit.models:
            equip_names = [e.name for e in model.equipment]
            equip_str = f" ({', '.join(equip_names)})" if equip_names else ""
            stdout.print(f"  - {model.display_name}{equip_str}", highlight=False)
    cost = army.cost()
    stdout.print(f"\n[dim]Total cost:[/]  {cost}", highlight=False)


def print_army_rules(army: Army) -> None:
    """Pretty-print a resolved Army as a rules-reference view."""
    stdout.rule(f"{army.nick} — {army.race.title()} Army")
    for unit in army.units:
        stdout.print(
            f"- [yellow]{unit.display_name}[/] - {unit.cost()}", highlight=False
        )
        unit_specials = special_lines(unit.unit_special_instances)
        if unit_specials:
            stdout.print("  - [dim]Specials:[/]", highlight=False)
            for heading, special in unit_specials:
                # A signature is full of square brackets, which are Rich's own
                # markup: printed raw, `[range=1]` would vanish as a tag.
                stdout.print(
                    f"    - [blue]{escape(heading)}:[/] {escape(special)}",
                    highlight=False,
                )
        for model in unit.models:
            model_pts = model.cost().to_points()
            cost_str = f" ({model_pts} pts)" if model_pts else ""
            stdout.print(f"  - {model.display_name}{cost_str}", highlight=False)
            model_specials = special_lines(model.model_special_instances)
            if model_specials:
                stdout.print("    - [dim]Specials:[/]", highlight=False)
            for heading, special in model_specials:
                stdout.print(
                    f"      - [blue]{escape(heading)}:[/] {escape(special)}",
                    highlight=False,
                )
            for equip in model.equipment:
                equip_cost_str = f" ({equip.cost})" if equip.cost is not None else ""
                stdout.print(f"    - {equip.name}{equip_cost_str}", highlight=False)
                if equip.range is not None:
                    r = equip.range
                    angle_str = "".join("*" if a else "." for a in r.angle)
                    stdout.print(
                        f"      - Range: {r.range} [{angle_str}],"
                        f" Damage {r.damage}, AP {r.ap}",
                        highlight=False,
                    )
            assault = model.assault()
            str_angles = "/".join(str(s) for s in assault.strength)
            def_angles = "/".join(str(d) for d in assault.deflection)
            stdout.print(
                f"    - Assault: Strength [{str_angles}]/{assault.strength_die}"
                f" Deflect [{def_angles}]/{assault.deflection_die}"
                f" Damage {assault.damage} AP {assault.ap}",
                highlight=False,
            )
    stdout.print(f"\n[dim]Total cost:[/]  {army.cost()}", highlight=False)


def _validate_army_data(data: dict[str, Any], *, cfg: RaceConfig) -> list[str]:
    """Collect name-resolution errors from raw JSON data before construction."""
    errors: list[str] = []
    for unit_idx, unit_data in enumerate(data["units"]):
        unit_name = unit_data["name"]
        if unit_name not in cfg.units:
            errors.append(f"Unit #{unit_idx} (name {unit_name!r}): unknown unit name")
            continue
        if unit_nick_error := nick_error(unit_data.get("nick")):
            errors.append(f"Unit #{unit_idx} ({unit_name!r}): {unit_nick_error}")
        for model_idx, model_data in enumerate(unit_data["models"]):
            model_name = model_data["name"]
            if model_name not in cfg.models:
                errors.append(
                    f"Unit #{unit_idx} ({unit_name!r}) / model #{model_idx}"
                    f" (name {model_name!r}): unknown model name"
                )
                continue
            if model_nick_error := nick_error(model_data.get("nick")):
                errors.append(
                    f"Unit #{unit_idx} ({unit_name!r}) / model #{model_idx}"
                    f" ({model_name!r}): {model_nick_error}"
                )
            errors.extend(
                f"Unit #{unit_idx} ({unit_name!r}) / model #{model_idx}"
                f" ({model_name!r}): unknown equipment {upgrade!r}"
                for upgrade in model_data["upgrades"]
                if upgrade not in cfg.equipment
            )
    return errors


def _build_army_list(data: dict[str, Any], *, cfg: RaceConfig) -> ArmyList:
    """Reconstruct an ArmyList from deserialized JSON data and a live RaceConfig."""
    errors = _validate_army_data(data, cfg=cfg)
    if errors:
        msg = "Army JSON contains invalid entries:\n" + "\n".join(errors)
        raise ValueError(msg)
    units = [
        ArmyUnit(
            name=unit_data["name"],
            config=cfg.units[unit_data["name"]],
            models=[
                ArmyModel(
                    name=model_data["name"],
                    config=cfg.models[model_data["name"]],
                    upgrades=list(model_data["upgrades"]),
                    nick=model_data.get("nick"),
                )
                for model_data in unit_data["models"]
            ],
            nick=unit_data.get("nick"),
        )
        for unit_data in data["units"]
    ]
    return ArmyList(race=data["race"], nick=data["nick"], units=units)
