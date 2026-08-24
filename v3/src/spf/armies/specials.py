"""Merging Special instances along a source chain (ADR 0024)."""

from spf.schemas.special import Specials

NOTE_SEPARATOR = "; "
"""Between the notes of two sources resolved into one record."""


def join_notes(*notes: str) -> str:
    """Join every source's `note` into the one the resolved record carries.

    `note` is a sibling of `specials` rather than one of them (ADR 0024), so it
    has no instances to keep apart — a chain of sources collapses to one string,
    dropping the empty ones and any repeat.
    """
    kept = list(dict.fromkeys(note for note in notes if note))
    return NOTE_SEPARATOR.join(kept)


def merge_specials(*sources: Specials) -> Specials:
    """Accumulate every source's instances, resetting where one replaces.

    Accumulation is the default and it keeps N instances: the data layer never
    merges two instances into one, because joining their prose is a rendering
    decision — and an impossible one where the two carry different args.

    An instance marked `replace` clears every instance of its id contributed
    *earlier* in the chain, leaving itself and anything contributed later. That
    order-dependence is the point: clearing the whole chain would let a default
    equipment's replace eat a paid upgrade's contribution, inverting the
    paid-kit-wins ordering of ADR 0020.

    The chain is per slot. Nothing here crosses from one slot into another —
    `assault_poison` and `range_poison` are different rules, so a replace that
    reached across would be replacing a rule it does not name.
    """
    merged: Specials = {}
    for source in sources:
        for identifier, instances in source.items():
            for instance in instances:
                if instance.replace:
                    merged[identifier] = []
                merged.setdefault(identifier, []).append(instance)
    return merged
