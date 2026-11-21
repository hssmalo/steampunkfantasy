"""The closed effect vocabulary a Damage row's text is parsed into.

The parser is best-effort: a clause it does not recognize becomes `Unparsed`, a
no-op the report lists with how often it was hit.
"""

import re
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from typing import cast

from spf.prose import LINK
from spf.schemas.type_aliases import DamageTableName
from spf.sim.dice import Dice


@dataclass(frozen=True, kw_only=True)
class Vocabulary:
    """The Token names plain prose may use, mapped to their ids: `shaken`."""

    tokens: Mapping[str, str]


@dataclass(frozen=True, kw_only=True)
class Kill:
    """Kill `count` Models, or Temporary Kill them."""

    count: int
    temporary: bool = False


@dataclass(frozen=True, kw_only=True)
class FutureDamage:
    """Add `amount` Future Damage."""

    amount: int


@dataclass(frozen=True, kw_only=True)
class FutureCrewDamage:
    """Add `amount` Future Crew Damage."""

    amount: int


@dataclass(frozen=True, kw_only=True)
class PlaceToken:
    """Place one Token, named by its id, with its `[N]` where it has one."""

    name: str
    strength: int | None = None


@dataclass(frozen=True, kw_only=True)
class DamageOn:
    """Roll `dice` damage on another of the Unit's Damage tables."""

    dice: Dice
    table: DamageTableName


@dataclass(frozen=True, kw_only=True)
class UnitDestroyed:
    """The Unit is destroyed."""


@dataclass(frozen=True, kw_only=True)
class AmplifyBleeding:
    """Step every Bleed up one size, optionally only when Bleed caused the roll."""

    only_from_bleeding: bool = False


@dataclass(frozen=True, kw_only=True)
class RollAgain:
    """Roll `times` more times on this same table."""

    times: int


@dataclass(frozen=True, kw_only=True)
class RowReference:
    """Apply the earlier row printed as `label` first."""

    label: str


@dataclass(frozen=True, kw_only=True)
class Spillover:
    """An effect aimed at something other than this Unit: counted, not followed."""

    text: str


@dataclass(frozen=True, kw_only=True)
class Unparsed:
    """Text the parser did not recognize: a no-op that is reported."""

    text: str


type Effect = (
    Kill
    | FutureDamage
    | FutureCrewDamage
    | PlaceToken
    | DamageOn
    | UnitDestroyed
    | AmplifyBleeding
    | RollAgain
    | RowReference
    | Spillover
    | Unparsed
)

STRENGTH_REQUIRED = frozenset({"bleed", "poison"})
"""Tokens that mean nothing without their `[N]`."""

_NUMBERS = {"a": 1, "one": 1, "two": 2, "three": 3, "four": 4, "five": 5}

_ROW_REFERENCE = re.compile(r"As (\d+(?:-\d+|\+)?),\s*")
_PARENTHETICAL = re.compile(r"\s*\([^()]*\)")
_SENTENCE = re.compile(r"\.(?:\s+|$)")
_SPILLOVER = re.compile(
    r"transported|all units|friendly units|within range|adjacent|this hex|"
    r"poison cloud",
    re.IGNORECASE,
)

_KILL = re.compile(
    r"(?P<temporary>temporarily )?(?:kill|destroy) (\w+) models?",
    re.IGNORECASE,
)
_FUTURE = re.compile(r"(?:x(\d+) )?\+(\d+) to future (crew )?damage", re.IGNORECASE)
_DESTROYED = re.compile(
    r"unit(?P<passengers> and all transported units)? (?:destroyed|killed)",
    re.IGNORECASE,
)
_DAMAGE_ON = re.compile(
    r"(?:roll |take |do )?(?P<dice>\d*d\d+(?:[+-]\d+)?) "
    r"(?:(?P<table>psychic|critical|crew|regular|inner) )?damage",
    re.IGNORECASE,
)
_AMPLIFY = re.compile(
    r"(?P<conditional>if caused by bleeding, )?amplify (?:all )?bleeding(?: one step)?",
    re.IGNORECASE,
)
_ROLL_AGAIN = re.compile(r"roll (\w+) times on this table", re.IGNORECASE)
_EXTRA_TOKEN = re.compile(
    r"(?:gain one extra |unit gets another )?(?P<token>.+?)(?: token)?", re.IGNORECASE
)
_STRENGTH = re.compile(r"(?P<name>.*?)\[(?P<strength>\d+)\]")


def _number(text: str) -> int | None:
    """Read a count written as digits or as a word."""
    return int(text) if text.isdigit() else _NUMBERS.get(text.lower())


def _clauses(text: str) -> list[str]:
    """Split effect text into clauses, keeping a condition with its consequence."""
    pieces = [
        piece.strip()
        for sentence in _SENTENCE.split(_PARENTHETICAL.sub("", text))
        for piece in sentence.split(",")
    ]
    clauses: list[str] = []
    for piece in filter(None, pieces):
        if clauses and clauses[-1].lower().startswith("if ") and "," not in clauses[-1]:
            clauses[-1] = f"{clauses[-1]}, {piece}"
        else:
            clauses.append(piece)
    return clauses


def _token(text: str, vocabulary: Vocabulary) -> PlaceToken | Unparsed | None:
    """Recognize one Token, by Rule Link first and by its plain name otherwise."""
    if link := LINK.fullmatch(text):
        namespace, _, token = link[2].partition(".")
        if namespace != "token":
            return None
        label = link[1]
    elif (name := _STRENGTH.fullmatch(text)) and name["name"].lower() in (
        vocabulary.tokens
    ):
        token, label = vocabulary.tokens[name["name"].lower()], text
    elif text.lower() in vocabulary.tokens:
        token, label = vocabulary.tokens[text.lower()], text
    else:
        return None
    strength = _STRENGTH.fullmatch(label)
    if token in STRENGTH_REQUIRED and strength is None:
        return Unparsed(text=text)
    return PlaceToken(
        name=token, strength=None if strength is None else int(strength["strength"])
    )


def _effects_of(clause: str, vocabulary: Vocabulary) -> list[Effect] | None:
    """Parse one clause, or `None` when it fits no shape in the vocabulary."""
    parsers: list[Callable[[str], list[Effect] | None]] = [
        _kill,
        _future,
        _destroyed,
        _damage_on,
        _amplify,
        _roll_again,
    ]
    for parse in parsers:
        if (effects := parse(clause)) is not None:
            return effects
    if (extra := _EXTRA_TOKEN.fullmatch(clause)) and (
        token := _token(extra["token"], vocabulary)
    ):
        return [token]
    return None


def _kill(clause: str) -> list[Effect] | None:
    """Parse `Kill N models` and `Temporarily kill N models`."""
    if (match := _KILL.fullmatch(clause)) and (count := _number(match[2])):
        return [Kill(count=count, temporary=bool(match["temporary"]))]
    return None


def _future(clause: str) -> list[Effect] | None:
    """Parse `+N to future (crew) damage`, optionally multiplied: `x3 +3 …`."""
    if not (match := _FUTURE.fullmatch(clause)):
        return None
    amount = int(match[1] or 1) * int(match[2])
    return [
        FutureCrewDamage(amount=amount) if match[3] else FutureDamage(amount=amount)
    ]


def _destroyed(clause: str) -> list[Effect] | None:
    """Parse `Unit destroyed`, with or without its passengers."""
    if not (match := _DESTROYED.fullmatch(clause)):
        return None
    return (
        [UnitDestroyed(), Spillover(text=clause)]
        if match["passengers"]
        else [UnitDestroyed()]
    )


def _damage_on(clause: str) -> list[Effect] | None:
    """Parse `d6 psychic damage`: a roll on another Damage table."""
    if not (match := _DAMAGE_ON.fullmatch(clause)):
        return None
    table = cast("DamageTableName", (match["table"] or "regular").capitalize())
    return [DamageOn(dice=Dice.parse(match["dice"]), table=table)]


def _amplify(clause: str) -> list[Effect] | None:
    """Parse `Amplify bleeding`, optionally only when Bleed caused the roll."""
    if not (match := _AMPLIFY.fullmatch(clause)):
        return None
    return [AmplifyBleeding(only_from_bleeding=bool(match["conditional"]))]


def _roll_again(clause: str) -> list[Effect] | None:
    """Parse `Roll N times on this table`."""
    if (match := _ROLL_AGAIN.fullmatch(clause)) and (times := _number(match[1])):
        return [RollAgain(times=times)]
    return None


def parse_effect(text: str, *, vocabulary: Vocabulary) -> list[Effect]:
    """Parse a Damage row's effect text into effects, in the order written."""
    effects: list[Effect] = []
    if reference := _ROW_REFERENCE.match(text):
        effects.append(RowReference(label=reference[1]))
        text = text[reference.end() :]
    for clause in _clauses(text):
        if (parsed := _effects_of(clause, vocabulary)) is not None:
            effects.extend(parsed)
        elif _SPILLOVER.search(clause):
            effects.append(Spillover(text=clause))
        elif " and " in clause and all(
            parts := [_effects_of(part, vocabulary) for part in clause.split(" and ")]
        ):
            effects.extend(effect for part in parts for effect in part or [])
        else:
            effects.append(Unparsed(text=clause))
    return effects
