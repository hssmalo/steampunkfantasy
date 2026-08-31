"""Tests for the synthetic builders the rest of the suite is written against.

The builders stand in for the committed corpus (ADR 0033), so what they hand a
test has to behave the way loaded Race data does: pass the load-time gate, and
survive a trip through a TOML file.
"""

from pathlib import Path

import pytest
from pydantic import ValidationError

from spf.armies import unit
from spf.config import config
from spf.races import get_race
from tests.conftest import (
    InstallRegistry,
    synthetic_assault,
    synthetic_equipment,
    synthetic_model,
    synthetic_race,
    synthetic_registry,
    synthetic_special,
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


# ---------------------------------------------------------------------------
# The registry seam
# ---------------------------------------------------------------------------

_COUNTDOWN = {"countdown": [{"text": "Three rounds."}]}
"""A Special Instance of an id no committed registry holds."""


def test_the_gate_accepts_a_special_id_the_installed_registry_declares(
    install_registry: InstallRegistry,
) -> None:
    install_registry(synthetic_registry(specials={"countdown": None}))

    race = synthetic_race(units={"squad": synthetic_unit(specials=_COUNTDOWN)})

    assert list(race.units["squad"].specials) == ["countdown"]


def test_the_gate_still_rejects_a_special_id_the_registry_lacks(
    install_registry: InstallRegistry,
) -> None:
    install_registry()

    with pytest.raises(ValidationError, match="'countdown' is not a Special id"):
        synthetic_race(units={"squad": synthetic_unit(specials=_COUNTDOWN)})


def test_an_invented_special_id_reaches_every_holder_and_slot(
    install_registry: InstallRegistry,
) -> None:
    # The reason the seam exists: with the registry fixed, no synthetic Race
    # could carry a Special on every Holder, and such tests had to read a
    # committed Race instead.
    install_registry(synthetic_registry(specials={"countdown": None}))

    race = synthetic_race(
        units={"squad": synthetic_unit(specials=_COUNTDOWN)},
        models={
            "soldier": synthetic_model(
                unit_specials=_COUNTDOWN,
                specials=_COUNTDOWN,
                assault=synthetic_assault(specials=_COUNTDOWN),
            )
        },
        equipment={
            "knife": synthetic_equipment(
                name="Knife",
                cost=None,
                upgrade_all=None,
                unit_specials=_COUNTDOWN,
                model_specials=_COUNTDOWN,
                assault={"specials": _COUNTDOWN},
                range={
                    "range": 12,
                    "angle": [True, False, False, False],
                    "damage": "d6",
                    "ap": 0,
                    "specials": _COUNTDOWN,
                },
            )
        },
    )

    assert list(race.equipment["knife"].range.specials) == ["countdown"]  # pyright: ignore[reportOptionalMemberAccess]


def test_a_narrowed_special_is_refused_the_slots_it_does_not_declare(
    install_registry: InstallRegistry,
) -> None:
    install_registry(
        synthetic_registry(specials={"countdown": synthetic_special(slots=["model"])})
    )

    with pytest.raises(ValidationError, match="is not a unit Special"):
        synthetic_race(units={"squad": synthetic_unit(specials=_COUNTDOWN)})


def test_the_installed_registry_answers_a_module_that_imported_the_loader(
    install_registry: InstallRegistry,
) -> None:
    # `spf.armies.unit` reads its Speeds through its own reference to
    # `load_registry`, bound when the module was imported rather than looked
    # up per call.
    installed = install_registry()

    assert unit.load_registry() is installed
