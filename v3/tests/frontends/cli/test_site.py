"""Tests for the site build: the Landing Page generator and `render_site`.

The Landing Page is a pure function over already-built sections, and the
section builders are pure functions over already-rendered pages, so these tests
build `SitePage`s by hand rather than rendering anything for real. The
`render_site` tests cover only what it refuses to build, which needs no render.
"""

import re
from pathlib import Path

import pytest

from spf.config import config
from spf.frontends.cli.site import (
    SITE_INDEX_PATH,
    SOURCE_URL,
    SitePage,
    SiteRow,
    SiteSection,
    loose_section,
    pack_section,
    race_section,
    render_landing_page,
    render_site,
)


def _army_pages(label: str, stem: str) -> list[SitePage]:
    """Both Products in both Formats for one Army, as `render_site` writes them."""
    return [
        SitePage(
            product=product,
            label=label,
            fmt=fmt,
            relative_path=f"{product}/{stem}.{fmt}",
        )
        for product in ("army-rules", "cards")
        for fmt in ("pdf", "html")
    ]


def _race_pages(label: str, stem: str) -> list[SitePage]:
    """Both Formats of one Race Overview."""
    return [
        SitePage(
            product="race-overview",
            label=label,
            fmt=fmt,
            relative_path=f"race-overview/{stem}.{fmt}",
        )
        for fmt in ("pdf", "html")
    ]


RULEBOOK = SitePage(
    product="general-rules",
    label="Rulebook",
    fmt="pdf",
    relative_path="general-rules/rulebook.pdf",
)
RULEBOOK_SECTION = loose_section("general-rules", [RULEBOOK])


def test_loose_section_is_one_labeled_line_and_no_table() -> None:
    """A Product outside every table has no heading and no columns to fill."""
    section = loose_section("general-rules", [RULEBOOK])

    assert section.heading is None
    assert section.columns == ()
    assert section.rows == ()
    assert [line.label for line in section.lines] == ["Rulebook"]
    assert section.lines[0].pages == (RULEBOOK,)


def test_pack_section_is_one_row_per_army_and_the_pack_below() -> None:
    """The Pack's own document is a trailing line, never one of its Armies."""
    pack_pages = [
        SitePage(
            product="army-pack",
            label="Dummy Pack Document",
            fmt="pdf",
            relative_path="army-pack/2026-dummy.pdf",
        )
    ]
    section = pack_section(
        "Dummy Pack A",
        [
            *_army_pages("Dummy Army One", "2026-dummy-one"),
            *_army_pages("Dummy Army Two", "2026-dummy-two"),
        ],
        pack_pages,
    )

    assert section.heading == "Dummy Pack A"
    assert section.columns == ("Army", "Army Reference", "Order Cards")
    assert [row.label for row in section.rows] == [
        "Dummy Army One",
        "Dummy Army Two",
    ]
    assert [len(row.cells) for row in section.rows] == [2, 2]
    assert [line.label for line in section.lines] == ["Army Pack"]


def test_a_pack_that_rendered_no_pack_document_has_no_trailing_line() -> None:
    """The page links what rendered; it never fabricates a link that did not."""
    section = pack_section(
        "Dummy Pack A", _army_pages("Dummy Army One", "2026-dummy-one"), []
    )

    assert section.lines == ()


def test_race_section_is_one_race_overview_column() -> None:
    """Rows are Races, and the one Product column is the Race Overview."""
    section = race_section(
        "Races",
        [
            *_race_pages("Dummy Race One", "dummyone"),
            *_race_pages("Dummy Race Two", "dummytwo"),
        ],
    )

    assert section.heading == "Races"
    assert section.columns == ("Race", "Race Overview")
    assert [row.label for row in section.rows] == ["Dummy Race One", "Dummy Race Two"]
    assert [len(row.cells) for row in section.rows] == [1, 1]


def test_links_every_page() -> None:
    """Each page's relative path appears as a link target."""
    html = render_landing_page(
        [
            RULEBOOK_SECTION,
            pack_section(
                "Dummy Pack C",
                [
                    SitePage(
                        product="army-rules",
                        label="2026-dummy-one",
                        fmt="html",
                        relative_path="army-rules/2026-dummy-one.html",
                    )
                ],
                [],
            ),
        ]
    )

    assert 'href="general-rules/rulebook.pdf"' in html
    assert 'href="army-rules/2026-dummy-one.html"' in html


def test_a_loose_section_renders_above_every_heading() -> None:
    """The Rulebook belongs to no pack, so it sits above the first heading."""
    html = render_landing_page(
        [
            RULEBOOK_SECTION,
            pack_section(
                "Dummy Pack C", _army_pages("Dummy Army One", "2026-dummy-one"), []
            ),
        ]
    )

    assert html.index("general-rules/rulebook.pdf") < html.index("<h2>")


def test_sections_render_in_the_order_given() -> None:
    """Sections follow Site Index order — neither alphabetical nor chronological."""
    html = render_landing_page(
        [
            race_section("Races", _race_pages("Dummy Race One", "dummyone")),
            pack_section(
                "Dummy Pack C", _army_pages("Dummy Army One", "2026-dummy-one"), []
            ),
            pack_section(
                "Dummy Pack A", _army_pages("Dummy Army One", "2026-dummy-one"), []
            ),
            pack_section(
                "Dummy Pack B", _army_pages("Dummy Army Two", "2026-dummy-two"), []
            ),
        ]
    )

    assert html.index("Races") < html.index("Dummy Pack C")
    assert html.index("Dummy Pack C") < html.index("Dummy Pack A")
    assert html.index("Dummy Pack A") < html.index("Dummy Pack B")


def test_an_army_is_one_row_with_a_cell_per_product() -> None:
    """Each Army is a `<tr>`: its name, its Army Reference, its Order Cards."""
    html = render_landing_page(
        [
            pack_section(
                "Dummy Pack A", _army_pages("Dummy Army One", "2026-dummy-one"), []
            )
        ]
    )

    rows = re.findall(r"<tr>(.*?)</tr>", html, flags=re.DOTALL)
    army_rows = [row for row in rows if "Dummy Army One" in row]
    assert len(army_rows) == 1
    cells = re.findall(r"<td>(.*?)</td>", army_rows[0], flags=re.DOTALL)
    assert len(cells) == 3
    assert 'href="army-rules/2026-dummy-one.pdf"' in cells[1]
    assert 'href="army-rules/2026-dummy-one.html"' in cells[1]
    assert 'href="cards/2026-dummy-one.pdf"' in cells[2]
    assert 'href="cards/2026-dummy-one.html"' in cells[2]


def test_a_race_is_one_row_with_both_formats_in_one_cell() -> None:
    """A Race is a `<tr>`: its name, then both Formats of its Race Overview."""
    html = render_landing_page(
        [race_section("Races", _race_pages("Dummy Race One", "dummyone"))]
    )

    rows = re.findall(r"<tr>(.*?)</tr>", html, flags=re.DOTALL)
    race_rows = [row for row in rows if "Dummy Race One" in row]
    assert len(race_rows) == 1
    cells = re.findall(r"<td>(.*?)</td>", race_rows[0], flags=re.DOTALL)
    assert len(cells) == 2
    assert 'href="race-overview/dummyone.pdf"' in cells[1]
    assert 'href="race-overview/dummyone.html"' in cells[1]


def test_a_section_with_no_rows_still_renders_its_table() -> None:
    """An opted-in section with nothing in it says so, visibly."""
    html = render_landing_page([race_section("Races", [])])

    assert "<h2>Races</h2>" in html
    rows = re.findall(r"<tr>(.*?)</tr>", html, flags=re.DOTALL)
    assert rows == ["<th>Race</th><th>Race Overview</th>"]


def test_the_army_pack_renders_below_its_table_not_as_a_row() -> None:
    """A Pack's own document is a link under its table, not one of its Armies."""
    html = render_landing_page(
        [
            pack_section(
                "Dummy Pack A",
                _army_pages("Dummy Army One", "2026-dummy-one"),
                [
                    SitePage(
                        product="army-pack",
                        label="Dummy Pack Document",
                        fmt="pdf",
                        relative_path="army-pack/2026-dummy.pdf",
                    )
                ],
            )
        ]
    )

    assert "army-pack/2026-dummy.pdf" not in html[: html.index("</table>")]
    assert "army-pack/2026-dummy.pdf" in html[html.index("</table>") :]
    rows = re.findall(r"<tr>(.*?)</tr>", html, flags=re.DOTALL)
    assert not any("army-pack/2026-dummy.pdf" in row for row in rows)


def test_a_missing_product_leaves_an_empty_cell() -> None:
    """The page links what rendered; it never fabricates a link that did not."""
    html = render_landing_page(
        [
            pack_section(
                "Dummy Pack C",
                [
                    SitePage(
                        product="army-rules",
                        label="Dummy Army One",
                        fmt="pdf",
                        relative_path="army-rules/2026-dummy-one.pdf",
                    )
                ],
                [],
            )
        ]
    )

    assert "cards/2026-dummy-one" not in html
    assert "<td></td>" in html


def test_the_footer_links_the_repository() -> None:
    """A reader on the site can find the sources it was generated from."""
    html = render_landing_page([RULEBOOK_SECTION])

    assert f'href="{SOURCE_URL}"' in html
    assert "<footer>" in html


def test_escapes_untrusted_looking_content() -> None:
    """Labels, headings, and paths are HTML-escaped before being embedded."""
    html = render_landing_page(
        [
            SiteSection(
                heading="<em>",
                columns=("<b>",),
                rows=(SiteRow(label="<script>", cells=()),),
                lines=(),
            )
        ]
    )

    assert "<script>" not in html
    assert "&lt;script&gt;" in html
    assert "<em>" not in html
    assert "&lt;em&gt;" in html
    assert "&lt;b&gt;" in html


@pytest.fixture
def armies_dir(tmp_path: Path, *, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Redirect config.paths.armies to a temporary directory."""
    monkeypatch.setattr(config.paths, "armies", tmp_path)
    return tmp_path


def test_a_missing_site_index_fails_the_build(armies_dir: Path) -> None:  # noqa: ARG001
    """Without the Site Index there is nothing authored to publish."""
    with pytest.raises(SystemExit) as exit_info:
        render_site()

    assert exit_info.value.code == 1


def test_a_pack_missing_from_disk_fails_the_whole_build(armies_dir: Path) -> None:
    """A Pack the Site Index names but disk lacks fails the site, not its section.

    Publishing the other packs would leave a hole no one on the page can see
    (ADR 0023's whole-site failure policy).
    """
    (armies_dir / SITE_INDEX_PATH).write_text(
        '[[packs]]\npack = "ghost"\nheading = "Ghost Armies"\n', encoding="utf-8"
    )

    with pytest.raises(SystemExit) as exit_info:
        render_site()

    assert exit_info.value.code == 1
