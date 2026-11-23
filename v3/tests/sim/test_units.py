"""Building a Scenario from a catalogue Unit, its Instances and the Registry.

The Race and the Registry are synthetic, so no rule or Race edit can move what
these tests expect.
"""

import pytest

from spf.registry import Registry
from spf.schemas import rules as r
from spf.schemas.race import RaceConfig
from spf.sim.dice import Dice
from spf.sim.scenario import Start
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
        },
        records={
            "resistance_type": {
                kind: r.DamageTypeRuleConfig(name=kind.title(), effect="Resists.")
                for kind in ["regular", "poison"]
            },
            "token": {
                "dazed": r.TokenRuleConfig(name="Dazed", effect="Reels."),
                "bleed": r.TokenRuleConfig(name="Bleed", effect="Bleeds."),
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
    assert vocabulary_of(registry).tokens == {"dazed": "dazed", "bleed": "bleed"}


def test_a_scenario_counts_the_units_models(registry: Registry) -> None:
    scenario = unit_scenario(_race(), "squad", registry=registry, start=Start())
    assert (scenario.unit, scenario.models) == ("Squad", 3)
    assert list(scenario.tables) == ["Regular"]


def test_resistance_comes_from_every_instance(registry: Registry) -> None:
    scenario = unit_scenario(_race(), "squad", registry=registry, start=Start())
    assert scenario.resistance["regular"] == [Dice.parse("1")]
    assert scenario.resistance["poison"] == [Dice.parse("d4")] * 3


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
