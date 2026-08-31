"""Tests for the shared orders-table shaping in `spf.render.orders`."""

from spf.render.orders import flat_rows


def test_flat_rows_yields_one_row_per_option_in_speed_order() -> None:
    orders = {"still": [["A", "B"], ["C", "D"]], "slow": [["E", "F"]]}

    assert flat_rows(orders) == [
        ("still", ["A", "B"]),
        ("still", ["C", "D"]),
        ("slow", ["E", "F"]),
    ]


def test_flat_rows_of_an_absent_order_table_is_empty() -> None:
    assert flat_rows(None) == []
    assert flat_rows({}) == []


def test_flat_rows_copies_the_cells_it_is_given() -> None:
    cells = ["A", "B"]

    ((_, row),) = flat_rows({"still": [cells]})

    assert row == cells
    assert row is not cells
