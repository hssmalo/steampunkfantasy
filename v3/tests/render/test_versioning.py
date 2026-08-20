"""Every rendered document carries the version of `spf` that produced it.

Driven through the CLI render commands, so these exercise the real templates
rather than the fixtures under `tests/fixtures/templates`.
"""

from collections.abc import Callable
from pathlib import Path

import pytest

from spf.frontends.cli.render import (
    RenderOpts,
    render_army_pack,
    render_army_rules,
    render_cards,
    render_general_rules,
)

DEMO_ARMY = "demo"

Renderer = Callable[[str, Path], None]


def _cards(fmt: str, out: Path) -> None:
    render_cards(DEMO_ARMY, opts=RenderOpts(format=fmt, out=out, no_images=True))


def _army_rules(fmt: str, out: Path) -> None:
    render_army_rules(DEMO_ARMY, opts=RenderOpts(format=fmt, out=out, no_images=True))


def _army_pack(fmt: str, out: Path) -> None:
    render_army_pack(DEMO_ARMY, opts=RenderOpts(format=fmt, out=out, no_images=True))


def _general_rules(fmt: str, out: Path) -> None:
    render_general_rules(opts=RenderOpts(format=fmt, out=out, no_images=True))


PRODUCT_RENDERERS: dict[str, Renderer] = {
    "cards": _cards,
    "army-rules": _army_rules,
    "army-pack": _army_pack,
    "general-rules": _general_rules,
}

# The three page-based documents share the `fancyhdr` footer; Order Cards stamp
# the version in flacards' own back-right slot instead.
PAGED_PRODUCTS = ["army-rules", "army-pack", "general-rules"]


def _render(product: str, fmt: str, tmp_path: Path) -> str:
    out = tmp_path / f"out.{'tex' if fmt == 'latex' else 'md'}"
    PRODUCT_RENDERERS[product](fmt, out)
    return out.read_text(encoding="utf-8")


@pytest.mark.parametrize("product", list(PRODUCT_RENDERERS))
@pytest.mark.parametrize("fmt", ["latex", "markdown"])
def test_rendered_document_stamps_the_version(
    tmp_path: Path, pinned_version: str, product: str, fmt: str
) -> None:
    assert f"v{pinned_version}" in _render(product, fmt, tmp_path)


@pytest.mark.parametrize("product", PAGED_PRODUCTS)
def test_latex_stamps_the_version_in_the_page_footer(
    tmp_path: Path, pinned_version: str, product: str
) -> None:
    text = _render(product, "latex", tmp_path)

    assert r"\usepackage{fancyhdr}" in text
    assert rf"\fancyfoot[R]{{\tiny v{pinned_version}}}" in text
    # `\maketitle` switches page 1 to `plain`, which would otherwise drop the
    # footer from exactly the page most likely to be looked at.
    assert r"\fancypagestyle{plain}" in text


@pytest.mark.parametrize("product", PAGED_PRODUCTS)
def test_latex_footer_keeps_the_page_number(tmp_path: Path, product: str) -> None:
    # `fancyhdr` starts from an empty footer, so the page number `article`
    # prints by default — and every table of contents points at — has to be
    # put back explicitly.
    assert r"\fancyfoot[C]{\thepage}" in _render(product, "latex", tmp_path)


@pytest.mark.parametrize("product", PAGED_PRODUCTS)
def test_latex_documents_show_the_render_date(tmp_path: Path, product: str) -> None:
    # An empty `\date{}` blanks the title-block date; all three documents let
    # LaTeX default to `\today` instead.
    assert r"\date{}" not in _render(product, "latex", tmp_path)


def test_cards_latex_stamps_the_version_on_the_card_back(
    tmp_path: Path, pinned_version: str
) -> None:
    text = _render("cards", "latex", tmp_path)

    assert rf"\renewcommand{{\brfoot}}{{\tiny v{pinned_version}}}" in text
