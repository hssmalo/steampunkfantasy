"""Data access functions for SteamPunkFantasy rules."""

from pathlib import Path

from configaroo import Configuration

from spf.config import config
from spf.schemas import rules as r
from spf.schemas.rulebook import RulebookConfig

RULEBOOK_INDEX = "rulebook.toml"


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


def get_rulebook(path: Path | None = None) -> RulebookConfig:
    """Read the Rulebook Index, by default the committed `rules/rulebook.toml`.

    Takes a path rather than a file name (unlike the rules loaders above) so
    `spf render general-rules --index` can point at an alternate index
    anywhere on disk.
    """
    path = path if path is not None else config.paths.rules / RULEBOOK_INDEX
    return (
        Configuration.from_file(path)
        .add_envs({}, prefix="SPF_")
        .parse_dynamic()
        .convert_model(RulebookConfig)
    )
