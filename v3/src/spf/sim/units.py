"""Build a Scenario from a Unit: its Models, Damage tables and Instances."""

import re
from collections import defaultdict
from typing import Literal

from spf.armies.build import ArmyList
from spf.armies.model import Model
from spf.armies.specials import merge_specials
from spf.armies.unit import Unit
from spf.registry import Registry
from spf.schemas.race import RaceConfig
from spf.schemas.rules import TokenRuleConfig
from spf.schemas.special import Specials
from spf.sim.dice import Dice
from spf.sim.effects import Vocabulary
from spf.sim.scenario import Healer, Hit, Scenario, Start
from spf.sim.tables import compile_table

_RESISTANCE_TYPE = "resistance_type."
_ELITE_TYPES = {"Elite", "SuperElite"}
_HEALING_KINDS: tuple[Literal["heal", "repair"], ...] = ("heal", "repair")
_HEALING_PHASES: dict[str, Literal[1, 2]] = {"1st Healing": 1, "2nd Healing": 2}
_PER_ALIVE_MODEL = re.compile(r"one per alive( .+)? model", re.IGNORECASE)
_NEVER_BOTH = "never both"


def vocabulary_of(registry: Registry) -> Vocabulary:
    """Map every Token's name, as prose writes it, to the Token's id."""
    return Vocabulary(
        tokens={
            record.name.lower(): identifier
            for identifier, record in registry.records.get("token", {}).items()
            if record.name
        }
    )


def _critical(registry: Registry) -> frozenset[str]:
    """List the Tokens the rules flag as a Critical Damage Effect."""
    return frozenset(
        identifier
        for identifier, record in registry.records.get("token", {}).items()
        if isinstance(record, TokenRuleConfig) and record.critical
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
    healing: bool = True,
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
        healing=healing,
    )


def scenario_of(  # noqa: PLR0913
    unit: Unit,
    *,
    registry: Registry,
    start: Start,
    incoming: list[Hit] | None = None,
    max_rounds: int = 20,
    resistance: bool = True,
    healing: bool = True,
) -> Scenario:
    """Build the Scenario for a resolved Unit at whatever Loadout it carries.

    Resistance, Endurance, Heal and Repair are read from the Unit-level
    Instances of the Unit, its Models and their effective Equipment (ADR 0027
    for resistance).
    """
    chain = merge_specials(*_resistance_contributors(unit))
    vocabulary = vocabulary_of(registry)
    resistances: defaultdict[str, list[Dice]] = defaultdict(list)
    for instance in chain.get("resistance", []) if resistance else []:
        version, strength = instance.args.get("version"), instance.args.get("N")
        if isinstance(version, str) and strength is not None:
            kind = version.removeprefix(_RESISTANCE_TYPE)
            resistances[kind].append(Dice.parse(str(strength)))
    healers, unplayed = _healers(chain) if healing else ([], [])
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
        endurance=_endurance(unit),
        healers=healers,
        critical=_critical(registry),
        unplayed_healing=unplayed,
        max_rounds=max_rounds,
        points=None if unit.config.cost is None else unit.cost().to_points(),
    )


def _resistance_contributors(unit: Unit) -> list[Specials]:
    """Each contributor's Unit-level Instances once; a Unit Fixture's per purchase.

    A contributor is the Unit, a Model kind or an Equipment kind, however many
    Models carry it. A Unit Fixture is bought for the whole Unit (ADR 0026).
    """
    contributors = [unit.config.specials]
    models: set[str] = set()
    equipment: set[str] = set()
    purchases = unit.fixture_purchases
    for model in unit.models:
        if model.name not in models:
            models.add(model.name)
            contributors.append(model.config.unit_specials)
        for equip in model.equipment:
            if equip.name not in equipment:
                equipment.add(equip.name)
                copies = purchases.get(equip.name, 1) if equip.upgrade_all else 1
                contributors.extend([equip.unit_specials] * copies)
    return contributors


def _healers(chain: Specials) -> tuple[list[Healer], list[str]]:
    """Read the Heal and Repair Instances this Unit plays on itself.

    Return the Healers in collection order, and the spelling of each Instance
    the simulator cannot play. An Instance for other Units only is no concern
    of this Unit. Where an Instance says "never both", only the largest of its
    kind in its Healing Phase acts.
    """
    healers: list[Healer] = []
    unplayed: list[str] = []
    for kind in _HEALING_KINDS:
        played: list[Healer] = []
        exclusive: set[int] = set()
        for instance in chain.get(kind, []):
            args = instance.args
            if args.get("unit") == "other":
                continue
            if (healer := _healer(kind, args)) is None:
                unplayed.append(_spelled(kind, args))
                continue
            played.append(healer)
            if _NEVER_BOTH in (instance.text or "").casefold():
                exclusive.add(healer.phase)
        for phase in exclusive:
            largest = max(
                (healer for healer in played if healer.phase == phase),
                key=_known_points,
            )
            played = [h for h in played if h.phase != phase or h is largest]
        healers.extend(played)
    return healers, unplayed


def _known_points(healer: Healer) -> int:
    """Compare Healers by N; one point per alive Model is not known until play."""
    return healer.points if isinstance(healer.points, int) else 0


def _healer(
    kind: Literal["heal", "repair"], args: dict[str, int | str]
) -> Healer | None:
    """Make one Instance a Healer, or `None` when its args cannot be played."""
    phase = _HEALING_PHASES.get(str(args.get("phase")))
    if args.get("unit") not in {"self", "any"} or phase is None:
        return None
    match args.get("N"):
        case int(points):
            return Healer(kind=kind, points=points, phase=phase)
        case str(text) if _PER_ALIVE_MODEL.fullmatch(text.strip()):
            return Healer(kind=kind, points="alive", phase=phase)
        case _:
            return None


def _spelled(kind: str, args: dict[str, int | str]) -> str:
    """Spell an Instance as its Signature prints it (`special.heal`)."""
    values = (str(args.get(name, "?")) for name in ["N", "unit", "phase"])
    return f"{kind.title()}[{', '.join(values)}]"


def _endurance(unit: Unit) -> int:
    """Endurance Tokens: N per Model of the named class, for every carrier."""
    total = 0
    for model in unit.models:
        chain = merge_specials(unit.config.specials, model.unit_specials)
        for instance in chain.get("endurance", []):
            strength = instance.args.get("N")
            if isinstance(strength, int) and _of_class(
                model, model_class=instance.args.get("model_class")
            ):
                total += strength
    return total


def _of_class(model: Model, *, model_class: object) -> bool:
    """Tell whether the Model is of the class an endurance Instance names.

    An elite is a Model of Type Elite or SuperElite; any class other than
    elite or regular names every Model.
    """
    elite = bool(_ELITE_TYPES.intersection(model.config.type))
    match str(model_class).strip().casefold():
        case "elite model":
            return elite
        case "regular model":
            return not elite
        case _:
            return True
