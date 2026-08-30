"""Rendering a `Cost` for a document rather than for a console.

`Cost.__str__` grays its zero components out with Rich markup, which is right
in a terminal and wrong everywhere else: the tags would land literally in a
Markdown document and break a LaTeX one. So a Rendering formats a Cost here,
two ways — compact prose for a detail entry, and one cell per currency for a
summary table that has to align down the page.
"""

from spf.schemas import type_aliases as t

CURRENCIES: tuple[str, ...] = ("ip", "mp", "xp", "cp", "vpm")
"""Every currency, in the order both formatters print them."""

FREE = "free"
"""What a Cost of nothing reads as; an unpriced record renders as nothing."""


def _amounts(cost: t.Cost) -> list[tuple[str, int]]:
    """Pair each currency with its amount, in `CURRENCIES` order."""
    return [(currency, getattr(cost, currency)) for currency in CURRENCIES]


def cost_text(cost: t.Cost | None) -> str:
    """Render a Cost compactly (`3ip 2mp`), leaving the zero currencies out.

    A Cost of nothing is `FREE` and an absent one is the empty string: a record
    with no `cost` is not something a player buys, which is a different fact
    from one that costs nothing.
    """
    if cost is None:
        return ""
    parts = [f"{amount}{currency}" for currency, amount in _amounts(cost) if amount]
    return " ".join(parts) if parts else FREE


def cost_columns(cost: t.Cost | None) -> list[str]:
    """Render a Cost as one cell per currency, in `CURRENCIES` order.

    A zero is an empty cell rather than a `0`, so a column of mostly-unpriced
    records reads as sparsely down the page as `cost_text` reads across it.
    """
    if cost is None:
        return ["" for _ in CURRENCIES]
    return [str(amount) if amount else "" for _, amount in _amounts(cost)]
