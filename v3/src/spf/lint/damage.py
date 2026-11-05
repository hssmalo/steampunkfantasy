"""The Row reference rule, as a pure predicate over a Damage table's rows.

A reference to a row that isn't there is the data contradicting itself, and its
form is what makes a reference recognizable in free text (ADR 0038). How an
effect is otherwise worded is not the linter's business.
"""

import re
from collections.abc import Collection, Iterator, Sequence

RULE = "row-reference"

_ROLL = r"\d+(?:-\d+|\+)?"
_REFERENCE = re.compile(rf"\bas ({_ROLL})(?![\w-])(?P<after>.?)", re.IGNORECASE)
_DIRECTION = re.compile(r"\bas (below|above)\b", re.IGNORECASE)
_LEADING_ROLL = re.compile(rf"^{_ROLL},")


def check_table(rows: Sequence[tuple[str, str]]) -> Iterator[tuple[str, str]]:
    """Yield `(rule, message)` for every Row reference that breaks the rule."""
    every_roll = {roll for roll, _ in rows}
    earlier: set[str] = set()
    for roll, effect in rows:
        for problem in _check_effect(effect, every_roll, earlier):
            yield RULE, f"row {roll!r}: {problem}"
        earlier.add(roll)


def _check_effect(
    effect: str, every_roll: Collection[str], earlier: Collection[str]
) -> Iterator[str]:
    """Describe what is wrong with the Row references in one effect."""
    if direction := _DIRECTION.search(effect):
        yield f"{direction[0]!r} is a direction, which names no row"
    if _LEADING_ROLL.match(effect):
        yield f"{effect!r} leads with a roll: a reference starts 'As'"
    for match in _REFERENCE.finditer(effect):
        spelled, target = f"as {match[1]}", match[1]
        if match.start() > 0:
            yield f"{spelled!r} must come first"
        elif not match[0].startswith("As"):
            yield f"{spelled!r} must be written 'As'"
        if match["after"] not in {"", ","}:
            yield f"{spelled!r} must be followed by a comma"
        if target not in every_roll:
            yield f"{target!r} names no row"
        elif target not in earlier:
            yield f"{target!r} is not an earlier row"
