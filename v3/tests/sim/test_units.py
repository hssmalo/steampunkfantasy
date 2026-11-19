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
from spf.sim.units import unit_scenario, vocabulary_of
from tests.conftest import (
    InstallRegistry,
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
