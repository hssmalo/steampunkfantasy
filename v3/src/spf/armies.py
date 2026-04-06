"""Handle army files."""

from configaroo import Configuration

from spf.config import config
from spf.schemas import type_aliases as t
from spf.schemas.army import ArmyConfig


def get_army(army_name: t.ArmyName) -> ArmyConfig:
    """Get the definition of one army."""
    path = config.paths.data / f"{army_name}.toml"
    return Configuration.from_file(path).convert_model(ArmyConfig)
