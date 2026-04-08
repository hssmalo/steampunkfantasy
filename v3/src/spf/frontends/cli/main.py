"""Cyclopts CLI for SteamPunkFantasy."""

import configaroo
import cyclopts

from spf.config import config
from spf.frontends import cli

app = cyclopts.App(help="SteamPunkFantasy")

# Subcommands
army_app = app.command(cyclopts.App(name="army", help="Work with a specific army"))
cli.army.add_commands(army_app)
race_app = app.command(cyclopts.App(name="race", help="Work with a specific race"))
cli.race.add_commands(race_app)


@app.command
def builder() -> None:
    """Start the army builder."""


@app.command
def show_config(section: str | None = None) -> None:
    """Show the configuration."""
    configaroo.print_configuration(config, section=section)
