"""Tests for the Site Index: the authored TOML naming what the site publishes."""

from pathlib import Path

import pytest
from pydantic import ValidationError

from spf.armies import io
from spf.schemas.site import SiteConfig, SitePackConfig, SiteRacesConfig

VALID_INDEX = """\
[[packs]]
pack = "showcase"
heading = "Showcase Armies"

[[packs]]
pack = "2025"
heading = "2025 Armies"
"""


def test_index_lists_its_packs_in_order() -> None:
    index = SiteConfig(
        packs=[
            SitePackConfig(pack="showcase", heading="Showcase Armies"),
            SitePackConfig(pack="2025", heading="2025 Armies"),
        ]
    )

    assert [entry.pack for entry in index.packs] == ["showcase", "2025"]
    assert index.packs[0].heading == "Showcase Armies"


def test_index_requires_packs() -> None:
    with pytest.raises(ValidationError, match="packs"):
        SiteConfig()  # pyright: ignore[reportCallIssue]


def test_index_rejects_an_empty_pack_list() -> None:
    with pytest.raises(ValidationError, match="packs"):
        SiteConfig(packs=[])


def test_index_rejects_an_unknown_key() -> None:
    with pytest.raises(ValidationError, match="extra"):
        SiteConfig(  # pyright: ignore[reportCallIssue]
            packs=[SitePackConfig(pack="showcase", heading="Showcase Armies")],
            title="nope",  # pyright: ignore[reportCallIssue]
        )


def test_index_rejects_an_unknown_key_on_an_entry() -> None:
    with pytest.raises(ValidationError, match="extra"):
        SitePackConfig(  # pyright: ignore[reportCallIssue]
            pack="showcase",
            heading="Showcase Armies",
            title="nope",  # pyright: ignore[reportCallIssue]
        )


def test_entry_requires_a_heading() -> None:
    with pytest.raises(ValidationError, match="heading"):
        SitePackConfig(pack="showcase")  # pyright: ignore[reportCallIssue]


def test_get_site_index_parses_a_toml_file(tmp_path: Path) -> None:
    path = tmp_path / "site.toml"
    path.write_text(VALID_INDEX, encoding="utf-8")

    index = io.get_site_index(path)

    assert [entry.pack for entry in index.packs] == ["showcase", "2025"]
    assert [entry.heading for entry in index.packs] == [
        "Showcase Armies",
        "2025 Armies",
    ]


RACES_INDEX = """\
[[packs]]
pack = "showcase"
heading = "Showcase Armies"

[races]
heading = "Races"
publish = ["elf", "dwarf"]
"""


def test_index_keeps_published_races_in_authored_order() -> None:
    """The list is editorial: the Landing Page rows follow it, unsorted."""
    index = SiteConfig(
        packs=[SitePackConfig(pack="showcase", heading="Showcase Armies")],
        races=SiteRacesConfig(heading="Races", publish=["elf", "dwarf"]),
    )

    assert index.races is not None
    assert index.races.publish == ["elf", "dwarf"]
    assert index.races.heading == "Races"


def test_index_without_a_races_block_publishes_no_races() -> None:
    """A site that never opted in is not a broken one."""
    index = SiteConfig(packs=[SitePackConfig(pack="showcase", heading="Showcase")])

    assert index.races is None


def test_index_accepts_an_empty_publish_list() -> None:
    """Opting in with nothing to show yet is a legal, meaningful state."""
    races = SiteRacesConfig(heading="Races", publish=[])

    assert races.publish == []


def test_races_rejects_an_unknown_key() -> None:
    with pytest.raises(ValidationError, match="extra"):
        SiteRacesConfig(  # pyright: ignore[reportCallIssue]
            heading="Races",
            races=["elf"],  # pyright: ignore[reportCallIssue]
        )


def test_races_rejects_a_name_that_is_not_a_race() -> None:
    """A typo is a schema error naming the races there are, not a silent miss."""
    with pytest.raises(ValidationError, match="publish"):
        SiteRacesConfig(heading="Races", publish=["elfs"])  # pyright: ignore[reportArgumentType]


def test_races_requires_a_heading() -> None:
    with pytest.raises(ValidationError, match="heading"):
        SiteRacesConfig(publish=["elf"])  # pyright: ignore[reportCallIssue]


def test_get_site_index_parses_a_races_block(tmp_path: Path) -> None:
    path = tmp_path / "site.toml"
    path.write_text(RACES_INDEX, encoding="utf-8")

    index = io.get_site_index(path)

    assert index.races is not None
    assert index.races.heading == "Races"
    assert index.races.publish == ["elf", "dwarf"]
