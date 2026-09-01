"""Tests for the Site Index: the authored TOML naming what the site publishes."""

from pathlib import Path

import pytest
from pydantic import ValidationError

from spf.armies import io
from spf.schemas.site import SiteConfig, SitePackConfig, SiteRacesConfig

VALID_INDEX = """\
[[packs]]
pack = "dummy-b"
heading = "Dummy Pack B"

[[packs]]
pack = "dummy-a"
heading = "Dummy Pack A"
"""


def test_index_lists_its_packs_in_order() -> None:
    """The list is authored order, which nothing sorts on the way through."""
    index = SiteConfig(
        packs=[
            SitePackConfig(pack="dummy-b", heading="Dummy Pack B"),
            SitePackConfig(pack="dummy-a", heading="Dummy Pack A"),
        ]
    )

    assert [entry.pack for entry in index.packs] == ["dummy-b", "dummy-a"]
    assert index.packs[0].heading == "Dummy Pack B"


def test_index_requires_packs() -> None:
    with pytest.raises(ValidationError, match="packs"):
        SiteConfig()  # pyright: ignore[reportCallIssue]


def test_index_rejects_an_empty_pack_list() -> None:
    with pytest.raises(ValidationError, match="packs"):
        SiteConfig(packs=[])


def test_index_rejects_an_unknown_key() -> None:
    with pytest.raises(ValidationError, match="extra"):
        SiteConfig(  # pyright: ignore[reportCallIssue]
            packs=[SitePackConfig(pack="dummy-a", heading="Dummy Pack A")],
            title="nope",  # pyright: ignore[reportCallIssue]
        )


def test_index_rejects_an_unknown_key_on_an_entry() -> None:
    with pytest.raises(ValidationError, match="extra"):
        SitePackConfig(  # pyright: ignore[reportCallIssue]
            pack="dummy-a",
            heading="Dummy Pack A",
            title="nope",  # pyright: ignore[reportCallIssue]
        )


def test_entry_requires_a_heading() -> None:
    with pytest.raises(ValidationError, match="heading"):
        SitePackConfig(pack="dummy-a")  # pyright: ignore[reportCallIssue]


def test_get_site_index_parses_a_toml_file(tmp_path: Path) -> None:
    path = tmp_path / "site.toml"
    path.write_text(VALID_INDEX, encoding="utf-8")

    index = io.get_site_index(path)

    assert [entry.pack for entry in index.packs] == ["dummy-b", "dummy-a"]
    assert [entry.heading for entry in index.packs] == ["Dummy Pack B", "Dummy Pack A"]


RACES_INDEX = """\
[[packs]]
pack = "dummy"
heading = "Dummy Pack"

[races]
heading = "Races"
publish = ["elf", "dwarf"]
"""


def test_index_keeps_published_races_in_authored_order() -> None:
    """The list is editorial: the Landing Page rows follow it, unsorted."""
    index = SiteConfig(
        packs=[SitePackConfig(pack="dummy", heading="Dummy Pack")],
        races=SiteRacesConfig(heading="Races", publish=["elf", "dwarf"]),
    )

    assert index.races is not None
    assert index.races.publish == ["elf", "dwarf"]
    assert index.races.heading == "Races"


def test_index_without_a_races_block_publishes_no_races() -> None:
    """A site that never opted in is not a broken one."""
    index = SiteConfig(packs=[SitePackConfig(pack="dummy", heading="Dummy Pack")])

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
        SiteRacesConfig(heading="Races", publish=["dark-elf"])  # pyright: ignore[reportArgumentType]


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
