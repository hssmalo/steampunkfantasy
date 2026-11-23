"""Build a Scenario from a Unit: its Models, Damage tables and Instances."""

from collections import defaultdict

from spf.armies.build import ArmyList
from spf.armies.specials import merge_specials
from spf.armies.unit import Unit
from spf.registry import Registry
from spf.schemas.race import RaceConfig
from spf.schemas.special import Specials
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
    """Build the Scenario for one catalogue Unit at its default Loadout."""
    army = ArmyList(race=next(iter(race.races)), nick="", units=[])
    resolved = army.add_unit(unit, race_config=race).resolve(race).units[0]
    return scenario_of(
        resolved,
        registry=registry,
        start=start,
        incoming=incoming,
        max_rounds=max_rounds,
        resistance=resistance,
    )


def scenario_of(  # noqa: PLR0913
    unit: Unit,
    *,
    registry: Registry,
    start: Start,
    incoming: list[Hit] | None = None,
    max_rounds: int = 20,
    resistance: bool = True,
) -> Scenario:
    """Build the Scenario for a resolved Unit at whatever Loadout it carries.

    Resistance and Endurance are read from the Unit-level Instances of the Unit,
    its Models and their effective Equipment (ADR 0027 for resistance).
    """
    specials = unit.unit_specials
    sources = merge_specials(*_resistance_sources(unit))
    vocabulary = vocabulary_of(registry)
    resistances: defaultdict[str, list[Dice]] = defaultdict(list)
    for instance in sources.get("resistance", []) if resistance else []:
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
        unit=unit.display_name,
        models=len(unit.models),
        tables={
            name: compile_table(name, table, vocabulary=vocabulary)
            for name, table in unit.config.damage_tables.items()
        },
        start=start,
        incoming=incoming or [],
        resistance=dict(resistances),
        endurance=endurance,
        max_rounds=max_rounds,
        points=None if unit.config.cost is None else unit.cost().to_points(),
    )


def _resistance_sources(unit: Unit) -> list[Specials]:
    """Each source's Unit-level Instances once; a Unit Fixture's once per purchase.

    A source is the Unit, a Model kind or an Equipment kind, however many Models
    carry it. A Unit Fixture is bought for the whole Unit (ADR 0026).
    """
    sources = [unit.config.specials]
    models: set[str] = set()
    equipment: set[str] = set()
    purchases = unit.fixture_purchases
    for model in unit.models:
        if model.name not in models:
            models.add(model.name)
            sources.append(model.config.unit_specials)
        for equip in model.equipment:
            if equip.name not in equipment:
                equipment.add(equip.name)
                copies = purchases.get(equip.name, 1) if equip.upgrade_all else 1
                sources.extend([equip.unit_specials] * copies)
    return sources
