"""Race commands for the SteamPunkFantasy CLI."""

from typing import cast

import configaroo
import cyclopts
import pydantic

from spf import races
from spf.config import config
from spf.console import stdout
from spf.schemas import type_aliases as t


def add_commands(app: cyclopts.App) -> None:
    """Add race commands to the CLI."""
    app.command(list_races, name="list")
    app.command(show_race, name="show")


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
