"""Race commands for the SteamPunkFantasy CLI."""

from operator import attrgetter
from typing import cast

import configaroo
import cyclopts
import pydantic

from spf import races
from spf.config import config
from spf.console import stdout
from spf.schemas import type_aliases as t
from spf.schemas.race import RaceConfig

_NO_COST = "[gray30] -mp  -cp  -xp  -ip[/]"


def add_commands(app: cyclopts.App) -> None:
    """Add race commands to the CLI."""
    app.command(list_races, name="list")
    app.command(show_race, name="show")
    app.command(list_units, name="units")
    app.command(list_models, name="models")
    app.command(list_equipment, name="equipment")
    app.command(list_things, name="things")


def list_races() -> None:
    """List available races."""
    for race_path in sorted(config.paths.races.glob("*.toml")):
        race_name = cast("t.RaceName", race_path.stem)
        try:
            race = races.get_race(race_name)
        except pydantic.ValidationError:
            continue  # Don't list non-validated races

        stdout.print(
            f"- {race_name:<20} {race.races[race_name].name:<16}"
            f" [dim]{race_path.relative_to(config.paths.project)}[/]"
        )


def show_race(race_name: t.RaceName, section: str | None = None) -> None:
    """Load and display a saved race."""
    race = races.get_race(race_name)
    configaroo.print_configuration(race, section=section)


def _cost_str(cost: t.Cost | None) -> str:
    """Return a formatted cost string, or a dash placeholder if cost is None."""
    return str(cost) if cost is not None else _NO_COST


def _print_units(race: RaceConfig) -> None:
    """Print one line per unit with name and cost."""
    for unit in sorted(race.units.values(), key=attrgetter("name")):
        stdout.print(f"- {unit.name:<40} {_cost_str(unit.cost)}", highlight=False)


def _print_models(race: RaceConfig) -> None:
    """Print one line per model with name and cost."""
    for model in sorted(race.models.values(), key=attrgetter("name")):
        stdout.print(f"- {model.name:<40} {_cost_str(model.cost)}", highlight=False)


def _print_equipment(race: RaceConfig) -> None:
    """Print one line per equipment item with name and cost."""
    for equipment in sorted(race.equipment.values(), key=attrgetter("name")):
        stdout.print(
            f"- {equipment.name:<40} {_cost_str(equipment.cost)}", highlight=False
        )


def list_units(race_name: t.RaceName) -> None:
    """List units for a race with name and cost."""
    race = races.get_race(race_name)
    _print_units(race)


def list_models(race_name: t.RaceName) -> None:
    """List models for a race with name and cost."""
    race = races.get_race(race_name)
    _print_models(race)


def list_equipment(race_name: t.RaceName) -> None:
    """List equipment for a race with name and cost."""
    race = races.get_race(race_name)
    _print_equipment(race)


def list_things(race_name: t.RaceName) -> None:
    """List units, models, and equipment for a race with name and cost."""
    race = races.get_race(race_name)
    stdout.print("[bold]Units[/]")
    _print_units(race)
    stdout.print("[bold]Models[/]")
    _print_models(race)
    stdout.print("[bold]Equipment[/]")
    _print_equipment(race)
