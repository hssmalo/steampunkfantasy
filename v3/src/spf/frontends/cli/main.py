"""Cyclopts CLI for SteamPunkFantasy."""

import shlex
import subprocess
from pathlib import Path

import configaroo
import cyclopts

from spf.config import config
from spf.frontends import cli

app = cyclopts.App(help="SteamPunkFantasy")

# Subcommands
army_app = app.command(cyclopts.App(name="army", help="Work with a specific army."))
cli.army.add_commands(army_app)
race_app = app.command(cyclopts.App(name="race", help="Work with a specific race."))
cli.race.add_commands(race_app)
rules_app = app.command(cyclopts.App(name="rules", help="Work with rules."))
cli.rules.add_commands(rules_app)
render_app = app.command(cyclopts.App(name="render", help="Render products to files."))
cli.render.add_commands(render_app)
special_app = app.command(cyclopts.App(name="special", help="Work with special rules."))
cli.special.add_commands(special_app)


@app.command
def builder() -> None:
    """Start the army builder."""
    path = Path(__file__).parent.parent / "builder" / "app.py"
    command = f"streamlit run {path}"
    subprocess.run(shlex.split(command), check=True, shell=False)  # noqa: S603


@app.command
def show_config(section: str | None = None) -> None:
    """Show the configuration."""
    configaroo.print_configuration(config, section=section)
