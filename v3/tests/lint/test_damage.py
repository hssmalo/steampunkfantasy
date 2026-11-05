"""Tests for the Row reference rule, a pure predicate over a Damage table's rows.

Table-driven over plain `(roll, effect)` pairs, like the prose rules: the rule
needs no fixture, no disk and no schema.
"""

import pytest

from spf.lint import damage


def messages(*rows: tuple[str, str]) -> list[str]:
    """Return the message of every finding on `rows`, checking the rule's name."""
    findings = list(damage.check_table(rows))
    assert {rule for rule, _ in findings} <= {"row-reference"}
    return [message for _, message in findings]


def test_a_reference_to_a_roll_no_row_has_fires() -> None:
    """`As 1-4` contradicts a table that has no row `1-4`."""
    found = messages(("1-3", "+1 to future damage"), ("4-5", "As 1-4, Shaken"))
    assert len(found) == 1
    assert "1-4" in found[0]


def test_a_reference_forward_fires() -> None:
    """A row can only build on what is printed above it."""
    found = messages(("4", "As 5-8, Shaken"), ("5-8", "d6 critical damage"))
    assert len(found) == 1
    assert "5-8" in found[0]


def test_a_row_naming_itself_fires() -> None:
    """A row is not earlier than itself."""
    assert len(messages(("4", "As 4, Shaken"))) == 1


def test_a_reference_to_an_earlier_row_is_quiet() -> None:
    """The form the rule exists to protect, with and without a further effect."""
    assert not messages(
        ("1-3", "+1 to future damage"),
        ("4", "As 1-3"),
        ("5", "As 4, Shaken"),
        ("6+", "d6 critical damage"),
        ("7+", "As 6+, Shaken"),
    )


@pytest.mark.parametrize(
    "effect", ["As below, Shaken", "as below", "as above", "Shaken, as below"]
)
def test_a_direction_instead_of_a_roll_fires(effect: str) -> None:
    """Below and above don't name a row, however they are spelled or placed."""
    found = messages(("1-3", "+1 to future damage"), ("4", effect))
    assert len(found) == 1
    assert "direction" in found[0]
