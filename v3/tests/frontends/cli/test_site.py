"""Tests for the site build: the Landing Page generator and `render_site`.

`render_landing_page` is a pure function over already-rendered pages, so those
tests build `SitePage`s by hand rather than rendering anything for real. The
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
    render_landing_page,
    render_site,
)


def _army_pages(group: str, label: str, stem: str) -> list[SitePage]:
    """Both Products in both Formats for one Army, as `render_site` writes them."""
    return [
        SitePage(
            product=product,
            label=label,
            fmt=fmt,
            relative_path=f"{product}/{stem}.{fmt}",
            group=group,
        )
        for product in ("army-rules", "cards")
        for fmt in ("pdf", "html")
    ]


RULEBOOK = SitePage(
    product="general-rules",
    label="Rulebook",
    fmt="pdf",
    relative_path="general-rules/rulebook.pdf",
    group=None,
)


def test_links_every_page() -> None:
    """Each page's relative path appears as a link target."""
    pages = [
        RULEBOOK,
        SitePage(
            product="army-rules",
            label="showcase-elf",
            fmt="html",
            relative_path="army-rules/showcase-elf.html",
            group="Showcase Armies",
        ),
    ]

    html = render_landing_page(pages)

    assert 'href="general-rules/rulebook.pdf"' in html
    assert 'href="army-rules/showcase-elf.html"' in html


def test_ungrouped_pages_render_above_every_section() -> None:
    """The Rulebook belongs to no pack, so it sits above the first heading."""
    pages = [*_army_pages("Showcase Armies", "Showcase Elf", "showcase-elf"), RULEBOOK]

    html = render_landing_page(pages)

    assert html.index("general-rules/rulebook.pdf") < html.index("<h2>")


def test_groups_render_in_first_appearance_order() -> None:
    """Sections follow Site Index order — neither alphabetical nor chronological."""
    pages = [
        *_army_pages("Showcase Armies", "Showcase Elf", "showcase-elf"),
        *_army_pages("2025 Armies", "Geir Arne: Sabeltann", "2025-geir-arne"),
        *_army_pages("2024 Armies", "Morten: Gnomes", "2024-morten"),
    ]

    html = render_landing_page(pages)

    assert html.index("Showcase Armies") < html.index("2025 Armies")
    assert html.index("2025 Armies") < html.index("2024 Armies")


def test_an_army_is_one_row_with_a_cell_per_product() -> None:
    """Each Army is a `<tr>`: its name, its Army Reference, its Order Cards."""
    pages = _army_pages("2025 Armies", "Geir Arne: Sabeltann", "2025-geir-arne")

    html = render_landing_page(pages)

    rows = re.findall(r"<tr>(.*?)</tr>", html, flags=re.DOTALL)
    army_rows = [row for row in rows if "Geir Arne: Sabeltann" in row]
    assert len(army_rows) == 1
    cells = re.findall(r"<td>(.*?)</td>", army_rows[0], flags=re.DOTALL)
    assert len(cells) == 3
    assert 'href="army-rules/2025-geir-arne.pdf"' in cells[1]
    assert 'href="army-rules/2025-geir-arne.html"' in cells[1]
    assert 'href="cards/2025-geir-arne.pdf"' in cells[2]
    assert 'href="cards/2025-geir-arne.html"' in cells[2]


def test_the_army_pack_renders_below_its_table_not_as_a_row() -> None:
    """A Pack's own document is a link under its table, not one of its Armies."""
    pages = [
        *_army_pages("2025 Armies", "Geir Arne: Sabeltann", "2025-geir-arne"),
        SitePage(
            product="army-pack",
            label="Steampunkfantasy Tournament 2025",
            fmt="pdf",
            relative_path="army-pack/2025.pdf",
            group="2025 Armies",
        ),
    ]

    html = render_landing_page(pages)

    assert "army-pack/2025.pdf" not in html[: html.index("</table>")]
    assert "army-pack/2025.pdf" in html[html.index("</table>") :]
    rows = re.findall(r"<tr>(.*?)</tr>", html, flags=re.DOTALL)
    assert not any("army-pack/2025.pdf" in row for row in rows)


def test_a_missing_product_leaves_an_empty_cell() -> None:
    """The page links what rendered; it never fabricates a link that did not."""
    pages = [
        SitePage(
            product="army-rules",
            label="Showcase Elf",
            fmt="pdf",
            relative_path="army-rules/showcase-elf.pdf",
            group="Showcase Armies",
        )
    ]

    html = render_landing_page(pages)

    assert "cards/showcase-elf" not in html
    assert "<td></td>" in html


def test_the_footer_links_the_repository() -> None:
    """A reader on the site can find the sources it was generated from."""
    html = render_landing_page([RULEBOOK])

    assert SOURCE_URL == "https://github.com/hssmalo/steampunkfantasy/tree/master/v3"
    assert f'href="{SOURCE_URL}"' in html
    assert "<footer>" in html


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


def test_escapes_untrusted_looking_content() -> None:
    """Labels, headings, and paths are HTML-escaped before being embedded."""
    pages = [
        SitePage(
            product="army-rules",
            label="<script>",
            fmt="pdf",
            relative_path="army-rules/x.pdf",
            group="<em>",
        )
    ]

    html = render_landing_page(pages)

    assert "<script>" not in html
    assert "&lt;script&gt;" in html
    assert "<em>" not in html
    assert "&lt;em&gt;" in html
