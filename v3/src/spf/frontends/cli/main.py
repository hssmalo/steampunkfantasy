"""Cyclopts CLI for SteamPunkFantasy."""

import configaroo
import cyclopts

from spf import races
from spf.config import config
from spf.frontends import cli
from spf.schemas import type_aliases as t

app = cyclopts.App(help="SteamPunkFantasy")

# Subcommands
army_app = app.command(cyclopts.App(name="army", help="Work with a specific army"))
cli.army.add_commands(army_app)


@app.command
def builder() -> None:
    """Start the army builder."""


@app.command
def show_config(section: str | None = None) -> None:
    """Show the configuration."""
    configaroo.print_configuration(config, section=section)


@app.command
def show_race(race: t.RaceName, section: str | None = None) -> None:
    """Show one race."""
    configaroo.print_configuration(races.get_race(race), section=section)
