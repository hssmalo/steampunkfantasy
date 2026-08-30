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

from spf.armies import io
from spf.config import config
from spf.console import stderr, stdout
from spf.frontends.cli.render import (
    ARMY_PACK,
    ARMY_PACK_STEM,
    ARMY_RULES,
    CARDS,
    GENERAL_RULES,
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
from spf.render.rulebook import build_rulebook
from spf.rules import get_rulebook, rulebook_index_path

# The showcase pack is the site's one authored source of what to publish
# (ADR 0018, ADR 0022) -- the site contains exactly its Armies, no others.
SHOWCASE_PACK_PATH = "showcase/pack.toml"

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
}

# The Products a pack's table has one column of, in column order.
_ARMY_PRODUCTS = ("army-rules", "cards")

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
    group: str | None = None
    """The heading of the Army Pack section this page belongs under; `None` for
    a page that stands outside every pack, as the Rulebook does."""


def _format_links(pages: Sequence[SitePage]) -> str:
    """Render one link per Format, or nothing at all when none rendered."""
    return " ".join(
        f'<a href="{escape(page.relative_path)}">{escape(page.fmt)}</a>'
        for page in pages
    )


def _product_line(product: str, pages: Sequence[SitePage]) -> str:
    """Render a Product that stands outside a table as a labeled line."""
    title = _PRODUCT_TITLES.get(product, product)
    return f"<p>{escape(title)}: {_format_links(pages)}</p>"


def _render_section(heading: str, pages: Sequence[SitePage]) -> str:
    """Render one pack: a table of its Armies, then its Army Pack below."""
    armies: dict[str, dict[str, list[SitePage]]] = {}
    packs: dict[str, list[SitePage]] = {}
    for page in pages:
        if page.product == ARMY_PACK.name:
            packs.setdefault(page.product, []).append(page)
        else:
            armies.setdefault(page.label, {}).setdefault(page.product, []).append(page)

    headers = "".join(
        f"<th>{escape(_PRODUCT_TITLES.get(product, product))}</th>"
        for product in _ARMY_PRODUCTS
    )
    rows = [f"<tr><th>Army</th>{headers}</tr>"]
    for label, by_product in armies.items():
        # An Army the site did not fully render gets an empty cell: the page
        # cannot advertise a link to something that failed to render.
        cells = "".join(
            f"<td>{_format_links(by_product.get(product, []))}</td>"
            for product in _ARMY_PRODUCTS
        )
        rows.append(f"<tr><td>{escape(label)}</td>{cells}</tr>")

    table = "<table>\n" + "\n".join(rows) + "\n</table>"
    below = [
        _product_line(product, pack_pages) for product, pack_pages in packs.items()
    ]
    return "\n".join([f"<h2>{escape(heading)}</h2>", table, *below])


def render_landing_page(pages: Sequence[SitePage]) -> str:
    """Render a minimal HTML landing page linking every page, grouped by pack.

    One section per Army Pack, in the order the pages arrive — which is Site
    Index order. Pages belonging to no pack render above the first section.
    """
    ungrouped: dict[str, list[SitePage]] = {}
    groups: dict[str, list[SitePage]] = {}
    for page in pages:
        if page.group is None:
            ungrouped.setdefault(page.product, []).append(page)
        else:
            groups.setdefault(page.group, []).append(page)

    body = "\n".join(
        [
            *(
                _product_line(product, product_pages)
                for product, product_pages in ungrouped.items()
            ),
            *(
                _render_section(heading, group_pages)
                for heading, group_pages in groups.items()
            ),
        ]
    )
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


def render_site() -> None:
    """Render every published Product/Format into `output/`, plus a Landing Page.

    Builds the Rulebook, each showcase Army's Reference and Order Cards, and
    the Army Pack named by `armies/showcase/pack.toml`. Fails the whole build
    on any error rather than publishing a partial site -- a stale-but-complete
    site degrades safely, a silently incomplete one does not (extends ADR
    0022 from one Product to the whole site).
    """
    output_root = config.paths.output
    pack_path = config.paths.armies / SHOWCASE_PACK_PATH
    try:
        pack_index = io.get_army_pack(pack_path)
        armies = io.load_pack_armies(pack_index, base_dir=pack_path.parent)
        rulebook_path = rulebook_index_path(None)
        rulebook = build_rulebook(
            get_rulebook(rulebook_path), rules_dir=rulebook_path.parent
        )
    except (FileNotFoundError, ValueError) as err:
        stderr.print(f"[red]Error:[/] {err}")
        raise SystemExit(1) from None

    pages = _render_page(
        GENERAL_RULES,
        rulebook,
        name=RULEBOOK_STEM,
        label="Rulebook",
        output_root=output_root,
    )

    for entry, (label, army) in zip(pack_index.armies, armies, strict=True):
        stem = safe_stem(f"showcase/{entry.army}")
        page_label = f"{label}: {army.nick}" if label is not None else army.nick
        reference = build_reference(army, stem=stem, image_for=committed_image)
        pages += _render_page(
            ARMY_RULES, reference, name=stem, label=page_label, output_root=output_root
        )
        deck = build_deck(army, stem=stem, image_for=committed_image)
        pages += _render_page(
            CARDS, deck, name=stem, label=page_label, output_root=output_root
        )

    pack_stem = safe_stem(pack_path.resolve().parent.name) or ARMY_PACK_STEM
    pack = build_pack(
        armies, title=pack_index.title, stem=pack_stem, image_for=committed_image
    )
    pages += _render_page(
        ARMY_PACK, pack, name=pack_stem, label=pack_index.title, output_root=output_root
    )

    index_path = output_root / "index.html"
    index_path.write_text(render_landing_page(pages), encoding="utf-8")

    for page in pages:
        stdout.print(f"Wrote {output_root / page.relative_path}")
    stdout.print(f"Wrote {index_path}")


def add_commands(app: cyclopts.App) -> None:
    """Add the `spf render site` command to the CLI."""
    app.command(render_site, name="site")
