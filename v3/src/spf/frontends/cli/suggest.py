"""Turn a mistyped CLI value into a "Did you mean ...?" error.

Split in two on purpose: `suggest` does the matching and knows nothing about
how an error is worded, so a command with its own vocabulary can rank
candidates here and phrase its own message.
"""

import difflib
from collections.abc import Iterable

# Above this many candidates, a "Did you mean ...?" is a vocabulary dump.
_MAX_SUGGESTIONS = 8

# A typo has one intended target, so the fuzzy pass offers a shortlist rather
# than a whole family, and only over candidates this similar.
_MAX_FUZZY = 3
_CUTOFF = 0.6


def _normalize(value: str) -> str:
    """Casefold and collapse internal whitespace, so matching ignores both."""
    return " ".join(value.split()).casefold()


def suggest(value: str, options: Iterable[str]) -> list[str]:
    """Return ranked suggestions for a value that is not one of options."""
    options = list(options)
    normalized = _normalize(value)

    # Substring matches are ordered shortest-first so an exact key leads its own
    # family ("To Hit" before "To Hit (2)"), and are uncapped so the whole
    # family is offered.
    substring = sorted(
        (option for option in options if normalized in _normalize(option)),
        key=_rank,
    )
    # The fuzzy pass only covers typos, where nothing contains the value at all.
    # Running both would answer "Reroll" with "Recoil" as well as "Ork Reroll".
    # It matches on normalized forms too, so a typo shouted in caps still lands.
    matches = substring or _fuzzy(normalized, options)
    return list(dict.fromkeys(matches))


def _rank(option: str) -> tuple[int, str]:
    """Order shortest-first, alphabetically among equals."""
    return (len(option), option)


def _fuzzy(normalized: str, options: list[str]) -> list[str]:
    """Return the closest options by similarity, ranked by `_rank` among ties.

    Scored here rather than by `difflib.get_close_matches`, which orders equally
    similar candidates arbitrarily — "To Hit (3)" ahead of "To Hit (2)" — and so
    would contradict the substring pass on the same family.
    """
    matcher = difflib.SequenceMatcher(b=normalized)
    scored: list[tuple[float, str]] = []
    for option in options:
        matcher.set_seq1(_normalize(option))
        if matcher.ratio() >= _CUTOFF:
            scored.append((matcher.ratio(), option))
    scored.sort(key=lambda scored_option: (-scored_option[0], _rank(scored_option[1])))
    return [option for _, option in scored[:_MAX_FUZZY]]


def _did_you_mean(suggestions: list[str]) -> str:
    *rest, last = (f'"{suggestion}"' for suggestion in suggestions)
    if not rest:
        listed = last
    elif len(rest) == 1:  # no Oxford comma between just two
        listed = f"{rest[0]} or {last}"
    else:
        listed = f"{', '.join(rest)}, or {last}"
    return f"Did you mean {listed}?"


def resolve_or_raise(value: str, options: Iterable[str], *, noun: str, see: str) -> str:
    """Return the canonical spelling of value, or raise ValueError.

    A unique case-insensitive match is accepted and canonicalised: case is the
    commonest way to get these keys wrong, and `take cover` is unambiguous.
    """
    options = list(options)
    if value in options:
        return value

    normalized = _normalize(value)
    equal = [option for option in options if _normalize(option) == normalized]
    if len(equal) == 1:
        return equal[0]

    # `suggest` is deliberately uncapped, so a whole family survives — but a
    # value too vague to guess matches most of the vocabulary, and reprinting
    # it is the wall of text these messages exist to replace. Past that point
    # there is no guess worth offering, so point at the listing instead.
    suggestions = suggest(value, options)
    guessable = 0 < len(suggestions) <= _MAX_SUGGESTIONS
    tail = (
        _did_you_mean(suggestions)
        if guessable
        else f"Run {see!r} to see all {noun} rules."
    )
    msg = f'Unknown {noun} "{value}". {tail}'
    raise ValueError(msg)
