"""Build the published site: every Product/Format `render_site` writes.

Plus a generated Landing Page.

The Landing Page is *not* a Product (`CONTEXT.md`): it is a build-time artifact
over what actually got rendered, not a source-of-truth object bound to a
template family. Keeping it here, rather than in `spf/render/`, keeps that
package's contract "Products to Formats" exactly.
"""

from collections.abc import Sequence
from dataclasses import dataclass
from html import escape
from pathlib import Path

import cyclopts

from spf import races
from spf.armies import io
from spf.armies.army import Army
from spf.config import config
from spf.console import stderr, stdout
from spf.frontends.cli.render import (
    ARMY_PACK,
    ARMY_PACK_STEM,
    ARMY_RULES,
    CARDS,
    GENERAL_RULES,
    RACE_OVERVIEW,
    RULEBOOK_STEM,
    safe_stem,
)
from spf.render import render
from spf.render.army_pack import build_pack
from spf.render.army_rules import build_reference
from spf.render.cards import build_deck
from spf.render.formats import get_format
from spf.render.images import committed_image
from spf.render.products import Product
from spf.render.race_overview import build_overview
from spf.render.rulebook import build_rulebook
from spf.rules import get_rulebook, rulebook_index_path
from spf.schemas import type_aliases as t
from spf.schemas.army_pack import ArmyPackConfig
from spf.schemas.race import RaceConfig
from spf.schemas.site import SiteConfig, SitePackConfig

# The Site Index is the site's one authored source of what to publish: the
# Army Packs and Races it names, and no others (ADR 0018, ADR 0028, ADR 0035).
SITE_INDEX_PATH = "site.toml"

SITE_FORMATS = ("pdf", "html")

# Where the sources the site is generated from actually live.
SOURCE_URL = "https://github.com/hssmalo/steampunkfantasy/tree/master/v3"

# Heading for each Product on the Landing Page: a column header inside a
# pack's table, a line label for the Products that stand outside one.
_PRODUCT_TITLES: dict[str, str] = {
    "general-rules": "Rulebook",
    "army-rules": "Army Reference",
    "cards": "Order Cards",
    "army-pack": "Army Pack",
    "race-overview": "Race Overview",
}

# The Products a pack's table has one column of, in column order.
_ARMY_PRODUCTS = (ARMY_RULES.name, CARDS.name)

_STYLE = """\
body {
  font-family: system-ui, -apple-system, "Segoe UI", Roboto, sans-serif;
  line-height: 1.5;
  max-width: 48rem;
  margin: 0 auto;
  padding: 2rem 1rem;
}
table {
  border-collapse: collapse;
  width: 100%;
}
th, td {
  border: 1px solid #ccc;
  padding: 0.35rem 0.6rem;
  text-align: left;
}
th {
  background: #f4f4f4;
}
footer {
  border-top: 1px solid #ccc;
  margin-top: 3rem;
  padding-top: 1rem;
  color: #666;
}\
"""


@dataclass(frozen=True)
class SitePage:
    """One rendered file `render_site` wrote, for the Landing Page to link."""

    product: str
    label: str
    fmt: str
    relative_path: str


@dataclass(frozen=True)
class SiteRow:
    """One row of a section's table: a labeled thing and its Products."""

    label: str
    cells: tuple[tuple[SitePage, ...], ...]
    """One cell of pages per column after the label column."""


@dataclass(frozen=True)
class SiteLine:
    """A labeled line of links standing outside a table."""

    label: str
    pages: tuple[SitePage, ...]


@dataclass(frozen=True)
class SiteSection:
    """One Landing Page section: an optional heading, a table, trailing lines.

    Deliberately generic. The Landing Page knows nothing about Army Packs or
    Races; the builders below hold that knowledge, so a further kind of section
    is a further builder rather than an edit to the renderer (ADR 0035).
    """

    heading: str | None
    columns: tuple[str, ...]
    """The full header row, the label column first; empty renders no table."""

    rows: tuple[SiteRow, ...]
    lines: tuple[SiteLine, ...]


def _format_links(pages: Sequence[SitePage]) -> str:
    """Render one link per Format, or nothing at all when none rendered."""
    return " ".join(
        f'<a href="{escape(page.relative_path)}">{escape(page.fmt)}</a>'
        for page in pages
    )


def _product_title(product: str) -> str:
    """Give the heading a Product appears under, or its own name if it has none."""
    return _PRODUCT_TITLES.get(product, product)


def loose_section(product: str, pages: Sequence[SitePage]) -> SiteSection:
    """Build the section for a Product that stands outside every table."""
    return SiteSection(
        heading=None,
        columns=(),
        rows=(),
        lines=(SiteLine(label=_product_title(product), pages=tuple(pages)),),
    )


def pack_section(
    heading: str, army_pages: Sequence[SitePage], pack_pages: Sequence[SitePage]
) -> SiteSection:
    """Build one Army Pack's section: a row per Army, the Pack document below."""
    armies: dict[str, dict[str, list[SitePage]]] = {}
    for page in army_pages:
        armies.setdefault(page.label, {}).setdefault(page.product, []).append(page)

    rows = tuple(
        SiteRow(
            label=label,
            # An Army the site did not fully render gets an empty cell: the
            # page cannot advertise a link to something that failed to render.
            cells=tuple(
                tuple(by_product.get(product, [])) for product in _ARMY_PRODUCTS
            ),
        )
        for label, by_product in armies.items()
    )
    lines = (
        (SiteLine(label=_product_title(ARMY_PACK.name), pages=tuple(pack_pages)),)
        if pack_pages
        else ()
    )
    return SiteSection(
        heading=heading,
        columns=("Army", *(_product_title(p) for p in _ARMY_PRODUCTS)),
        rows=rows,
        lines=lines,
    )


def race_section(heading: str, pages: Sequence[SitePage]) -> SiteSection:
    """Build the Races section: one Race Overview column, one row per Race."""
    by_race: dict[str, list[SitePage]] = {}
    for page in pages:
        by_race.setdefault(page.label, []).append(page)

    return SiteSection(
        heading=heading,
        columns=("Race", _product_title(RACE_OVERVIEW.name)),
        rows=tuple(
            SiteRow(label=label, cells=(tuple(race_pages),))
            for label, race_pages in by_race.items()
        ),
        lines=(),
    )


def _render_table(section: SiteSection) -> str:
    """Render a section's table, header row and all, even with no rows."""
    headers = "".join(f"<th>{escape(column)}</th>" for column in section.columns)
    rows = [f"<tr>{headers}</tr>"]
    for row in section.rows:
        cells = "".join(f"<td>{_format_links(cell)}</td>" for cell in row.cells)
        rows.append(f"<tr><td>{escape(row.label)}</td>{cells}</tr>")
    return "<table>\n" + "\n".join(rows) + "\n</table>"


def _render_section(section: SiteSection) -> str:
    """Render one section: its heading, its table, then its trailing lines."""
    parts = []
    if section.heading is not None:
        parts.append(f"<h2>{escape(section.heading)}</h2>")
    if section.columns:
        parts.append(_render_table(section))
    parts += [
        f"<p>{escape(line.label)}: {_format_links(line.pages)}</p>"
        for line in section.lines
    ]
    return "\n".join(parts)


def render_landing_page(sections: Sequence[SiteSection]) -> str:
    """Render a minimal HTML landing page from already-built sections.

    Sections render in the order given — which is the order `render_site` chose
    — and this function neither re-sorts them nor asks what they contain.
    """
    body = "\n".join(_render_section(section) for section in sections)
    return (
        "<!doctype html>\n"
        '<html lang="en">\n<head>\n<meta charset="utf-8">\n'
        "<title>SteamPunkFantasy Reference</title>\n"
        f"<style>\n{_STYLE}\n</style>\n</head>\n<body>\n"
        "<h1>SteamPunkFantasy Reference</h1>\n"
        f"{body}\n"
        f'<footer><a href="{SOURCE_URL}">Source on GitHub</a></footer>\n'
        "</body>\n</html>\n"
    )


def _section_pages(section: SiteSection) -> list[SitePage]:
    """List every page a section links, in the order it links them."""
    return [
        *(page for row in section.rows for cell in row.cells for page in cell),
        *(page for line in section.lines for page in line.pages),
    ]


def _render_page(
    product: Product,
    source: object,
    *,
    name: str,
    label: str,
    output_root: Path,
) -> list[SitePage]:
    """Render `source` to every Site Format and return one `SitePage` each."""
    pages = []
    for fmt_name in SITE_FORMATS:
        fmt = get_format(fmt_name)
        out = render(product, source, fmt=fmt, name=name, output_root=output_root)
        pages.append(
            SitePage(
                product=product.name,
                label=label,
                fmt=fmt_name,
                relative_path=str(out.relative_to(output_root)),
            )
        )
    return pages


@dataclass(frozen=True)
class _LoadedPack:
    """One Site Index entry, with the Army Pack Index and Armies it resolved to."""

    entry: SitePackConfig
    index: ArmyPackConfig
    armies: list[tuple[str | None, Army]]


def _load_packs(site_index: SiteConfig) -> list[_LoadedPack]:
    """Load every Army Pack the Site Index names, in Index order."""
    packs = []
    for entry in site_index.packs:
        path = config.paths.armies / entry.pack / "pack.toml"
        pack_index = io.get_army_pack(path)
        armies = io.load_pack_armies(pack_index, base_dir=path.parent)
        packs.append(_LoadedPack(entry=entry, index=pack_index, armies=armies))
    return packs


def _load_races(site_index: SiteConfig) -> list[tuple[t.RaceName, RaceConfig]]:
    """Load every Race the Site Index names, in Index order.

    Up front, with the packs: a Race the index names but disk lacks must fail
    the build before anything renders, not midway through.
    """
    if site_index.races is None:
        return []
    return [(race, races.get_race(race)) for race in site_index.races.publish]


def _render_races(
    heading: str,
    loaded: Sequence[tuple[t.RaceName, RaceConfig]],
    *,
    output_root: Path,
) -> SiteSection:
    """Render a Race Overview per named Race and build the Races section."""
    pages: list[SitePage] = []
    for race, race_config in loaded:
        # The Race Name is the stem: it is the name of the TOML file the
        # catalogue was read from, so it needs no slugifying.
        overview = build_overview(race_config, stem=race, image_for=committed_image)
        pages += _render_page(
            RACE_OVERVIEW,
            overview,
            name=race,
            label=race_config.races[race].name,
            output_root=output_root,
        )
    return race_section(heading, pages)


def _render_pack(pack: _LoadedPack, *, output_root: Path) -> SiteSection:
    """Render one pack: an Army Reference and Order Cards each, then the Pack."""
    army_pages: list[SitePage] = []
    for entry, (label, army) in zip(pack.index.armies, pack.armies, strict=True):
        # The pack directory is part of the stem: the same player fields an
        # Army in more than one tournament, and their renders must not collide.
        stem = safe_stem(f"{pack.entry.pack}/{entry.army}")
        page_label = f"{label}: {army.nick}" if label is not None else army.nick
        reference = build_reference(army, stem=stem, image_for=committed_image)
        army_pages += _render_page(
            ARMY_RULES,
            reference,
            name=stem,
            label=page_label,
            output_root=output_root,
        )
        deck = build_deck(army, stem=stem, image_for=committed_image)
        army_pages += _render_page(
            CARDS, deck, name=stem, label=page_label, output_root=output_root
        )

    pack_stem = safe_stem(pack.entry.pack) or ARMY_PACK_STEM
    document = build_pack(
        pack.armies, title=pack.index.title, stem=pack_stem, image_for=committed_image
    )
    pack_pages = _render_page(
        ARMY_PACK,
        document,
        name=pack_stem,
        label=pack.index.title,
        output_root=output_root,
    )
    return pack_section(pack.entry.heading, army_pages, pack_pages)


def render_site() -> None:
    """Render every published Product/Format into `output/`, plus a Landing Page.

    Builds the Rulebook, then a Race Overview per Race the Site Index names,
    then every Army Pack it names: each Army's Reference and Order Cards, and
    the Pack document itself. Fails the whole
    build on any error rather than publishing a partial site -- a
    stale-but-complete site degrades safely, a silently incomplete one does not
    (extends ADR 0022 from one Product to the whole site).
    """
    output_root = config.paths.output
    try:
        site_index = io.get_site_index(config.paths.armies / SITE_INDEX_PATH)
        packs = _load_packs(site_index)
        loaded_races = _load_races(site_index)
        rulebook_path = rulebook_index_path(None)
        rulebook = build_rulebook(
            get_rulebook(rulebook_path), rules_dir=rulebook_path.parent
        )
    except (FileNotFoundError, ValueError) as err:
        stderr.print(f"[red]Error:[/] {err}")
        raise SystemExit(1) from None

    rulebook_pages = _render_page(
        GENERAL_RULES,
        rulebook,
        name=RULEBOOK_STEM,
        label=_product_title(GENERAL_RULES.name),
        output_root=output_root,
    )
    # Rules, then what a player can field, then what players did field.
    sections = [loose_section(GENERAL_RULES.name, rulebook_pages)]
    if site_index.races is not None:
        sections.append(
            _render_races(
                site_index.races.heading, loaded_races, output_root=output_root
            )
        )
    sections += [_render_pack(pack, output_root=output_root) for pack in packs]

    index_path = output_root / "index.html"
    index_path.write_text(render_landing_page(sections), encoding="utf-8")

    for page in [page for section in sections for page in _section_pages(section)]:
        stdout.print(f"Wrote {output_root / page.relative_path}")
    stdout.print(f"Wrote {index_path}")


def add_commands(app: cyclopts.App) -> None:
    """Add the `spf render site` command to the CLI."""
    app.command(render_site, name="site")
