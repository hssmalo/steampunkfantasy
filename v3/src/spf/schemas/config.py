"""Schema for configuration of SteamPunkFantasy."""

from pathlib import Path

from spf.schemas import StrictModel


class PathsConfig(StrictModel):
    project: Path
    armies: Path
    races: Path
    templates: Path


class SteamPunkFantasyConfig(StrictModel):
    paths: PathsConfig
