"""Presenting Special instances: interpolation and grouping (ADR 0024).

The data layer keeps N instances of an id and never joins two of them, because
joining their prose is a presentation decision. This is where that decision is
made, once, for every surface that prints an Army's Specials: the Army
Reference, the console rules view, and `spf special show`.

What a reader sees is a **heading** — the rule's name, or the instance's own
atmospheric one — and a **text**: the rule's signature filled in with this
instance's arguments, followed by whatever prose the instance adds about its
own occurrence.
"""

from collections.abc import Callable
from typing import NamedTuple

from spf.prose import fill, interpolate
from spf.registry import Registry, load_registry
from spf.schemas.rules import RuleRecord, SpecialRuleConfig
from spf.schemas.special import SpecialInstance, Specials

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
    prose = _prose(
        instance.text,
        instance.variant,
        rule=rule,
        args=instance.args,
        registry=registry,
    )
    return heading, _join(_PROSE_SEPARATOR, signature, prose)


def _prose(
    text: str | None,
    variant: str | None,
    *,
    rule: SpecialRuleConfig | None,
    args: dict[str, int | str],
    registry: Registry,
) -> str | None:
    """Resolve the prose slot and fill its placeholders from `args` (ADR 0037).

    Total by design (ADR 0032): an id resolving to nothing renders as no prose,
    because the load-time gate is what reports it and rendering must stay
    printable for a rule the registry does not hold at all.
    """
    resolved = text if variant is None else _variant(variant, rule)
    return None if resolved is None else fill(resolved, args, registry)


def _variant(variant: str, rule: SpecialRuleConfig | None) -> str | None:
    """Look up the prose a named variant spells, or nothing without one."""
    return rule.variants.get(variant) if rule is not None else None


def _cases(
    instance: SpecialInstance, rule: SpecialRuleConfig | None, registry: Registry
) -> str:
    """Render a case-shaped instance: its preamble, then its cases (ADR 0030).

    Each case fills the signature and its own prose with its own args over the
    instance's, so a value constant across the cases is written once. A
    preamble scopes every case, so it sees only the instance's own (ADR 0037).
    Cases that read alike are both printed: they are hand-written in one array,
    where a repeat is a typo the reader should see.
    """
    lines = [
        _join(
            _VALUES_SEPARATOR,
            _signature(rule, instance.args | case.args, registry),
            _prose(
                case.text,
                case.variant,
                rule=rule,
                args=instance.args | case.args,
                registry=registry,
            ),
        )
        for case in instance.cases
    ]
    preamble = _prose(
        instance.preamble,
        instance.variant,
        rule=rule,
        args=instance.args,
        registry=registry,
    )
    return _join(_PREAMBLE_SEPARATOR, preamble, _join(_CASE_SEPARATOR, *lines))


def _signature(
    rule: RuleRecord | None, args: dict[str, int | str], registry: Registry
) -> str:
    """Fill in the rule's signature, or nothing at all for an unknown id."""
    return "" if rule is None else interpolate(rule, args, registry)


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
