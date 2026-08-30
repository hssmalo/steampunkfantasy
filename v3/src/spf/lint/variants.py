"""Find prose written out longhand that a variant of the rule already spells.

A soft finding rather than a load failure (ADR 0031): both spellings render the
same line, so a corpus half-migrated is a tidiness question, not a correctness
one. That is what lets the migration proceed a rule at a time.

`check_longhand` is a predicate over two strings, in the shape `names.py`
keeps. `check_specials` adds the walk over the prose slots an instance has, and
still reads no disk: the pools come from the caller.
"""

from collections.abc import Iterator, Mapping

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


def _prose_slots(instance: SpecialInstance) -> Iterator[str | None]:
    """Every slot of one instance a variant could have filled (ADR 0031)."""
    yield instance.text
    yield instance.preamble
    for case in instance.cases:
        yield case.text


def check_specials(
    specials: Specials, pools: Mapping[str, Mapping[str, str]]
) -> Iterator[tuple[str, str]]:
    """Yield `(identifier, message)` for every prose slot written longhand.

    `pools` maps a rule's identifier to its variants: a rule the mapping does
    not name has no pool to draw on, so nothing it writes is longhand.
    """
    for identifier, instances in specials.items():
        variants = pools.get(identifier, {})
        if not variants:
            continue
        for instance in instances:
            for prose in _prose_slots(instance):
                if (message := check_longhand(prose, variants)) is not None:
                    yield identifier, message
