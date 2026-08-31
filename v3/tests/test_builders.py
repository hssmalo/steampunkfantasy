"""Tests for the synthetic builders the rest of the suite is written against.

The builders stand in for the committed corpus (ADR 0033), so what they hand a
test has to behave the way loaded Race data does: pass the load-time gate, and
survive a trip through a TOML file.
"""

from pathlib import Path

import pytest

from spf.config import config
from spf.races import get_race
from tests.conftest import (
    synthetic_equipment,
    synthetic_model,
    synthetic_race,
    synthetic_unit,
    write_race_toml,
)


def test_default_race_has_a_costed_and_an_uncosted_unit() -> None:
    units = synthetic_race().units

    assert [unit.cost is None for unit in units.values()] == [False, True]


def test_default_race_model_declares_a_holder() -> None:
    model = synthetic_race().models["soldier"]

    assert [holder.holder for holder in model.equipment_limit] == ["Hands"]


def test_default_race_has_one_default_and_one_upgrade_equipment() -> None:
    race = synthetic_race()

    defaults = race.models["soldier"].equipment
    upgrades = [key for key, item in race.equipment.items() if item.cost is not None]
    assert defaults == ["knife"]
    assert upgrades == ["sword"]


def test_shaped_race_keeps_only_what_it_was_given() -> None:
    race = synthetic_race(
        units={"mob": synthetic_unit(name="Mob", models=["brute"])},
        models={"brute": synthetic_model(name="Brute", equipment=[])},
        equipment={},
    )

    assert list(race.units) == ["mob"]
    assert list(race.models) == ["brute"]
    assert race.equipment == {}


def test_equipment_defaults_to_an_upgrade_and_can_be_made_a_default() -> None:
    upgrade = synthetic_equipment()
    default = synthetic_equipment(name="Knife", cost=None, upgrade_all=None)

    assert upgrade.cost is not None
    assert default.cost is None


def test_written_race_toml_loads_back_as_the_race_it_was_written_from(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    race = synthetic_race()
    path = write_race_toml(tmp_path, race)
    monkeypatch.setattr(config.paths, "races", tmp_path)

    assert path.name == "goblin.toml"
    assert get_race("goblin") == race
