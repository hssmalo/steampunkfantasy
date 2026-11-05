"""The Row reference rule, as a pure predicate over a Damage table's rows.

Only the reference is checked, because a reference to a row that isn't there is
the data contradicting itself (ADR 0038). How an effect is otherwise worded is
not the linter's business.
"""

import re
from collections.abc import Iterator, Sequence

RULE = "row-reference"

_ROLL = r"\d+(?:-\d+|\+)?"
_REFERENCE = re.compile(rf"\bas ({_ROLL})(?![\w-])", re.IGNORECASE)
_DIRECTION = re.compile(r"\bas (below|above)\b", re.IGNORECASE)
_BARE = re.compile(rf"^{_ROLL},")


def check_table(rows: Sequence[tuple[str, str]]) -> Iterator[tuple[str, str]]:
    """Yield `(rule, message)` for every Row reference that breaks the rule."""
    every_roll = {roll for roll, _ in rows}
    earlier: set[str] = set()
    for roll, effect in rows:
        if direction := _DIRECTION.search(effect):
            yield RULE, f"row {roll!r} says {direction[0]!r}: a direction names no row"
        if _BARE.match(effect):
            yield RULE, f"row {roll!r} says {effect!r}: a reference starts 'As'"
        for match in _REFERENCE.finditer(effect):
            target = match[1]
            if match.start() > 0:
                yield RULE, f"row {roll!r} says {match[0]!r}: it must come first"
            elif match[0].startswith("as"):
                yield RULE, f"row {roll!r} says {match[0]!r}: write it 'As'"
            if effect[match.end() :][:1] not in {"", ","}:
                yield RULE, f"row {roll!r} says {match[0]!r}: follow it with a comma"
            if target not in every_roll:
                yield RULE, f"row {roll!r} names {target!r}: no such row"
            elif target not in earlier:
                yield RULE, f"row {roll!r} names {target!r}: not an earlier row"
        earlier.add(roll)
