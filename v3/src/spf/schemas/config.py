"""Schema for configuration of SteamPunkFantasy."""

from pathlib import Path

from spf.schemas import StrictModel


class PathsConfig(StrictModel):
    data: Path


class SteamPunkFantasyConfig(StrictModel):
    paths: PathsConfig
