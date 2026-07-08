"""Command line interface for SteamPunkFantasy."""

from spf.frontends.cli import army, race, render, rules, special
from spf.frontends.cli.main import app

__all__ = ["app", "army", "race", "render", "rules", "special"]
