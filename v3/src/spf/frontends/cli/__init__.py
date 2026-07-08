"""Command line interface for SteamPunkFantasy."""

from spf.frontends.cli import army, assets, race, render, rules, special
from spf.frontends.cli.main import app

__all__ = ["app", "army", "assets", "race", "render", "rules", "special"]
