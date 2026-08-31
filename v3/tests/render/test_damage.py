"""Tests for the shared damage-roll rendering in `spf.render.damage`."""

from spf.render.damage import roll_text
from spf.schemas.type_aliases import AtLeastRoll, ExactRoll, RangeRoll


def test_roll_text_renders_each_roll_variant() -> None:
    assert roll_text(ExactRoll(value=9)) == "9"
    assert roll_text(RangeRoll(low=1, high=2)) == "1-2"
    assert roll_text(AtLeastRoll(value=6)) == "6+"
