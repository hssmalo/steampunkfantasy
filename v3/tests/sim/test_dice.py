"""Dice expressions, rolled against a scripted die."""

import pytest

from spf.sim.dice import Dice, RandomRoller
from tests.sim.conftest import ScriptedRoller


def test_single_die() -> None:
    assert Dice.parse("d6").roll(ScriptedRoller([(6, 4)])) == 4


def test_modifier_is_added() -> None:
    assert Dice.parse("d6-2").roll(ScriptedRoller([(6, 5)])) == 3
    assert Dice.parse("d8+1").roll(ScriptedRoller([(8, 8)])) == 9


def test_several_dice_are_summed() -> None:
    assert Dice.parse("2d4").roll(ScriptedRoller([(4, 1), (4, 3)])) == 4


def test_a_constant_is_a_dice_expression() -> None:
    assert Dice.parse("3").roll(ScriptedRoller([])) == 3


def test_spelling_is_forgiving() -> None:
    assert Dice.parse(" D12 + 2 ").roll(ScriptedRoller([(12, 1)])) == 3


def test_str_round_trips() -> None:
    assert str(Dice.parse("2d4-1")) == "2d4-1"
    assert str(Dice.parse("d6")) == "d6"


@pytest.mark.parametrize("text", ["", "dd6", "d", "6d", "d6+", "x"])
def test_nonsense_is_rejected(text: str) -> None:
    with pytest.raises(ValueError, match="dice"):
        Dice.parse(text)


def test_random_roller_is_reproducible_by_seed() -> None:
    first = RandomRoller.seeded(7)
    second = RandomRoller.seeded(7)
    rolls = [first.roll(6) for _ in range(20)]
    assert rolls == [second.roll(6) for _ in range(20)]
    assert 1 <= min(rolls) <= max(rolls) <= 6
