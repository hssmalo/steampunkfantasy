"""Shared anchor-slugging for Markdown tables of contents.

Both the Rulebook (ADR 0018) and the Army Pack build a Markdown contents list
of links to `<a id>` anchors, one per titled entry. This is the one place that
turns a title into a slug and disambiguates collisions, so the two Products
can never drift into different collision-numbering schemes.
"""

import re

_NON_SLUG = re.compile(r"[^a-z0-9]+")


def slug(title: str) -> str:
    """Reduce `title` to a lowercase, dash-separated anchor."""
    return _NON_SLUG.sub("-", title.lower()).strip("-")


def anchor(title: str, taken: set[str]) -> str:
    """Return a slug of `title` not already in `taken`.

    Two entries may legitimately share a title, but not an anchor: every link
    to the second would otherwise land on the first.
    """
    base = slug(title)
    candidate = base
    suffix = 1
    while candidate in taken:
        suffix += 1
        candidate = f"{base}-{suffix}"
    taken.add(candidate)
    return candidate
