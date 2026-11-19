"""The small grammar `--start` and `--incoming` are written in."""

import pytest

from spf.sim.dice import Dice
from spf.sim.effects import PlaceToken
from spf.sim.scenario import Hit, Start, parse_hits, parse_start


def test_a_bare_roll_lands_on_the_chosen_table() -> None:
    assert parse_hits("d6", table="Psychic") == [
        Hit(dice=Dice.parse("d6"), table="Psychic")
    ]


def test_a_roll_may_name_its_table() -> None:
    assert parse_hits("regular:d6-2, crew: 2d4", table="Psychic") == [
        Hit(dice=Dice.parse("d6-2"), table="Regular"),
        Hit(dice=Dice.parse("2d4"), table="Crew"),
    ]


def test_a_start_holds_hits_future_damage_and_tokens() -> None:
    start = parse_start(
        "regular:d6, bleed=4, bleed=6, future=2, future_crew=1, fire=2, shaken",
        table="Regular",
    )
    assert start == Start(
        hits=[Hit(dice=Dice.parse("d6"))],
        tokens=[
            PlaceToken(name="bleed", strength=4),
            PlaceToken(name="bleed", strength=6),
            PlaceToken(name="fire"),
            PlaceToken(name="fire"),
            PlaceToken(name="shaken"),
        ],
        future=2,
        future_crew=1,
    )


def test_an_empty_start_is_allowed() -> None:
    assert parse_start("", table="Regular") == Start()


@pytest.mark.parametrize(
    "text", ["sideways:d6", "bleed", "poison=x", "future=lots", "=3", "d6=2"]
)
def test_nonsense_is_rejected(text: str) -> None:
    with pytest.raises(ValueError, match=r"--start|--incoming|dice|table"):
        parse_start(text, table="Regular")


def test_incoming_takes_only_rolls() -> None:
    with pytest.raises(ValueError, match="--incoming"):
        parse_hits("bleed=4", table="Regular")
