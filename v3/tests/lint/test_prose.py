"""Tests for the pure prose predicates and the walk that feeds them.

Table-driven over plain strings, like the name rules: a prose rule is a string
predicate precisely so a test needs no fixture, no disk and no schema.
"""

import pytest

from spf.lint import prose

# ---------------------------------------------------------------------------
# Whitespace
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "value",
    [
        "A flying monster bird.",
        "Two sentences. Separated by one space.",
        "A paragraph.\n\nAnd the next one.",
        "- One bullet\n- Another bullet",
        "",
    ],
)
def test_check_whitespace_accepts_clean_prose(value: str) -> None:
    """Single spaces, newlines and blank lines are all prose as authored."""
    assert prose.check_whitespace(value) is None


@pytest.mark.parametrize(
    "value",
    [
        " leading",
        "trailing ",
        "trailing newline is padding too\n ",
        "a doubled  space",
        "a tripled   space",
    ],
)
def test_check_whitespace_rejects_padding(value: str) -> None:
    """Padding at either edge, and any run of spaces inside a line."""
    assert prose.check_whitespace(value) is not None


def test_check_whitespace_allows_a_trailing_newline() -> None:
    r"""A multi-line TOML string ends with one, and that is not padding.

    `'''...\\n'''` is how the corpus writes a paragraph, so treating the
    closing newline as a defect would flag most of the data and teach nothing.
    """
    assert prose.check_whitespace("A paragraph.\n") is None


# ---------------------------------------------------------------------------
# Terminal punctuation
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "value",
    [
        "Within weapon range",
        "Range = 1",
        "bleeding does not cause more bleeding",
        "Stacks with still, slow, and fast",
        "Two sentences. Both terminated.",
        "A lead-in, then a list:\n\n- One\n- Two.",
        "Ignore the damage at {N}+",
        "Speed is set to still. Treat all F as -",
        "",
    ],
)
def test_check_terminal_punctuation_accepts(value: str) -> None:
    """A fragment needs no terminator, and notation may be the last character.

    A value carrying no internal sentence punctuation is left alone whichever
    way it ends: deciding whether one clause is a sentence or a fragment is
    not something a predicate can do, and guessing would rewrite good prose.
    """
    assert prose.check_terminal_punctuation(value) is None


@pytest.mark.parametrize(
    "value",
    [
        "Two sentences. The second is unterminated",
        "A lead-in, then a list:\n\n- One\n- Two",
        "Roll a d6. Apply damage (after every token)",
        "Ends on a comma. Which is not a terminator,",
    ],
)
def test_check_terminal_punctuation_rejects(value: str) -> None:
    """A value that punctuates a sentence inside it must close the last one."""
    assert prose.check_terminal_punctuation(value) is not None


# ---------------------------------------------------------------------------
# The walk
# ---------------------------------------------------------------------------


def test_walk_prose_locates_each_value_by_its_dotted_path() -> None:
    """A finding has to name something a reader can open the file and find."""
    data = {
        "units": {
            "archer": {
                "name": "Archer",
                "description": "An archer.",
                "specials": [{"text": "First."}, {"text": "Second."}],
            }
        }
    }

    assert dict(prose.walk_prose(data)) == {
        "units.archer.description": "An archer.",
        "units.archer.specials.0.text": "First.",
        "units.archer.specials.1.text": "Second.",
    }


def test_walk_prose_reaches_prose_held_in_a_list() -> None:
    """A damage table's `notes` is a list, and every entry of it is prose."""
    data = {"notes": ["first note", "second note"]}

    assert dict(prose.walk_prose(data)) == {
        "notes.0": "first note",
        "notes.1": "second note",
    }


def test_walk_prose_stays_out_of_a_damage_table() -> None:
    """A row is a table cell, terse by design, and carries its own `effect`."""
    data = {"damage_tables": {"Regular": {"rows": [{"effect": "Kill 1 model"}]}}}

    assert list(prose.walk_prose(data)) == []


def test_walk_prose_skips_fields_that_are_not_prose() -> None:
    """`name` is the name linter's, and `todo` is the designer's own notes."""
    data = {"name": "Archer", "todo": "Skrive ferdig reglene", "signature": "Fire"}

    assert list(prose.walk_prose(data)) == []


def test_check_prose_names_the_rule_it_broke() -> None:
    """The bundler yields `(rule, message)` pairs, as the name rules do."""
    rules = [rule for rule, _ in prose.check_prose("Two sentences.  Padded")]

    assert rules == ["whitespace", "terminal-punctuation"]
