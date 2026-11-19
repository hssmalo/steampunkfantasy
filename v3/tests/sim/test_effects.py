"""Parsing a Damage row's effect text into the closed effect vocabulary."""

import pytest

from spf.sim.dice import Dice
from spf.sim.effects import (
    AmplifyBleeding,
    DamageOn,
    Effect,
    FutureCrewDamage,
    FutureDamage,
    Kill,
    PlaceToken,
    RollAgain,
    RowReference,
    Spillover,
    UnitDestroyed,
    Unparsed,
    Vocabulary,
    parse_effect,
)

VOCABULARY = Vocabulary(
    tokens={
        "dazed": "dazed",
        "bleed": "bleed",
        "poison": "poison",
        "fire": "fire",
        "stuck fast": "stuck_fast",
    }
)
"""Invented Token names, so the parser is tested against its own vocabulary."""


def _parse(text: str) -> list[Effect]:
    return parse_effect(text, vocabulary=VOCABULARY)


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("Kill 1 model", [Kill(count=1)]),
        ("Destroy 2 models", [Kill(count=2)]),
        ("destroy one model", [Kill(count=1)]),
        ("+1 to future damage", [FutureDamage(amount=1)]),
        ("+3 to future damage,", [FutureDamage(amount=3)]),
        ("x3 +3 to future damage", [FutureDamage(amount=9)]),
        ("+2 to future crew damage", [FutureCrewDamage(amount=2)]),
        ("Unit destroyed", [UnitDestroyed()]),
        ("Unit Destroyed", [UnitDestroyed()]),
        ("Unit killed", [UnitDestroyed()]),
        ("Roll three times on this table", [RollAgain(times=3)]),
        ("Amplify all bleeding one step", [AmplifyBleeding()]),
    ],
)
def test_single_effects(text: str, expected: list[Effect]) -> None:
    assert _parse(text) == expected


def test_damage_on_another_table() -> None:
    assert _parse("Kill 1 model, d6 psychic damage") == [
        Kill(count=1),
        DamageOn(dice=Dice.parse("d6"), table="Psychic"),
    ]
    assert _parse("Take d12 crew damage") == [
        DamageOn(dice=Dice.parse("d12"), table="Crew")
    ]
    assert _parse("roll 2d4-1 critical damage") == [
        DamageOn(dice=Dice.parse("2d4-1"), table="Critical")
    ]


def test_a_row_reference_comes_first() -> None:
    assert _parse("As 4-5, +1 to future damage") == [
        RowReference(label="4-5"),
        FutureDamage(amount=1),
    ]


def test_token_by_plain_word() -> None:
    assert _parse("Dazed") == [PlaceToken(name="dazed")]
    assert _parse("Stuck Fast, Fire") == [
        PlaceToken(name="stuck_fast"),
        PlaceToken(name="fire"),
    ]
    assert _parse("Bleed[6]") == [PlaceToken(name="bleed", strength=6)]


def test_token_by_rule_link() -> None:
    assert _parse("{Dazed:token.dazed}") == [PlaceToken(name="dazed")]
    assert _parse("{Bleed[8]:token.bleed}") == [PlaceToken(name="bleed", strength=8)]


def test_a_rule_link_beats_its_label() -> None:
    assert _parse("{Bleed[4]:token.poison}") == [PlaceToken(name="poison", strength=4)]


def test_a_bleed_or_poison_without_strength_is_unparsed() -> None:
    assert _parse("As 1, {Dazed:token.bleed}") == [
        RowReference(label="1"),
        Unparsed(text="{Dazed:token.bleed}"),
    ]


def test_extra_token_phrasings() -> None:
    assert _parse("Gain one extra {Dazed:token.dazed}") == [PlaceToken(name="dazed")]
    assert _parse("+1 to future damage and unit gets another Dazed token") == [
        FutureDamage(amount=1),
        PlaceToken(name="dazed"),
    ]


def test_amplify_only_when_caused_by_bleeding() -> None:
    assert _parse("As 2-3, if caused by bleeding, amplify bleeding") == [
        RowReference(label="2-3"),
        AmplifyBleeding(only_from_bleeding=True),
    ]


def test_effects_aimed_elsewhere_are_spillover() -> None:
    text = "d6 psychic damage to all friendly units within range 2"
    assert _parse(f"Kill 1 model, {text}") == [Kill(count=1), Spillover(text=text)]


def test_destroyed_with_its_passengers() -> None:
    assert _parse("Unit and all transported units destroyed") == [
        UnitDestroyed(),
        Spillover(text="Unit and all transported units destroyed"),
    ]


def test_unrecognised_text_is_unparsed() -> None:
    assert _parse("Rotate unit 180°") == [Unparsed(text="Rotate unit 180°")]
    assert _parse("Dazed, loses {fear:special.fear}") == [
        PlaceToken(name="dazed"),
        Unparsed(text="loses {fear:special.fear}"),
    ]


def test_a_condition_keeps_its_consequence() -> None:
    assert _parse("If more than 2 models are alive, kill 1 model") == [
        Unparsed(text="If more than 2 models are alive, kill 1 model")
    ]
    assert _parse("Dazed, if already Dazed double initial crew damage") == [
        PlaceToken(name="dazed"),
        Unparsed(text="if already Dazed double initial crew damage"),
    ]


def test_parenthetical_asides_are_ignored() -> None:
    assert _parse("Amplify all bleeding one step. (4 to 6, 6 to 8)") == [
        AmplifyBleeding()
    ]
