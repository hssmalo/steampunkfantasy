"""Shared helpers for the damage simulator tests."""

from collections.abc import Iterable


class ScriptedRoller:
    """A die that returns the results it was given, in order.

    It checks each die's size too, so a test fails loudly when the engine rolls
    a different die than the one the scenario is about.
    """

    def __init__(self, results: Iterable[tuple[int, int]]) -> None:
        """Script `(sides, result)` pairs, consumed one per roll."""
        self._results = list(results)

    def roll(self, sides: int) -> int:
        """Return the next scripted result for a die of `sides` sides."""
        if not self._results:
            msg = f"unscripted roll of a d{sides}"
            raise AssertionError(msg)
        expected, result = self._results.pop(0)
        if sides != expected:
            msg = f"rolled a d{sides}, script expected a d{expected}"
            raise AssertionError(msg)
        return result

    @property
    def exhausted(self) -> bool:
        """Whether every scripted result was used."""
        return not self._results
