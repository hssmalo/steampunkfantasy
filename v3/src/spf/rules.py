"""Data access functions for SteamPunkFantasy rules."""

from pathlib import Path

from configaroo import Configuration

from spf.config import config
from spf.schemas import rules as r
from spf.schemas.rulebook import RulebookConfig

RULEBOOK_INDEX = "rulebook.toml"


def _read(path: Path) -> Configuration:
    """Read one rules file."""
    return Configuration.from_file(path).add_envs({}, prefix="SPF_").parse_dynamic()


def _get_rules(path: Path | None, file_name: str) -> Configuration:
    """Read one rules file: `path` if given, else `file_name` beside the rest.

    The Rulebook Index names each Section's source file, so a Rulebook parser
    has a path in hand and must be able to hand it over; every other caller
    wants the committed file and passes nothing.
    """
    return _read(path if path is not None else config.paths.rules / file_name)


def get_specials(path: Path | None = None) -> r.SpecialRulesConfig:
    """Get rules for specials."""
    return _get_rules(path, "special.toml").convert_model(r.SpecialRulesConfig)


def get_tokens(path: Path | None = None) -> r.TokenRulesConfig:
    """Get rules for tokens."""
    return _get_rules(path, "tokens.toml").convert_model(r.TokenRulesConfig)


def get_hexes(path: Path | None = None) -> r.HexRulesConfig:
    """Get rules for hexes."""
    return _get_rules(path, "hexes.toml").convert_model(r.HexRulesConfig)


def rulebook_index_path(path: Path | None = None) -> Path:
    """Resolve `path` against the committed Index, the default when it is None.

    The one place that default lives: callers need the path itself, not just
    what it loads, because a Section's sources resolve beside its Index.
    """
    return path if path is not None else config.paths.rules / RULEBOOK_INDEX


def get_rulebook(path: Path | None = None) -> RulebookConfig:
    """Read the Rulebook Index, by default the committed `rules/rulebook.toml`.

    Takes a path rather than a file name (unlike the rules loaders above) so
    `spf render general-rules --index` can point at an alternate Index
    anywhere on disk.
    """
    return _read(rulebook_index_path(path)).convert_model(RulebookConfig)
