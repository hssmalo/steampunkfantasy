"""Tests for the Cost formatters in `spf.render.costs`."""

from spf.render.costs import CURRENCIES, cost_columns, cost_text
from spf.schemas.type_aliases import Cost


def test_cost_text_omits_the_currencies_that_are_zero() -> None:
    assert cost_text(Cost(ip=3, mp=2)) == "3ip 2mp"


def test_cost_text_orders_the_currencies_the_way_the_columns_do() -> None:
    every = Cost(ip=1, mp=2, xp=3, cp=4, vpm=5)

    assert cost_text(every) == "1ip 2mp 3xp 4cp 5vpm"


def test_a_cost_of_nothing_is_free_and_an_absent_cost_is_blank() -> None:
    assert cost_text(Cost()) == "free"
    assert cost_text(None) == ""


def test_cost_text_carries_no_rich_markup() -> None:
    # `Cost.__str__` grays zeroes out with Rich tags, which would land
    # literally in a Markdown document and break a LaTeX one.
    assert "[" not in cost_text(Cost(mp=8))


def test_cost_columns_is_one_cell_per_currency_with_zeroes_left_blank() -> None:
    assert cost_columns(Cost(ip=3, mp=2)) == ["3", "2", "", "", ""]
    assert CURRENCIES == ("ip", "mp", "xp", "cp", "vpm")


def test_cost_columns_of_an_absent_cost_is_every_cell_blank() -> None:
    assert cost_columns(None) == ["", "", "", "", ""]
