"""Command line interface for SteamPunkFantasy."""

from spf.frontends.cli import (
    army,
    assets,
    lint,
    race,
    render,
    rules,
    site,
    special,
)
from spf.frontends.cli.main import app

__all__ = [
    "app",
    "army",
    "assets",
    "lint",
    "race",
    "render",
    "rules",
    "site",
    "special",
]
