"""Data access functions for SteamPunkFantasy rules."""

from configaroo import Configuration

from spf.config import config
from spf.schemas import rules as r


def _get_rules(file_name: str) -> Configuration:
    """Read one rules file."""
    path = config.paths.rules / file_name
    return Configuration.from_file(path).add_envs({}, prefix="SPF_").parse_dynamic()


def get_specials() -> r.SpecialRulesConfig:
    """Get rules for specials."""
    return _get_rules("special.toml").convert_model(r.SpecialRulesConfig)


def get_tokens() -> r.TokenRulesConfig:
    """Get rules for tokens."""
    return _get_rules("tokens.toml").convert_model(r.TokenRulesConfig)


def get_hexes() -> r.HexRulesConfig:
    """Get rules for hexes."""
    return _get_rules("hexes.toml").convert_model(r.HexRulesConfig)
