"""What the rules registries still owe the game designer (ADR 0024).

Three lists, none of them a gate. Adding a stub is deliberately no harder than
writing a real rule -- making it harder only buys fake one-line rule text --
so the countdown's visibility is the whole of the friction.

The three are kept apart on purpose. Completeness is at-least-one-of, so a
finished rule may carry an open question of its own, and a designer who wants
to write the missing rules should not have to read past questions about rules
that are already written.
"""

from collections.abc import Iterable, Iterator
from dataclasses import dataclass

from spf.registry import SPECIAL, Registry
from spf.schemas.race import RaceConfig
from spf.schemas.special import Specials


@dataclass(frozen=True)
class RuleEntry:
    """One record on a countdown, named the way a ref names it."""

    namespace: str
    key: str
    name: str
    todo: str | None = None

    @property
    def ref(self) -> str:
        """The record's fully qualified reference."""
        return f"{self.namespace}.{self.key}"


def _entries(registry: Registry) -> Iterator[tuple[RuleEntry, bool]]:
    """Every record in every namespace, paired with whether it is written."""
    for namespace, records in sorted(registry.records.items()):
        for key, record in sorted(records.items()):
            entry = RuleEntry(
                namespace=namespace, key=key, name=record.name, todo=record.todo
            )
            yield entry, record.written


def unwritten(registry: Registry) -> list[RuleEntry]:
    """List records with no meaning-bearing field, whose `todo` is all they say.

    The original countdown: these are stubs, and the rule text is missing.
    """
    return [entry for entry, written in _entries(registry) if not written]


def open_questions(registry: Registry) -> list[RuleEntry]:
    """List records that are written and still carry a `todo`.

    A design question about a finished rule -- whether two rules are
    duplicates, whether a fixed value wants a variable. Not a stub, and worth
    writing down only because this list can see it.
    """
    return [entry for entry, written in _entries(registry) if written and entry.todo]


def unreachable(registry: Registry, used: set[str]) -> list[RuleEntry]:
    """List the Special ids no Race writes an instance of.

    A countdown rather than a gate: most unreachable rules are *intentionally*
    dead -- the `assault_*` / `range_*` pairs -- so erroring would demand a
    hand-maintained list of the intentional ones, which is the kind of list
    deleting the `Literal`s existed to remove.

    Only the Special namespace is asked. Every other registry holds vocabulary
    the rest of the data spells in fields of its own -- a Unit's `size`, a
    Speed on an orders table -- so "no instance names it" would say nothing
    there.
    """
    return [
        entry
        for entry, _ in _entries(registry)
        if entry.namespace == SPECIAL and entry.key not in used
    ]


def _slots(race: RaceConfig) -> Iterator[Specials]:
    """Every collection of instances a Race holds, whatever slot it fills."""
    for unit in race.units.values():
        yield unit.specials
    for model in race.models.values():
        yield from (model.unit_specials, model.specials, model.assault.specials)
    for equipment in race.equipment.values():
        yield from (equipment.unit_specials, equipment.model_specials)
        if equipment.assault is not None:
            yield equipment.assault.specials
        if equipment.range is not None:
            yield equipment.range.specials


def used_special_ids(race_configs: Iterable[RaceConfig]) -> set[str]:
    """Collect the Special ids the given Races write at least one instance of."""
    return {key for race in race_configs for slot in _slots(race) for key in slot}
