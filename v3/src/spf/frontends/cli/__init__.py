"""Command line interface for SteamPunkFantasy."""

from spf.frontends.cli import army, race, special
from spf.frontends.cli.main import app

__all__ = ["app", "army", "race", "special"]
