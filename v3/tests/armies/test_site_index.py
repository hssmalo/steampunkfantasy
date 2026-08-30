"""Tests for the Site Index: the authored TOML naming the packs the site publishes."""

from pathlib import Path

import pytest
from pydantic import ValidationError

from spf.armies import io
from spf.schemas.site import SiteConfig, SitePackConfig

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
