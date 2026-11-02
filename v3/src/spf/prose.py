"""The placeholder grammar a signature and an instance's prose share (ADR 0037).

A `{N}` slot means the same thing wherever an **Instance** writes one: fill it
from that Instance's **Args**. The registry checks a placeholder is fillable,
rendering fills it, and lint compares two strings once filled — three modules
over one grammar, so it lives here rather than inside any one of them.

Filling yields linked text: the same words, with each Ref that printed still
attached to its span. The plain string is `str()` of that, so the two forms
cannot drift, and a surface that ignores the links degrades to text.

Prose may also author a **Rule Link** as `{label:<namespace>.<id>}` (ADR 0042).
Links parse before placeholders, so a placeholder in a label fills as text and
links never nest.
"""

import re
from collections.abc import Callable, Iterable, Iterator, Mapping
from dataclasses import dataclass, replace
from typing import TYPE_CHECKING, overload

from spf.schemas.rules import RuleRecord

if TYPE_CHECKING:
    from spf.registry import Registry

PLACEHOLDER = re.compile(r"\{([A-Za-z_][A-Za-z0-9_]*)(\.id)?\}")
"""A variable slot: `{N}`, or `{version.id}` for the raw ref."""

LINK = re.compile(
    r"\{((?:[^{}]|\{[A-Za-z_][A-Za-z0-9_]*(?:\.id)?\})+)"
    r":([a-z][a-z0-9_]*\.[a-z][a-z0-9_]*)\}"
)
"""An authored Rule Link. The Ref is anchored at the end, so a label may hold a
colon, and placeholders are the only braces it may hold."""

_LINK_SHAPED = re.compile(r"\{(?:[^{}]|\{[^{}]*\})*:[^{}]*\}")
"""Braces around a colon: what an author wrote when meaning a link."""

type AnchorOf = Callable[[str], str | None]
"""Resolves a Ref to its Rules Reference entry, or nothing."""

_GROUP = re.compile(r"\[[^][]*\]")
"""One bracketed group of a signature: `[{N}+]`, `[1 for {M}]`."""


def resolve(
    text: str | None, variant: str | None, variants: Mapping[str, str]
) -> str | None:
    """Resolve a prose slot, spelled inline or named from the pool (ADR 0032).

    Total by design: a name the pool does not hold resolves to no prose, so
    both the load-time gate and rendering can ask before it is reported.
    """
    return text if variant is None else variants.get(variant)


@dataclass(frozen=True)
class Span:
    """A run of printed text, and the Ref it names when it names one."""

    text: str
    ref: str | None = None
    anchor: str | None = None
    """Where the Ref's Rules Reference entry sits, once resolved against one."""


@dataclass(frozen=True)
class LinkedText:
    """Text whose spans may be **Rule Links**; compares by words and Refs alike."""

    spans: tuple[Span, ...] = ()

    @classmethod
    def join(cls, separator: str, parts: Iterable["LinkedText"]) -> "LinkedText":
        """Join `parts` with a plain `separator`, as `str.join` does."""
        spans: list[Span] = []
        for index, part in enumerate(parts):
            if index:
                spans.append(Span(separator))
            spans += part.spans
        return cls(_merged(spans))

    def resolved(self, anchor_of: AnchorOf) -> "LinkedText":
        """Anchor each span whose Ref has an entry; the rest stay plain text."""
        return LinkedText(
            tuple(
                replace(span, anchor=anchor_of(span.ref))
                if span.ref is not None
                else span
                for span in self.spans
            )
        )

    def __str__(self) -> str:
        """Return the words alone, which is what a surface without links prints."""
        return "".join(span.text for span in self.spans)

    def __bool__(self) -> bool:
        """Return whether anything prints."""
        return bool(self.spans)


def _merged(spans: Iterable[Span]) -> tuple[Span, ...]:
    """Drop empty spans and merge adjacent plain spans, so equal text compares equal."""
    merged: list[Span] = []
    for span in spans:
        if not span.text:
            continue
        if merged and span.ref is None and merged[-1].ref is None:
            merged[-1] = Span(merged[-1].text + span.text)
        else:
            merged.append(span)
    return tuple(merged)


def _pieces(raw: str) -> Iterator[tuple[str, str | None]]:
    """Split authored prose into `(text, ref)` runs, in order."""
    position = 0
    for match in LINK.finditer(raw):
        yield raw[position : match.start()], None
        yield match.group(1), match.group(2)
        position = match.end()
    yield raw[position:], None


def linked_prose(raw: str | None, anchor_of: AnchorOf | None = None) -> LinkedText:
    """Parse prose that has no Args to fill, so its `{N}` stay verbatim (ADR 0037).

    With `anchor_of`, each Rule Link is resolved against a Rules Reference.
    """
    if raw is None:
        return LinkedText()
    text = LinkedText(_merged(Span(*piece) for piece in _pieces(raw)))
    return text if anchor_of is None else text.resolved(anchor_of)


@overload
def plain(raw: str) -> str: ...
@overload
def plain(raw: None) -> None: ...
@overload
def plain(raw: str | None) -> str | None: ...
def plain(raw: str | None) -> str | None:
    """Reduce every authored Rule Link to its label, for a surface without links."""
    return None if raw is None else LINK.sub(r"\1", raw)


def link_refs(raw: str | None) -> list[str]:
    """List the Ref of each authored Rule Link in `raw`, in order."""
    return [] if raw is None else [match.group(2) for match in LINK.finditer(raw)]


def malformed_links(raw: str | None) -> list[str]:
    """List what `raw` writes as a link but the grammar does not accept."""
    return [] if raw is None else _LINK_SHAPED.findall(LINK.sub("", raw))


def writes_link(raw: str) -> bool:
    """Return whether `raw` writes anything shaped like a link, valid or not."""
    return _LINK_SHAPED.search(raw) is not None


def link_labels(raw: str) -> list[str]:
    """List the label of each authored Rule Link in `raw`, in order."""
    return [match.group(1) for match in LINK.finditer(raw)]


def fill_linked(
    template: str,
    args: dict[str, int | str],
    registry: "Registry",
    seen: frozenset[str] = frozenset(),
) -> LinkedText:
    """Fill every placeholder in `template` in with `args`.

    A bare `{var}` on a ref-valued argument renders the target's name, and the
    target's own signature after it: a ref's arguments travel with the ref, so
    the numbers an instance carries for the target print where the *target*
    declares them. `{var.id}` asks for the raw id instead.
    """
    spans: list[Span] = []
    for text, ref in _pieces(template):
        filled = _placeholders_filled(text, args, registry, seen)
        if ref is None:
            spans += filled
        else:
            spans.append(Span("".join(span.text for span in filled), ref=ref))
    return LinkedText(_merged(spans))


def _placeholders_filled(
    text: str,
    args: dict[str, int | str],
    registry: "Registry",
    seen: frozenset[str],
) -> list[Span]:
    """Return the spans of a run of `text`, each placeholder filled."""
    spans: list[Span] = []
    position = 0
    for match in PLACEHOLDER.finditer(text):
        spans.append(Span(text[position : match.start()]))
        spans += _filled(match, args, registry, seen)
        position = match.end()
    spans.append(Span(text[position:]))
    return spans


def _filled(
    match: re.Match[str],
    args: dict[str, int | str],
    registry: "Registry",
    seen: frozenset[str],
) -> Iterator[Span]:
    """Yield the spans one placeholder prints."""
    name, raw_id = match.group(1), match.group(2)
    value = args.get(name)
    if value is None:
        yield Span(match.group(0))  # an argument the instance never gave
        return
    target = registry.record(value) if isinstance(value, str) else None
    if target is None:
        yield Span(str(value))
    elif raw_id:
        yield Span(str(value).split(".", 1)[1])
    else:
        yield Span(target.name, ref=str(value))
        if value not in seen:  # a ref cycle renders as a name, not forever
            nested = interpolate_linked(target, args, registry, seen | {str(value)})
            yield from nested.spans


def fill(template: str, args: dict[str, int | str], registry: "Registry") -> str:
    """Fill `template` as `fill_linked` does, keeping only the words."""
    return str(fill_linked(template, args, registry))


def interpolate_linked(
    rule: RuleRecord,
    args: dict[str, int | str],
    registry: "Registry",
    seen: frozenset[str] = frozenset(),
) -> LinkedText:
    """Fill `rule`'s signature in with `args`.

    Only a signature has groups to elide: square brackets in prose are square
    brackets, so the elision stays here rather than in `fill_linked` (ADR 0037).
    """
    if not rule.signature:
        return LinkedText()
    return fill_linked(_elide(rule.signature, args), args, registry, seen)


def _elide(signature: str, args: dict[str, int | str]) -> str:
    """Drop each group no argument fills, so an optional one reads as absent."""

    def keep(match: re.Match[str]) -> str:
        names = [name for name, _ in PLACEHOLDER.findall(match.group(0))]
        unfilled = all(args.get(name) is None for name in names)
        return "" if names and unfilled else match.group(0)

    return _GROUP.sub(keep, signature)
