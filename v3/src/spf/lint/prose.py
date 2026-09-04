"""The prose rules, as pure predicates over strings.

The counterpart to `names` for the fields a player reads as sentences rather
than as labels. Every rule takes a plain string and returns the violation
message, or `None` when the value is clean.

The rules are deliberately narrow. Prose is not mechanically decidable, and a
rule that guesses at intent rewrites good writing -- so each one fires only
where the data contradicts itself, never where it merely could read better.
"""

import re
from collections.abc import Iterator, Mapping

PROSE_FIELDS = frozenset(
    {
        "comment",
        "description",
        "effect",
        "explanation",
        "flavor",
        "lore",
        "note",
        "notes",
        "preamble",
        "text",
        "tip",
    }
)
"""The fields read as sentences.

`name` and `signature` are labels, and belong to the name rules. `todo` is the
game designer's own working notes, kept verbatim -- part of it is Norwegian,
which is why `typos.toml` carries `som` as a word.
"""

TABLE_FIELDS = frozenset({"rows"})
"""Subtrees the prose rules stay out of.

A damage table's rows are cells, not sentences -- `Kill 1 model`, `+2 to future
damage, destroy one minor head` -- and a row carries its own `effect`. Holding
a cell to sentence punctuation would put a period on one row of a table and
not on the terser row beside it, which is less consistent, not more.
"""

SENTENCE_PUNCTUATION = ".!?:"
"""What closes a sentence, and what proves an earlier one was closed."""

NOTATION = "+-"
"""Order-card notation a value may legitimately end on: `at {N}+`, `all F as -`."""

_INTERNAL_RUN_OF_SPACES = re.compile(r"\S  +\S")


def check_whitespace(value: str) -> str | None:
    r"""Check that `value` is padded neither at its edges nor inside a line.

    One trailing newline is not padding: `'''...\\n'''` is how the corpus
    writes a paragraph, so the check is against the value with that closing
    newline removed.
    """
    body = value.removesuffix("\n")
    if body != body.strip():
        return f"prose {_excerpt(value)} has leading or trailing whitespace"
    if match := _INTERNAL_RUN_OF_SPACES.search(body):
        return f"prose {_excerpt(value)} has a doubled space at {match.group()!r}"
    return None


def check_terminal_punctuation(value: str) -> str | None:
    """Check that a value punctuating a sentence inside it closes the last one.

    Only that direction. Whether a lone clause is a sentence wanting a period
    or a fragment that must not have one is a judgment no predicate can make,
    and enforcing the converse would strip the period off `Robotic iron dragon
    breathing acid.` Internal punctuation is the one signal the data gives for
    free: a value that has closed a sentence already is prose, all the way to
    its end.
    """
    body = value.strip()
    if not body:
        return None
    if not any(mark in body[:-1] for mark in SENTENCE_PUNCTUATION):
        return None
    if body[-1] in SENTENCE_PUNCTUATION + NOTATION:
        return None
    return f"prose {_excerpt(value)} does not end its last sentence"


def check_prose(value: str) -> Iterator[tuple[str, str]]:
    """Yield `(rule, message)` for every prose rule `value` breaks."""
    checks = {
        "whitespace": check_whitespace,
        "terminal-punctuation": check_terminal_punctuation,
    }
    for rule, check in checks.items():
        if (message := check(value)) is not None:
            yield rule, message


def walk_prose(
    data: object, path: str = "", field: str = ""
) -> Iterator[tuple[str, str]]:
    """Yield `(location, value)` for every prose field under `data`.

    Walks a dumped model rather than the file, so the fields a schema does not
    declare never reach the rules -- which is what keeps a rules file still
    being drafted out of the corpus these checks police.

    The field name travels separately from the path because a list index is
    not a field: `notes = ["...", "..."]` is two pieces of prose, and both are
    `notes`.
    """
    if isinstance(data, Mapping):
        for key, value in data.items():
            if key in TABLE_FIELDS:
                continue
            yield from walk_prose(
                value, f"{path}.{key}" if path else str(key), str(key)
            )
    elif isinstance(data, list):
        for index, value in enumerate(data):
            yield from walk_prose(value, f"{path}.{index}", field)
    elif isinstance(data, str) and field in PROSE_FIELDS and data.strip():
        yield path, data


def _excerpt(value: str, limit: int = 40) -> str:
    """Quote enough of a value to find it, on one line."""
    flat = " ".join(value.split())
    return repr(flat if len(flat) <= limit else f"{flat[:limit]}...")
