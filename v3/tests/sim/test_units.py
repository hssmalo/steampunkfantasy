"""Building a Scenario from a catalogue Unit, its Instances and the Registry.

The Race and the Registry are synthetic, so no rule or Race edit can move what
these tests expect.
"""

import pytest

from spf.armies.build import ArmyList
from spf.registry import Registry
from spf.schemas import rules as r
from spf.schemas.race import RaceConfig
from spf.sim.dice import Dice
from spf.sim.scenario import Healer, Scenario, Start
from spf.sim.units import scenario_of, unit_scenario, vocabulary_of
from tests.conftest import (
    InstallRegistry,
    synthetic_army,
    synthetic_equipment,
    synthetic_model,
    synthetic_race,
    synthetic_registry,
    synthetic_special,
    synthetic_unit,
)


def _registry() -> Registry:
    return synthetic_registry(
        specials={
            "resistance": synthetic_special(
                name="Resistance",
                slots=["unit"],
                signature="{version}[{N}]",
                variables={
                    "version": {"type": "ref", "namespaces": ["resistance_type"]},
                    "N": {"type": ["int", "die"]},
                },
            ),
            "endurance": synthetic_special(
                name="Endurance",
                slots=["unit"],
                variables={"N": {"type": "int"}, "model_class": {"type": "str"}},
            ),
            **{
                kind: synthetic_special(
                    name=kind.title(),
                    slots=["unit"],
                    signature="[{N}, {unit}, {phase}]",
                    variables={
                        "N": {"type": ["int", "str"]},
                        "unit": {"type": "str"},
                        "phase": {"type": "str"},
                    },
                )
                for kind in ["heal", "repair"]
            },
        },
        records={
            "resistance_type": {
                kind: r.DamageTypeRuleConfig(name=kind.title(), effect="Resists.")
                for kind in ["regular", "poison", "psychic", "fire"]
            },
            "token": {
                "dazed": r.TokenRuleConfig(name="Dazed", effect="Reels."),
                "bleed": r.TokenRuleConfig(name="Bleed", effect="Bleeds."),
                "stuck": r.TokenRuleConfig(
                    name="Stuck", effect="Cannot move.", critical=True
                ),
            },
        },
    )


def _resistance(kind: str, strength: int | str) -> dict[str, object]:
    return {"args": {"version": f"resistance_type.{kind}", "N": strength}}


@pytest.fixture
def registry(install_registry: InstallRegistry) -> Registry:
    return install_registry(_registry())


def _race() -> RaceConfig:
    return synthetic_race(
        units={
            "squad": synthetic_unit(
                models=["soldier", "soldier", "soldier"],
                specials={"resistance": [_resistance("regular", 1)]},
                damage_tables={"Regular": {"rows": ["1: Dazed", "2+: Kill 1 model"]}},
            )
        },
        models={
            "soldier": synthetic_model(
                unit_specials={
                    "endurance": [{"args": {"N": 1, "model_class": "soldier"}}]
                },
            )
        },
        equipment={
            "knife": synthetic_equipment(
                name="Knife",
                cost=None,
                upgrade_all=None,
                unit_specials={"resistance": [_resistance("poison", "d4")]},
            )
        },
    )


def test_the_vocabulary_is_every_token_name(registry: Registry) -> None:
    assert vocabulary_of(registry).tokens == {
        "dazed": "dazed",
        "bleed": "bleed",
        "stuck": "stuck",
    }


def test_a_scenario_counts_the_units_models(registry: Registry) -> None:
    scenario = unit_scenario(_race(), "squad", registry=registry, start=Start())
    assert (scenario.unit, scenario.models) == ("Squad", 3)
    assert list(scenario.tables) == ["Regular"]


def test_resistance_counts_each_source_once(registry: Registry) -> None:
    scenario = unit_scenario(_race(), "squad", registry=registry, start=Start())
    assert scenario.resistance["regular"] == [Dice.parse("1")]
    assert scenario.resistance["poison"] == [Dice.parse("d4")]


def test_resistance_can_be_turned_off(registry: Registry) -> None:
    scenario = unit_scenario(
        _race(), "squad", registry=registry, start=Start(), resistance=False
    )
    assert scenario.resistance == {}


def test_endurance_sums_every_instance(registry: Registry) -> None:
    scenario = unit_scenario(_race(), "squad", registry=registry, start=Start())
    assert scenario.endurance == 3


def _costed(cost: dict[str, int] | None) -> RaceConfig:
    return synthetic_race(
        units={"squad": synthetic_unit(cost=cost)},
        models={"soldier": synthetic_model()},
    )


def test_a_scenario_carries_the_units_points(registry: Registry) -> None:
    scenario = unit_scenario(_race(), "squad", registry=registry, start=Start())
    assert scenario.points == 3


def test_points_triple_ip_and_add_the_vpm(registry: Registry) -> None:
    race = _costed({"mp": 2, "cp": 1, "xp": 1, "ip": 1, "vpm": 2})
    scenario = unit_scenario(race, "squad", registry=registry, start=Start())
    assert scenario.points == 9


def test_a_unit_with_no_cost_has_no_points(registry: Registry) -> None:
    scenario = unit_scenario(_costed(None), "squad", registry=registry, start=Start())
    assert scenario.points is None


def _upgradable() -> RaceConfig:
    """Build a squad of three soldiers, with a costed sword and a promoted veteran."""
    return synthetic_race(
        units={"squad": synthetic_unit(models=["soldier"] * 3)},
        models={
            "soldier": synthetic_model(),
            "veteran": synthetic_model(
                name="Veteran", replaces="soldier", cost={"mp": 1}
            ),
        },
        equipment={
            "knife": synthetic_equipment(name="Knife", cost=None, upgrade_all=None),
            "sword": synthetic_equipment(),
        },
    )


def test_a_scenario_of_an_army_unit_is_named_by_its_nick(registry: Registry) -> None:
    race = _upgradable()
    army = synthetic_army(race, units=[])
    army = army.add_unit("squad", nick="Red Squad", race_config=race)
    army = army.add_unit("squad", race_config=race)
    units = army.resolve(race).units
    names = [scenario_of(unit, registry=registry, start=Start()).unit for unit in units]
    assert names == ["Red Squad", "Squad"]


def test_a_scenario_of_an_army_unit_prices_its_upgrades(registry: Registry) -> None:
    race = _upgradable()
    army = synthetic_army(race).upgrade_model(
        ("squad", 0),
        model_key=("soldier", 0),
        equipment_name="sword",
        race_config=race,
    )
    unit = army.resolve(race).units[0]
    assert scenario_of(unit, registry=registry, start=Start()).points == 5


def test_an_upgrade_model_keeps_its_slot(registry: Registry) -> None:
    race = _upgradable()
    army = synthetic_army(race).upgrade_unit(
        ("squad", 0),
        model_key=("soldier", 1),
        upgrade_model_name="veteran",
        race_config=race,
    )
    scenario = scenario_of(
        army.resolve(race).units[0], registry=registry, start=Start()
    )
    assert (scenario.models, scenario.points) == (3, 4)


def _kitted(**unit_fields: object) -> RaceConfig:
    """Build a squad of three soldiers, an elite to promote and a Unit Fixture.

    The Fixture sits on its own Holder so buying it never evicts the Default
    knife.
    """
    soldier = {"holders": ["Hands:2", "Independent:2"]}
    return synthetic_race(
        units={"squad": synthetic_unit(models=["soldier"] * 3, **unit_fields)},
        models={
            "soldier": synthetic_model(**soldier),
            "elite": synthetic_model(
                **soldier,
                name="Elite",
                replaces="soldier",
                cost={"mp": 1},
                type=["Infantry", "Elite"],
                unit_specials={
                    "resistance": [_resistance("psychic", 1)],
                    "endurance": [_endurance(1, "elite model")],
                },
            ),
            "champion": synthetic_model(
                **soldier,
                name="Champion",
                replaces="soldier",
                cost={"mp": 2},
                type=["Infantry", "SuperElite"],
            ),
        },
        equipment={
            "knife": synthetic_equipment(
                name="Knife",
                cost=None,
                upgrade_all=None,
                unit_specials={"resistance": [_resistance("poison", "d4")]},
            ),
            "cloak": synthetic_equipment(
                name="Cloak",
                upgrade_all=True,
                requires=[["Independent:1"]],
                unit_specials={"resistance": [_resistance("fire", 1)]},
            ),
            "vest": synthetic_equipment(
                name="Vest",
                upgrade_all=True,
                requires=[["Independent:1"]],
                unit_specials={
                    "endurance": [
                        _endurance(1, "regular model"),
                        _endurance(2, "elite model"),
                    ]
                },
            ),
        },
    )


def _endurance(strength: int, model_class: str) -> dict[str, object]:
    return {"args": {"N": strength, "model_class": model_class}}


def _promote(
    army: ArmyList, race: RaceConfig, *, slots: int, to: str = "elite"
) -> ArmyList:
    for _ in range(slots):
        army = army.upgrade_unit(
            ("squad", 0),
            model_key=("soldier", 0),
            upgrade_model_name=to,
            race_config=race,
        )
    return army


def _buy(
    army: ArmyList, race: RaceConfig, *, purchases: int = 1, fixture: str = "cloak"
) -> ArmyList:
    for _ in range(purchases):
        army = army.equip_unit(("squad", 0), equipment_name=fixture, race_config=race)
    return army


def _scenario(army: ArmyList, race: RaceConfig, registry: Registry) -> Scenario:
    return scenario_of(army.resolve(race).units[0], registry=registry, start=Start())


def test_resistance_counts_a_model_kind_once(registry: Registry) -> None:
    race = _kitted()
    army = _promote(synthetic_army(race), race, slots=2)
    assert _scenario(army, race, registry).resistance["psychic"] == [Dice.parse("1")]


@pytest.mark.parametrize("purchases", [1, 2])
def test_resistance_counts_a_unit_fixture_once_per_purchase(
    registry: Registry, purchases: int
) -> None:
    race = _kitted()
    army = _buy(synthetic_army(race), race, purchases=purchases)
    fire = _scenario(army, race, registry).resistance["fire"]
    assert fire == [Dice.parse("1")] * purchases


def test_resistance_from_different_sources_adds_up(registry: Registry) -> None:
    race = _kitted(specials={"resistance": [_resistance("poison", 2)]})
    poison = _scenario(synthetic_army(race), race, registry).resistance["poison"]
    assert poison == [Dice.parse("2"), Dice.parse("d4")]


def test_endurance_counts_a_regular_carrier_once(registry: Registry) -> None:
    race = _kitted()
    army = _buy(synthetic_army(race), race, fixture="vest")
    assert _scenario(army, race, registry).endurance == 3


def test_endurance_counts_an_elite_carrier_as_elite(registry: Registry) -> None:
    race = _kitted()
    army = _buy(_promote(synthetic_army(race), race, slots=1), race, fixture="vest")
    assert _scenario(army, race, registry).endurance == 2 * 1 + 2 + 1


def test_a_superelite_counts_as_elite(registry: Registry) -> None:
    race = _kitted()
    army = _promote(synthetic_army(race), race, slots=1, to="champion")
    army = _buy(army, race, fixture="vest")
    assert _scenario(army, race, registry).endurance == 2 * 1 + 2


def test_any_other_class_counts_for_every_model(registry: Registry) -> None:
    race = _kitted(specials={"endurance": [_endurance(1, " Model")]})
    assert _scenario(synthetic_army(race), race, registry).endurance == 3


def _healing(
    points: int | str, unit: str = "self", phase: str = "1st Healing", text: str = ""
) -> dict[str, object]:
    return {
        "args": {"N": points, "unit": unit, "phase": phase},
        **({"text": text} if text else {}),
    }


def _healed(registry: Registry, **unit_fields: object) -> Scenario:
    race = synthetic_race(units={"squad": synthetic_unit(**unit_fields)})
    return unit_scenario(race, "squad", registry=registry, start=Start())


def test_a_unit_heal_becomes_a_healer(registry: Registry) -> None:
    scenario = _healed(registry, specials={"heal": [_healing(2)]})
    assert scenario.healers == [Healer(kind="heal", points=2, phase=1)]


def test_healing_for_other_units_is_skipped_silently(registry: Registry) -> None:
    scenario = _healed(registry, specials={"heal": [_healing(2, unit="other")]})
    assert (scenario.healers, scenario.unplayed_healing) == ([], [])


def test_model_and_equipment_healing_counts_each_kind_once(registry: Registry) -> None:
    race = synthetic_race(
        units={"squad": synthetic_unit(models=["soldier"] * 3)},
        models={
            "soldier": synthetic_model(
                unit_specials={"repair": [_healing(1, phase="2nd Healing")]}
            )
        },
        equipment={
            "knife": synthetic_equipment(
                name="Knife",
                cost=None,
                upgrade_all=None,
                unit_specials={"repair": [_healing(2, unit="any")]},
            )
        },
    )
    scenario = unit_scenario(race, "squad", registry=registry, start=Start())
    assert scenario.healers == [
        Healer(kind="repair", points=1, phase=2),
        Healer(kind="repair", points=2, phase=1),
    ]


@pytest.mark.parametrize(
    "points", ["one per alive model", "One per alive repair drone model"]
)
def test_one_point_per_alive_model_counts_the_living(
    registry: Registry, points: str
) -> None:
    scenario = _healed(registry, specials={"repair": [_healing(points)]})
    assert scenario.healers == [Healer(kind="repair", points="alive", phase=1)]


@pytest.mark.parametrize(
    ("args", "spelled"),
    [
        ({"N": "three-ish", "unit": "self"}, "Heal[three-ish, self, 1st Healing]"),
        ({"N": 2, "unit": "nearby"}, "Heal[2, nearby, 1st Healing]"),
        ({"N": 2, "phase": "Agony 0"}, "Heal[2, self, Agony 0]"),
    ],
)
def test_healing_the_simulator_cannot_play_is_listed(
    registry: Registry, args: dict[str, object], spelled: str
) -> None:
    instance = _healing(2)
    instance["args"] = {"N": 2, "unit": "self", "phase": "1st Healing", **args}
    scenario = _healed(registry, specials={"heal": [instance]})
    assert (scenario.healers, scenario.unplayed_healing) == ([], [spelled])


def test_never_both_keeps_only_the_larger_healer_of_the_phase(
    registry: Registry,
) -> None:
    heals = [
        _healing(2, unit="any"),
        _healing(3, text="Either this or the other, Never both."),
        _healing(1, phase="2nd Healing"),
    ]
    scenario = _healed(registry, specials={"heal": heals, "repair": [_healing(1)]})
    assert scenario.healers == [
        Healer(kind="heal", points=3, phase=1),
        Healer(kind="heal", points=1, phase=2),
        Healer(kind="repair", points=1, phase=1),
    ]


def test_without_never_both_every_healer_of_the_phase_acts(
    registry: Registry,
) -> None:
    scenario = _healed(registry, specials={"heal": [_healing(2), _healing(3)]})
    assert [healer.points for healer in scenario.healers] == [2, 3]
