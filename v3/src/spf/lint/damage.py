"""The Row reference rule, as a pure predicate over a Damage table's rows.

Only the reference is checked, because a reference to a row that isn't there is
the data contradicting itself (ADR 0038). How an effect is otherwise worded is
not the linter's business.
"""

import re
from collections.abc import Iterator, Sequence

_ROLL = r"\d+(?:-\d+|\+)?"
_LEADING = re.compile(rf"^As ({_ROLL})(?:,|$)")


def check_table(rows: Sequence[tuple[str, str]]) -> Iterator[tuple[str, str]]:
    """Yield `(rule, message)` for every Row reference that breaks the rule."""
    rolls = {roll for roll, _ in rows}
    for roll, effect in rows:
        if (match := _LEADING.match(effect)) and match[1] not in rolls:
            yield "row-reference", f"row {roll!r} names roll {match[1]!r}: no such row"
