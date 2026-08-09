"""Tests for the rules data-access functions."""

from pathlib import Path

from spf import rules

SPECIALS = """\
[assault]

[assault.probe]
name = "Probe"
short = "[N]"
explanation = "A probe."

[unit]

[range_]
"""

TOKENS = """\
explanation = "How tokens work."

[tokens]

[tokens.probe]
name = "Probe Token"
effect = "Nothing happens."
"""

HEXES = """\
explanation = "How hexes work."

[hexes]

[hexes.probe]
name = "Probe Hex"
effect = "Nothing happens here either."
"""


def test_get_specials_defaults_to_the_committed_file() -> None:
    assert rules.get_specials().assault


def test_get_specials_reads_an_explicit_path(tmp_path: Path) -> None:
    path = tmp_path / "special.toml"
    path.write_text(SPECIALS, encoding="utf-8")

    assert rules.get_specials(path).assault["probe"].name == "Probe"


def test_get_tokens_defaults_to_the_committed_file() -> None:
    assert rules.get_tokens().tokens


def test_get_tokens_reads_an_explicit_path(tmp_path: Path) -> None:
    path = tmp_path / "tokens.toml"
    path.write_text(TOKENS, encoding="utf-8")

    index = rules.get_tokens(path)

    assert index.explanation == "How tokens work."
    assert index.tokens["probe"].name == "Probe Token"


def test_get_hexes_defaults_to_the_committed_file() -> None:
    assert rules.get_hexes().hexes


def test_get_hexes_reads_an_explicit_path(tmp_path: Path) -> None:
    path = tmp_path / "hexes.toml"
    path.write_text(HEXES, encoding="utf-8")

    index = rules.get_hexes(path)

    assert index.explanation == "How hexes work."
    assert index.hexes["probe"].name == "Probe Hex"
