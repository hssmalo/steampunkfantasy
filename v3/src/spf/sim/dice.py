"""Dice expressions — `d6`, `d6-2`, `2d4`, `3` — and the die they are rolled on."""

import random
import re
from dataclasses import dataclass
from typing import Protocol, Self

_DICE = re.compile(r"(?:(?P<count>\d*)d(?P<sides>\d+))?(?P<modifier>[+-]?\d+)?")


class Roller(Protocol):
    """A source of die results. The engine only ever asks for one die at a time."""

    def roll(self, sides: int) -> int:
        """Roll one die with `sides` sides."""
        ...


@dataclass(frozen=True, kw_only=True)
class RandomRoller:
    """A Roller over a seeded `random.Random`, so a run can be reproduced."""

    rng: random.Random

    @classmethod
    def seeded(cls, seed: int) -> Self:
        """Build a Roller whose results are fixed by `seed`."""
        return cls(rng=random.Random(seed))  # noqa: S311  game dice, not cryptographic

    def roll(self, sides: int) -> int:
        """Roll one die with `sides` sides."""
        return self.rng.randint(1, sides)


@dataclass(frozen=True, kw_only=True)
class Dice:
    """`count` dice of `sides` sides plus `modifier`; no dice at all is a constant."""

    count: int
    sides: int
    modifier: int = 0

    @classmethod
    def parse(cls, text: str) -> Self:
        """Parse a dice expression, ignoring case and spaces."""
        spelled = text.replace(" ", "").lower()
        match = _DICE.fullmatch(spelled)
        if not spelled or match is None or not (match["sides"] or match["modifier"]):
            msg = f"not a dice expression: {text!r}"
            raise ValueError(msg)
        if match["sides"] is None:
            return cls(count=0, sides=0, modifier=int(match["modifier"]))
        return cls(
            count=int(match["count"] or 1),
            sides=int(match["sides"]),
            modifier=int(match["modifier"] or 0),
        )

    def roll(self, roller: Roller) -> int:
        """Roll every die and add the modifier."""
        return sum(roller.roll(self.sides) for _ in range(self.count)) + self.modifier

    def __str__(self) -> str:
        """Spell the expression the way a Damage row would."""
        dice = (
            f"{'' if self.count == 1 else self.count}d{self.sides}"
            if self.count
            else ""
        )
        modifier = f"{self.modifier:+d}" if self.modifier and dice else ""
        return dice + modifier if dice else str(self.modifier)
