"""Presenting Special instances: signature interpolation and grouping (ADR 0024).

The data layer keeps N instances of an id and never joins two of them, because
joining their prose is a presentation decision. This is where that decision is
made, once, for every surface that prints an Army's Specials: the Army
Reference, the console rules view, and `spf special show`.

What a reader sees is a **heading** — the rule's name, or the instance's own
atmospheric one — and a **text**: the rule's signature filled in with this
instance's arguments, followed by whatever prose the instance adds about its
own occurrence.
"""

import re
from collections.abc import Callable
from typing import NamedTuple

from spf.registry import Registry, load_registry
from spf.schemas.rules import RuleRecord, SpecialRuleConfig
from spf.schemas.special import SpecialInstance, Specials

_PLACEHOLDER = re.compile(r"\{([A-Za-z_][A-Za-z0-9_]*)(\.id)?\}")
"""A signature's variable slot: `{N}`, or `{version.id}` for the raw ref."""

_GROUP = re.compile(r"\[[^][]*\]")
"""One bracketed group of a signature: `[{N}+]`, `[1 for {M}]`."""

_PROSE_SEPARATOR = ". "
"""Between a signature and the instance's own prose about its occurrence."""

_INSTANCE_SEPARATOR = "; "
"""Between the texts of several instances sharing one heading."""

_PREAMBLE_SEPARATOR = ": "
"""Between a preamble and the cases it scopes."""

_VALUES_SEPARATOR = " "
"""Between a case's own values and the prose saying when they apply."""

_CASE_SEPARATOR = ", "
"""Between two cases of one instance.

Lighter than the separator between instances, so the condition groups of a
rule carrying several case-shaped instances stay visibly apart.
"""


class SpecialLine(NamedTuple):
    """One line a reader is shown, and where its rule is written out.

    The anchor travels beside the name rather than as a finished link: the
    Markdown and LaTeX families need different link syntax from the same
    value, and a display name alone cannot address a rule.
    """

    name: str
    text: str
    anchor: str | None
    """Where this rule's Rules Reference entry sits, when there is one."""


def special_row(
    identifier: str, instance: SpecialInstance, *, registry: Registry
) -> tuple[str, str]:
    """Render one instance as the (heading, text) pair a reader is shown."""
    rule = registry.specials.get(identifier)
    heading = instance.name or (rule.name if rule is not None else identifier)
    if instance.cases:
        return heading, _cases(instance, rule, registry)
    signature = _signature(rule, instance.args, registry)
    prose = _prose(instance.text, instance.variant, rule)
    return heading, _join(_PROSE_SEPARATOR, signature, prose)


def _prose(
    text: str | None, variant: str | None, rule: SpecialRuleConfig | None
) -> str | None:
    """Resolve the prose slot, spelled inline or drawn from the rule's variants.

    Total by design (ADR 0031): an id resolving to nothing renders as no prose,
    because the load-time gate is what reports it and rendering must stay
    printable for a rule the registry does not hold at all.
    """
    if variant is None:
        return text
    return rule.variants.get(variant) if rule is not None else None


def _cases(
    instance: SpecialInstance, rule: SpecialRuleConfig | None, registry: Registry
) -> str:
    """Render a case-shaped instance: its preamble, then its cases (ADR 0030).

    Each case fills the signature with its own args over the instance's, so a
    value constant across the cases is written once. Cases that read alike are
    both printed: they are hand-written in one array, where a repeat is a typo
    the reader should see.
    """
    lines = [
        _join(
            _VALUES_SEPARATOR,
            _signature(rule, instance.args | case.args, registry),
            _prose(case.text, case.variant, rule),
        )
        for case in instance.cases
    ]
    preamble = _prose(instance.preamble, instance.variant, rule)
    return _join(_PREAMBLE_SEPARATOR, preamble, _join(_CASE_SEPARATOR, *lines))


def _signature(
    rule: RuleRecord | None, args: dict[str, int | str], registry: Registry
) -> str:
    """Fill in the rule's signature, or nothing at all for an unknown id."""
    return "" if rule is None else _interpolate(rule, args, registry)


def _join(separator: str, *parts: str | None) -> str:
    """Join the parts that are there, so an absent one leaves no separator."""
    return separator.join(part for part in parts if part)


def special_lines(
    specials: Specials,
    *,
    registry: Registry | None = None,
    anchor_for: Callable[[str], str | None] | None = None,
) -> list[SpecialLine]:
    """Render one slot's instances as lines, grouped by heading.

    N instances of an id become one line, in the order the ids were
    contributed. An atmospheric name is part of the grouping key rather than a
    detail of the first instance: two `to_hit` named apart are two lines,
    because collapsing them would print one flavor name over the other's rule.

    Instances that read exactly alike are printed once. Three Models of a Unit
    each granting the same Resistance say one thing between them, and the
    reader learns nothing from the second and third copy.

    `anchor_for` resolves an Identifier to its Rules Reference entry. Without
    one every line's `anchor` is `None`, which is what the console printing
    and a `--no-rules` document want.
    """
    registry = registry if registry is not None else load_registry()
    grouped: dict[tuple[str, str], dict[str, None]] = {}
    for identifier, instances in specials.items():
        for instance in instances:
            heading, text = special_row(identifier, instance, registry=registry)
            grouped.setdefault((identifier, heading), {})[text] = None
    return [
        SpecialLine(
            name=heading,
            text=_INSTANCE_SEPARATOR.join(text for text in texts if text),
            anchor=anchor_for(identifier) if anchor_for is not None else None,
        )
        for (identifier, heading), texts in grouped.items()
    ]


def _interpolate(
    rule: RuleRecord,
    args: dict[str, int | str],
    registry: Registry,
    seen: frozenset[str] = frozenset(),
) -> str:
    """Fill `rule`'s signature in with `args`.

    A bare `{var}` on a ref-valued argument renders the target's name, and the
    target's own signature after it: a ref's arguments travel with the ref, so
    the numbers an instance carries for the target print where the *target*
    declares them. `{var.id}` asks for the raw id instead.
    """
    if not rule.signature:
        return ""

    def keep(match: re.Match[str]) -> str:
        """Drop a group no argument fills, so an optional one reads as absent."""
        names = [name for name, _ in _PLACEHOLDER.findall(match.group(0))]
        unfilled = all(args.get(name) is None for name in names)
        return "" if names and unfilled else match.group(0)

    def fill(match: re.Match[str]) -> str:
        name, raw_id = match.group(1), match.group(2)
        value = args.get(name)
        if value is None:
            return match.group(0)  # an argument the instance never gave
        target = registry.record(value) if isinstance(value, str) else None
        if target is None:
            return str(value)
        if raw_id:
            return str(value).split(".", 1)[1]
        if value in seen:  # a ref cycle renders as a name, not forever
            return target.name
        nested = _interpolate(target, args, registry, seen | {str(value)})
        return f"{target.name}{nested}"

    return _PLACEHOLDER.sub(fill, _GROUP.sub(keep, rule.signature))
