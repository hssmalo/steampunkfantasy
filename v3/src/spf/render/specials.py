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

from spf.registry import Registry, load_registry
from spf.schemas.rules import RuleRecord
from spf.schemas.special import SpecialInstance, Specials

_PLACEHOLDER = re.compile(r"\{([A-Za-z_][A-Za-z0-9_]*)(\.id)?\}")
"""A signature's variable slot: `{N}`, or `{version.id}` for the raw ref."""

_GROUP = re.compile(r"\[[^][]*\]")
"""One bracketed group of a signature: `[{N}+]`, `[1 for {M}]`."""

_PROSE_SEPARATOR = ". "
"""Between a signature and the instance's own prose about its occurrence."""

_INSTANCE_SEPARATOR = "; "
"""Between the texts of several instances sharing one heading."""


def special_row(
    identifier: str, instance: SpecialInstance, *, registry: Registry
) -> tuple[str, str]:
    """Render one instance as the (heading, text) pair a reader is shown."""
    rule = registry.specials.get(identifier)
    heading = instance.name or (rule.name if rule is not None else identifier)
    signature = "" if rule is None else _interpolate(rule, instance.args, registry)
    parts = [part for part in (signature, instance.text) if part]
    return heading, _PROSE_SEPARATOR.join(parts)


def special_lines(
    specials: Specials, *, registry: Registry | None = None
) -> list[tuple[str, str]]:
    """Render one slot's instances as (heading, text) lines, grouped by heading.

    N instances of an id become one line, in the order the ids were
    contributed. An atmospheric name is part of the grouping key rather than a
    detail of the first instance: two `to_hit` named apart are two lines,
    because collapsing them would print one flavor name over the other's rule.

    Instances that read exactly alike are printed once. Three Models of a Unit
    each granting the same Resistance say one thing between them, and the
    reader learns nothing from the second and third copy.
    """
    registry = registry if registry is not None else load_registry()
    grouped: dict[tuple[str, str], dict[str, None]] = {}
    for identifier, instances in specials.items():
        for instance in instances:
            heading, text = special_row(identifier, instance, registry=registry)
            grouped.setdefault((identifier, heading), {})[text] = None
    return [
        (heading, _INSTANCE_SEPARATOR.join(text for text in texts if text))
        for (_, heading), texts in grouped.items()
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
