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

from typing import NamedTuple

from spf.prose import (
    AnchorOf,
    LinkedText,
    fill_linked,
    interpolate_linked,
    resolve,
)
from spf.registry import SPECIAL, Registry, load_registry
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
    text: LinkedText
    anchor: str | None
    """Where this rule's Rules Reference entry sits, when there is one."""


def special_row(
    identifier: str, instance: SpecialInstance, *, registry: Registry
) -> tuple[str, str]:
    """Render one instance as the (heading, text) pair a reader is shown."""
    heading, text = _linked_row(identifier, instance, registry=registry)
    return heading, str(text)


def _linked_row(
    identifier: str, instance: SpecialInstance, *, registry: Registry
) -> tuple[str, LinkedText]:
    """Render one instance's heading, and its text with the Refs it prints."""
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
) -> LinkedText | None:
    """Resolve the prose slot and fill its placeholders from `args` (ADR 0037).

    Total by design (ADR 0032): an id resolving to nothing renders as no prose,
    because the load-time gate is what reports it and rendering must stay
    printable for a rule the registry does not hold at all.
    """
    variants = rule.variants if rule is not None else {}
    resolved = resolve(text, variant, variants)
    return None if resolved is None else fill_linked(resolved, args, registry)


def _cases(
    instance: SpecialInstance, rule: SpecialRuleConfig | None, registry: Registry
) -> LinkedText:
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
) -> LinkedText:
    """Fill in the rule's signature, or nothing at all for an unknown id."""
    return LinkedText() if rule is None else interpolate_linked(rule, args, registry)


def _join(separator: str, *parts: LinkedText | None) -> LinkedText:
    """Join the parts that are there, so an absent one leaves no separator."""
    return LinkedText.join(separator, (part for part in parts if part))


def special_lines(
    specials: Specials,
    *,
    registry: Registry | None = None,
    anchor_of: AnchorOf | None = None,
) -> list[SpecialLine]:
    """Render one slot's instances as lines, grouped by heading.

    N instances of an id become one line, in the order the ids were
    contributed. An atmospheric name is part of the grouping key rather than a
    detail of the first instance: two `to_hit` named apart are two lines,
    because collapsing them would print one flavor name over the other's rule.

    Instances that read exactly alike are printed once. Three Models of a Unit
    each granting the same Resistance say one thing between them, and the
    reader learns nothing from the second and third copy. Instances naming
    different Refs do not read alike, whatever their words: each still links to
    its own rule.

    `anchor_of` resolves a Ref to its Rules Reference entry, for the line's own
    rule and for each Rule Link in its text. Without one nothing is anchored,
    which is what the console printing and a `--no-rules` document want.
    """
    registry = registry if registry is not None else load_registry()
    grouped: dict[tuple[str, str], dict[LinkedText, None]] = {}
    for identifier, instances in specials.items():
        for instance in instances:
            heading, text = _linked_row(identifier, instance, registry=registry)
            grouped.setdefault((identifier, heading), {})[text] = None
    resolve_anchor = anchor_of if anchor_of is not None else _no_anchor
    return [
        SpecialLine(
            name=heading,
            text=_join(_INSTANCE_SEPARATOR, *texts).resolved(resolve_anchor),
            anchor=resolve_anchor(f"{SPECIAL}.{identifier}"),
        )
        for (identifier, heading), texts in grouped.items()
    ]


def _no_anchor(_ref: str) -> None:
    """Resolve nothing, for a document with no Rules Reference to link into."""
