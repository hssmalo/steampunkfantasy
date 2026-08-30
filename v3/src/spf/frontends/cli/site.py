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

# Display order and heading for each Product's group on the Landing Page.
_PRODUCT_TITLES: dict[str, str] = {
    "general-rules": "Rulebook",
    "army-rules": "Army Reference",
    "cards": "Order Cards",
    "army-pack": "Army Pack",
}


@dataclass(frozen=True)
class SitePage:
    """One rendered file `render_site` wrote, for the Landing Page to link."""

    product: str
    label: str
    fmt: str
    relative_path: str


def render_landing_page(pages: Sequence[SitePage]) -> str:
    """Render a minimal HTML landing page linking every page, grouped by Product."""
    groups: dict[str, list[SitePage]] = {name: [] for name in _PRODUCT_TITLES}
    for page in pages:
        groups.setdefault(page.product, []).append(page)

    sections: list[str] = []
    for product, product_pages in groups.items():
        if not product_pages:
            continue
        labels: dict[str, list[SitePage]] = {}
        for page in product_pages:
            labels.setdefault(page.label, []).append(page)
        items = [
            f"<li>{escape(label)}: "
            + " ".join(
                f'<a href="{escape(page.relative_path)}">{escape(page.fmt)}</a>'
                for page in label_pages
            )
            + "</li>"
            for label, label_pages in labels.items()
        ]
        title = _PRODUCT_TITLES.get(product, product)
        sections.append(
            f"<h2>{escape(title)}</h2>\n<ul>\n" + "\n".join(items) + "\n</ul>"
        )

    body = "\n".join(sections)
    return (
        "<!doctype html>\n"
        '<html lang="en">\n<head>\n<meta charset="utf-8">\n'
        "<title>SteamPunkFantasy Reference</title>\n</head>\n<body>\n"
        "<h1>SteamPunkFantasy Reference</h1>\n"
        f"{body}\n"
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
