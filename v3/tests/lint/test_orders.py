"""Tests for the order-cell predicates.

An order cell is the most-printed string in the corpus and the one `typos`
cannot read: it skips any token holding a `+`, so `F+Depoloy` is invisible to
it. These rules are what see it.
"""

import pytest

from spf.lint import orders

VOCABULARY = frozenset({"F", "B", "BB", "A", "L/R", "360°", "Chs", "Fire", "Deploy"})


@pytest.mark.parametrize(
    "cell",
    [
        "",
        "-",
        "F",
        "360°",
        "L/R",
        "(L/R)",
        "F+B",
        "F+(Deploy)",
        "(B)+(B)",
        "A[slow]",
        "Fire(res)",
        "A[fast, fly]",
        "360°+A+A",
    ],
)
def test_check_cell_accepts_the_vocabulary(cell: str) -> None:
    """A cell of known orders, combined with `+`, is what the cards print."""
    assert list(orders.check_cell(cell, VOCABULARY)) == []


@pytest.mark.parametrize(
    ("cell", "rule"),
    [
        (" 360°", "order-whitespace"),
        ("A ", "order-whitespace"),
        ("Chs + B", "order-whitespace"),
        ("360°,F", "order-separator"),
        ("F+Depoloy", "order-name"),  # typos: ignore
        ("fire", "order-name"),
        ("Fire (res)", "order-spacing"),
        ("Fire(RES)", "order-argument"),
        ("A[Slow]", "order-argument"),
        ("A[fast,fly]", "order-argument"),
    ],
)
def test_check_cell_rejects(cell: str, rule: str) -> None:
    """Each defect the corpus actually carries, named by its own rule."""
    assert rule in [broken for broken, _ in orders.check_cell(cell, VOCABULARY)]


def test_check_cell_names_the_unknown_order() -> None:
    """The message has to carry the misspelling, or it locates nothing."""
    cell = "F+Depoloy"  # typos: ignore
    messages = [message for _, message in orders.check_cell(cell, VOCABULARY)]

    assert any("Depoloy" in message for message in messages)  # typos: ignore


def test_check_cell_reports_a_lowercase_order_as_unknown() -> None:
    """Case is part of the name: `fire` and `Fire` are one order, spelled two ways."""
    assert [rule for rule, _ in orders.check_cell("fire", VOCABULARY)] == ["order-name"]


def test_walk_cells_finds_every_slot_that_holds_orders() -> None:
    """Movement and fire tables, equipment's gained orders, and shaken."""
    data = {
        "units": {
            "archer": {
                "orders": {"movement": {"slow": [["F", "B"]]}},
                "shaken": {"movement_order": ["-", "flee"]},
            }
        },
        "equipment": {"bow": {"orders_gained": {"fire": {"still": [["Fire"]]}}}},
    }

    assert dict(orders.walk_cells(data)) == {
        "units.archer.orders.movement.slow.0.0": "F",
        "units.archer.orders.movement.slow.0.1": "B",
        "units.archer.shaken.movement_order.0": "-",
        "units.archer.shaken.movement_order.1": "flee",
        "equipment.bow.orders_gained.fire.still.0.0": "Fire",
    }
