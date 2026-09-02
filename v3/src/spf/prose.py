"""The placeholder grammar a signature and an instance's prose share (ADR 0037).

A `{N}` slot means the same thing wherever an **Instance** writes one: fill it
from that Instance's **Args**. The registry checks a placeholder is fillable,
rendering fills it, and lint compares two strings once filled — three modules
over one grammar, so it lives here rather than inside any one of them.
"""

import re

from spf.registry import Registry
from spf.schemas.rules import RuleRecord

PLACEHOLDER = re.compile(r"\{([A-Za-z_][A-Za-z0-9_]*)(\.id)?\}")
"""A variable slot: `{N}`, or `{version.id}` for the raw ref."""

_GROUP = re.compile(r"\[[^][]*\]")
"""One bracketed group of a signature: `[{N}+]`, `[1 for {M}]`."""


def fill(
    template: str,
    args: dict[str, int | str],
    registry: Registry,
    seen: frozenset[str] = frozenset(),
) -> str:
    """Fill every placeholder in `template` in with `args`.

    A bare `{var}` on a ref-valued argument renders the target's name, and the
    target's own signature after it: a ref's arguments travel with the ref, so
    the numbers an instance carries for the target print where the *target*
    declares them. `{var.id}` asks for the raw id instead.
    """

    def substitute(match: re.Match[str]) -> str:
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
        nested = interpolate(target, args, registry, seen | {str(value)})
        return f"{target.name}{nested}"

    return PLACEHOLDER.sub(substitute, template)


def interpolate(
    rule: RuleRecord,
    args: dict[str, int | str],
    registry: Registry,
    seen: frozenset[str] = frozenset(),
) -> str:
    """Fill `rule`'s signature in with `args`.

    Only a signature has groups to elide: square brackets in prose are square
    brackets, so the elision stays here rather than in `fill` (ADR 0037).
    """
    if not rule.signature:
        return ""
    return fill(_elide(rule.signature, args), args, registry, seen)


def _elide(signature: str, args: dict[str, int | str]) -> str:
    """Drop each group no argument fills, so an optional one reads as absent."""

    def keep(match: re.Match[str]) -> str:
        names = [name for name, _ in PLACEHOLDER.findall(match.group(0))]
        unfilled = all(args.get(name) is None for name in names)
        return "" if names and unfilled else match.group(0)

    return _GROUP.sub(keep, signature)
