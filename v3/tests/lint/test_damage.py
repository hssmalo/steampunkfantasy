"""Tests for the Row reference rule, a pure predicate over a Damage table's rows.

Table-driven over plain `(roll, effect)` pairs, like the prose rules: the rule
needs no fixture, no disk and no schema.
"""

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
