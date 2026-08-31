"""Shaping an orders table into printable rows.

Pure over `OrdersConfig`'s own field type, so it serves a Rendering built from
a resolved Army's merged orders (ADR 0007) and one built from a `RaceConfig`'s
declared table alike, with no Army in reach of the latter.
"""

type Rows = list[tuple[str, list[str]]]  # (speed, cells) per row
type Orders = dict[str, list[list[str]]] | None  # one order-type, per Speed


def flat_rows(orders: Orders) -> Rows:
    """Flatten one order-type into (speed, cells) per option row, in Speed order."""
    if not orders:
        return []
    return [
        (speed, list(cells)) for speed, options in orders.items() for cells in options
    ]
