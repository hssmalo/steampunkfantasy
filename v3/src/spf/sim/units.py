"""Build a Scenario from a catalogue Unit: its Models, Damage tables and Instances."""

from collections import defaultdict

from spf.armies.build import ArmyList
from spf.registry import Registry
from spf.schemas.race import RaceConfig
from spf.sim.dice import Dice
from spf.sim.effects import Vocabulary
from spf.sim.scenario import Hit, Scenario, Start
from spf.sim.tables import compile_table

_RESISTANCE_TYPE = "resistance_type."


def vocabulary_of(registry: Registry) -> Vocabulary:
    """Map every Token's name, as prose writes it, to the Token's id."""
    return Vocabulary(
        tokens={
            record.name.lower(): identifier
            for identifier, record in registry.records.get("token", {}).items()
            if record.name
        }
    )


def unit_scenario(  # noqa: PLR0913
    race: RaceConfig,
    unit: str,
    *,
    registry: Registry,
    start: Start,
    incoming: list[Hit] | None = None,
    max_rounds: int = 20,
    resistance: bool = True,
) -> Scenario:
    """Build the Scenario for one Unit at its default loadout.

    Resistance and Endurance are read from the Unit-level Instances of the Unit,
    its Models and their Default Equipment (ADR 0027 for resistance).
    """
    army = ArmyList(race=next(iter(race.races)), nick="", units=[])
    resolved = army.add_unit(unit, race_config=race).resolve(race).units[0]
    specials = resolved.unit_specials
    vocabulary = vocabulary_of(registry)
    resistances: defaultdict[str, list[Dice]] = defaultdict(list)
    for instance in specials.get("resistance", []) if resistance else []:
        version, strength = instance.args.get("version"), instance.args.get("N")
        if isinstance(version, str) and strength is not None:
            kind = version.removeprefix(_RESISTANCE_TYPE)
            resistances[kind].append(Dice.parse(str(strength)))
    endurance = sum(
        strength
        for instance in specials.get("endurance", [])
        if isinstance(strength := instance.args.get("N"), int)
    )
    return Scenario(
        unit=resolved.config.name,
        models=len(resolved.models),
        tables={
            name: compile_table(name, table, vocabulary=vocabulary)
            for name, table in resolved.config.damage_tables.items()
        },
        start=start,
        incoming=incoming or [],
        resistance=dict(resistances),
        endurance=endurance,
        max_rounds=max_rounds,
        points=None if resolved.config.cost is None else resolved.cost().to_points(),
    )
