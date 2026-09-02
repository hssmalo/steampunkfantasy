"""Find prose written out longhand that a variant of the rule already spells.

A soft finding rather than a load failure (ADR 0032): both spellings render the
same line, so writing one out longhand is a tidiness question, not a
correctness one.

`check_longhand` is a predicate over two strings, in the shape `names.py`
keeps. `check_specials` adds the walk over the prose slots an instance has, and
still reads no disk: the pools come from the caller.
"""

from collections.abc import Iterator, Mapping

from spf.prose import fill
from spf.registry import Registry
from spf.schemas.special import SpecialInstance, Specials


def check_longhand(prose: str | None, variants: Mapping[str, str]) -> str | None:
    """Name the variant that already spells `prose`, or None when none does.

    Exact equality only. Deciding that two near-identical spellings mean one
    thing is a rules judgment, so it stays with the maintainer.
    """
    if prose is None:
        return None
    for identifier, text in variants.items():
        if prose == text:
            return f"prose {prose!r} is the variant {identifier!r} written out"
    return None


def _prose_slots(
    instance: SpecialInstance,
) -> Iterator[tuple[str | None, dict[str, int | str]]]:
    """Every slot a variant could have filled, with the args in scope for it.

    A case sees its own args over the instance's; the preamble scoping them
    sees only the instance's (ADR 0037).
    """
    yield instance.text, instance.args
    yield instance.preamble, instance.args
    for case in instance.cases:
        yield case.text, instance.args | case.args


def check_specials(
    specials: Specials,
    pools: Mapping[str, Mapping[str, str]],
    *,
    registry: Registry,
) -> Iterator[tuple[str, str]]:
    """Yield `(identifier, message)` for every prose slot written longhand.

    `pools` maps a rule's identifier to its variants: a rule the mapping does
    not name has no pool to draw on, so nothing it writes is longhand.

    Each pool is filled with the args in scope before it is compared, so an
    instance that typed the number out matches the variant that computes it
    (ADR 0037). The registry is what renders a ref-valued arg.
    """
    for identifier, instances in specials.items():
        variants = pools.get(identifier, {})
        if not variants:
            continue
        for instance in instances:
            for prose, args in _prose_slots(instance):
                if prose is None:
                    continue
                filled = {
                    name: fill(text, args, registry) for name, text in variants.items()
                }
                if (message := check_longhand(prose, filled)) is not None:
                    yield identifier, message
