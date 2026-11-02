"""The placeholder grammar a signature and an instance's prose share (ADR 0037).

A `{N}` slot means the same thing wherever an **Instance** writes one: fill it
from that Instance's **Args**. The registry checks a placeholder is fillable,
rendering fills it, and lint compares two strings once filled — three modules
over one grammar, so it lives here rather than inside any one of them.

Filling yields **linked text**: the same words, with each Ref that printed still
attached to its span. The plain string is `str()` of that, so the two forms
cannot drift, and a surface that ignores the links degrades to text.
"""

import re
from collections.abc import Callable, Iterable, Iterator, Mapping
from dataclasses import dataclass, replace
from typing import TYPE_CHECKING

from spf.schemas.rules import RuleRecord

if TYPE_CHECKING:
    from spf.registry import Registry

PLACEHOLDER = re.compile(r"\{([A-Za-z_][A-Za-z0-9_]*)(\.id)?\}")
"""A variable slot: `{N}`, or `{version.id}` for the raw ref."""

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
    def plain(cls, text: str) -> "LinkedText":
        """Wrap `text` that names no Ref."""
        return cls(_merged([Span(text)]))

    @classmethod
    def join(cls, separator: str, parts: Iterable["LinkedText"]) -> "LinkedText":
        """Join `parts` with a plain `separator`, as `str.join` does."""
        spans: list[Span] = []
        for index, part in enumerate(parts):
            if index:
                spans.append(Span(separator))
            spans += part.spans
        return cls(_merged(spans))

    def resolved(self, anchor_of: Callable[[str], str | None]) -> "LinkedText":
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
    position = 0
    for match in PLACEHOLDER.finditer(template):
        spans.append(Span(template[position : match.start()]))
        spans += _filled(match, args, registry, seen)
        position = match.end()
    spans.append(Span(template[position:]))
    return LinkedText(_merged(spans))


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


def fill(
    template: str,
    args: dict[str, int | str],
    registry: "Registry",
    seen: frozenset[str] = frozenset(),
) -> str:
    """Fill `template` as `fill_linked` does, keeping only the words."""
    return str(fill_linked(template, args, registry, seen))


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


def interpolate(
    rule: RuleRecord,
    args: dict[str, int | str],
    registry: "Registry",
    seen: frozenset[str] = frozenset(),
) -> str:
    """Fill `rule`'s signature as `interpolate_linked` does, keeping only the words."""
    return str(interpolate_linked(rule, args, registry, seen))


def _elide(signature: str, args: dict[str, int | str]) -> str:
    """Drop each group no argument fills, so an optional one reads as absent."""

    def keep(match: re.Match[str]) -> str:
        names = [name for name, _ in PLACEHOLDER.findall(match.group(0))]
        unfilled = all(args.get(name) is None for name in names)
        return "" if names and unfilled else match.group(0)

    return _GROUP.sub(keep, signature)
