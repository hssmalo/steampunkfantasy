"""Tests for the rules data-access functions."""

from pathlib import Path

from spf import rules

SPECIALS = """\
[special.probe]
name = "Probe"
slots = ["assault"]
signature = "[{N}]"
effect = "A probe."
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
    assert rules.get_specials().special


def test_get_specials_reads_an_explicit_path(tmp_path: Path) -> None:
    path = tmp_path / "special.toml"
    path.write_text(SPECIALS, encoding="utf-8")

    probe = rules.get_specials(path).special["probe"]

    assert (probe.name, probe.slots) == ("Probe", ["assault"])


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


TERRAIN = """\
[terrain.probe]
name = "Probe"
to_hit = "0"
todo = "Rule text not yet written."
"""

MODIFIERS = """\
[speed.probe]
name = "Probe"
to_hit = "+1"
to_be_hit = "0"

[distance]

[angle]

[size]

[ability]
"""

NAMESPACES = """\
[namespaces]
probe = { name = "Probes", label = "probe", file = "probe.toml", table = "probe" }

[damage_type.probe]
name = "Probe"
todo = "Rule text not yet written."
"""


def test_get_terrain_defaults_to_the_committed_file() -> None:
    assert rules.get_terrain().terrain


def test_get_terrain_reads_an_explicit_path(tmp_path: Path) -> None:
    path = tmp_path / "terrain.toml"
    path.write_text(TERRAIN, encoding="utf-8")

    assert rules.get_terrain(path).terrain["probe"].to_hit == "0"


def test_get_modifiers_defaults_to_the_committed_file() -> None:
    assert rules.get_modifiers().ability


def test_get_modifiers_reads_an_explicit_path(tmp_path: Path) -> None:
    path = tmp_path / "modifiers.toml"
    path.write_text(MODIFIERS, encoding="utf-8")

    assert rules.get_modifiers(path).speed["probe"].to_hit == "+1"


def test_get_namespaces_defaults_to_the_committed_file() -> None:
    namespaces = rules.get_namespaces()

    # Every namespace a ref may point into is declared here, damage types
    # included -- `acid` among them, which special.toml's old hand-written
    # version list omitted.
    assert "acid" in namespaces.damage_type
    assert namespaces.namespaces["hex"].group == "terrain"


def test_get_namespaces_reads_an_explicit_path(tmp_path: Path) -> None:
    path = tmp_path / "namespaces.toml"
    path.write_text(NAMESPACES, encoding="utf-8")

    assert rules.get_namespaces(path).namespaces["probe"].name == "Probes"
