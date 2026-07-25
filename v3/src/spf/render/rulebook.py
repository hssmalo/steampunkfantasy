"""Rulebook view-model: turn an authored Index into the object templates read.

The Rulebook is not "every file in `rules/`" — it is an ordered, authored Index
naming a **Section Kind** per Section (ADR 0018). A Kind binds a source shape to
one parser here and one template partial per family
(`templates/<family>/general-rules/<kind>.<ext>.jinja`, picked by name, nothing
to register).

The registry deliberately mirrors `spf.render.products` and
`spf.render.formats`: same record-plus-dict shape, same "Unknown x; known xs"
failure. Adding a Kind is a registration, never a change to `build_rulebook` or
to `main.<ext>.jinja`.

A bad Index **fails the build**. A Rulebook silently missing a chapter is worse
than one that refuses to build, so every failure names the Section's 1-based
position — what a human counts down the Index file.
"""

import re
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

from spf.schemas.rulebook import RulebookConfig

_H1 = re.compile(r"^#\s")
_NON_SLUG = re.compile(r"[^a-z0-9]+")


@dataclass(frozen=True)
class SectionKind:
    """A registered kind of Rulebook Section: how its source is read."""

    name: str
    parse: Callable[[Path], object]
    """Source path -> the Section's body, in whatever shape the Kind's partials
    expect. Plan 2 widens this to also take a shared rules context, so that a
    Kind can resolve cross-references; keeping the type here makes that a
    one-line change."""


KINDS: dict[str, SectionKind] = {}


def register_kind(kind: SectionKind) -> SectionKind:
    """Register a Section Kind under its name and return it."""
    KINDS[kind.name] = kind
    return kind


def get_kind(name: str) -> SectionKind:
    """Look up a registered Section Kind by name."""
    try:
        return KINDS[name]
    except KeyError:
        known = ", ".join(KINDS) or "(none registered)"
        msg = f"Unknown kind {name!r}; known kinds: {known}"
        raise ValueError(msg) from None


def parse_markdown(path: Path) -> str:
    """Read a free-text Markdown Section, dropping its H1 lines.

    A Section's heading always comes from the Index's `title`, so an H1 in the
    source would duplicate it one level too high. Dropping happens here because
    it is family-independent; mapping the *remaining* levels is each family's
    business (`shift_headings` and `md_to_latex`).
    """
    lines = path.read_text(encoding="utf-8").splitlines(keepends=True)
    return "".join(line for line in lines if not _H1.match(line))


MARKDOWN = register_kind(SectionKind(name="markdown", parse=parse_markdown))


@dataclass(frozen=True)
class Section:
    """One resolved Section: its rendered heading and its parsed body."""

    kind: str
    """Names the partial that renders it: `general-rules/<kind>.<ext>.jinja`."""

    title: str
    anchor: str
    """Slug of the title, unique within the Rulebook, for the Markdown TOC."""

    body: object
    """Whatever the Kind's parser returned."""


@dataclass(frozen=True)
class Rulebook:
    """A whole Rulebook: a document title and its ordered Sections."""

    title: str
    sections: list[Section]


def _slug(title: str) -> str:
    """Reduce `title` to a lowercase, dash-separated anchor."""
    return _NON_SLUG.sub("-", title.lower()).strip("-")


def _anchor(title: str, taken: set[str]) -> str:
    """Return a slug of `title` not already in `taken`.

    Two Sections may legitimately share a title, but not an anchor: every link
    to the second would otherwise land on the first.
    """
    slug = _slug(title)
    anchor = slug
    suffix = 1
    while anchor in taken:
        suffix += 1
        anchor = f"{slug}-{suffix}"
    taken.add(anchor)
    return anchor


def build_rulebook(index: RulebookConfig, *, rules_dir: Path) -> Rulebook:
    """Resolve an Index into the Rulebook object the templates render.

    Each Section's `kind` is looked up, its `source` located under `rules_dir`,
    and the Kind's parser run over it. An unknown Kind raises `ValueError` and a
    missing source `FileNotFoundError` — both naming the Section's position.
    """
    sections: list[Section] = []
    taken: set[str] = set()
    for position, config in enumerate(index.sections, start=1):
        where = f"Rulebook Index section {position}"
        try:
            kind = get_kind(config.kind)
        except ValueError as err:
            msg = f"{where}: {err}"
            raise ValueError(msg) from None

        source = rules_dir / config.source
        if not source.is_file():
            msg = f"{where}: source {config.source!r} not found in {rules_dir}"
            raise FileNotFoundError(msg)

        sections.append(
            Section(
                kind=kind.name,
                title=config.title,
                anchor=_anchor(config.title, taken),
                body=kind.parse(source),
            )
        )
    return Rulebook(title=index.title, sections=sections)
