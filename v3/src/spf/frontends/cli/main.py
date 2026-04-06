"""Cyclopts CLI for SteamPunkFantasy."""

import configaroo
import cyclopts

from spf import armies
from spf.config import config
from spf.schemas import type_aliases as t

app = cyclopts.App(help="SteamPunkFantasy")


@app.command
def builder() -> None:
    """Start the army builder."""


@app.command
def show_config(section: str | None = None) -> None:
    """Show the configuration."""
    configaroo.print_configuration(config, section=section)


@app.command
def show_army(army: t.ArmyName, section: str | None = None) -> None:
    """Show one army."""
    configaroo.print_configuration(armies.get_army(army), section=section)
