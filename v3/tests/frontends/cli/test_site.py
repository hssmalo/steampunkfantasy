"""Tests for the Site Index HTML generator.

`render_site_index` is a pure function over already-rendered pages, so these
build `SitePage`s by hand rather than rendering anything for real.
"""

from spf.frontends.cli.site import SitePage, render_site_index


def test_links_every_page() -> None:
    """Each page's relative path appears as a link target."""
    pages = [
        SitePage(
            product="general-rules",
            label="Rulebook",
            fmt="pdf",
            relative_path="general-rules/rulebook.pdf",
        ),
        SitePage(
            product="army-rules",
            label="showcase-elf",
            fmt="html",
            relative_path="army-rules/showcase-elf.html",
        ),
    ]

    html = render_site_index(pages)

    assert 'href="general-rules/rulebook.pdf"' in html
    assert 'href="army-rules/showcase-elf.html"' in html


def test_groups_by_product_in_a_fixed_order() -> None:
    """Product groups appear in a fixed order regardless of input order."""
    pages = [
        SitePage(product="army-pack", label="showcase", fmt="pdf", relative_path="p"),
        SitePage(
            product="general-rules", label="Rulebook", fmt="pdf", relative_path="r"
        ),
    ]

    html = render_site_index(pages)

    assert html.index("Rulebook") < html.index("Army Pack")


def test_a_product_with_no_pages_has_no_section() -> None:
    """Only Products that actually built pages get a heading."""
    pages = [
        SitePage(
            product="general-rules", label="Rulebook", fmt="pdf", relative_path="r"
        )
    ]

    html = render_site_index(pages)

    assert "Order Cards" not in html


def test_escapes_untrusted_looking_content() -> None:
    """Labels and paths are HTML-escaped before being embedded."""
    pages = [
        SitePage(
            product="army-rules",
            label="<script>",
            fmt="pdf",
            relative_path="army-rules/x.pdf",
        )
    ]

    html = render_site_index(pages)

    assert "<script>" not in html
    assert "&lt;script&gt;" in html
