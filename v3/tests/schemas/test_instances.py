"""Tests for the Special instance envelope (ADR 0024)."""

import pytest
from pydantic import ValidationError

from spf.schemas.race import RaceConfig
from spf.schemas.special import SpecialInstance


def test_an_instance_may_be_empty() -> None:
    # `[[units.x.specials.retreat]]` with no keys is a complete instance: the
    # id is the table key, and a rule with no variables needs nothing else.
    instance = SpecialInstance.model_validate({})

    assert instance.name is None
    assert instance.text is None
    assert instance.args == {}


def test_an_instance_does_not_replace_by_default() -> None:
    assert SpecialInstance.model_validate({}).replace is False


def test_an_instance_carries_a_local_name_and_prose() -> None:
    instance = SpecialInstance.model_validate(
        {"name": "Excellent Whip Handling", "text": "Only against Beasts.", "args": {}}
    )

    assert instance.name == "Excellent Whip Handling"
    assert instance.text == "Only against Beasts."


def test_args_are_nested() -> None:
    instance = SpecialInstance.model_validate({"args": {"N": 6, "version": "fire"}})

    assert instance.args == {"N": 6, "version": "fire"}


def test_the_envelope_is_closed() -> None:
    # A flat arg would be a fifth envelope key -- and the arg vocabulary is
    # edited in another file, so the closure cannot be a matter of convention.
    with pytest.raises(ValidationError, match="extra_forbidden"):
        SpecialInstance.model_validate({"N": 6})


# ---------------------------------------------------------------------------
# The gate, as a Race file meets it
# ---------------------------------------------------------------------------

_ASSAULT: dict[str, object] = {
    "strength": [1, 0, 0, 0],
    "strength_die": "4+",
    "deflection": [1, 0, 0, 0],
    "deflection_die": "4+",
    "damage": "d4",
    "ap": 0,
}

_MODEL: dict[str, object] = {
    "race": "goblin",
    "name": "Soldier",
    "equipment_limit": ["Hands:2"],
    "equipment": [],
    "type": ["Infantry"],
    "assault": _ASSAULT,
}

_UNIT: dict[str, object] = {
    "race": "goblin",
    "name": "Squad",
    "models": ["soldier"],
    "size": "Small",
    "shaken": {"speed": "slow", "movement_order": ["-", "-", "flee"]},
    "orders": {},
    "damage_tables": {"Regular": {"rows": ["1: Fine", "2: Dead"]}},
}

_EQUIPMENT: dict[str, object] = {"race": "goblin", "name": "Sword"}


def race(
    *,
    unit: dict[str, object] | None = None,
    model: dict[str, object] | None = None,
    equipment: dict[str, object] | None = None,
) -> RaceConfig:
    """Build the smallest race carrying one unit, one model and one equipment."""
    return RaceConfig.model_validate(
        {
            "races": {"goblin": {"name": "Goblin"}},
            "units": {"squad": _UNIT | (unit or {})},
            "models": {"soldier": _MODEL | (model or {})},
            "equipment": {"sword": _EQUIPMENT | (equipment or {})},
        }
    )


def test_a_unit_carries_instances_of_real_rules() -> None:
    loaded = race(
        unit={
            "specials": {
                "resistance": [{"args": {"version": "damage_type.poison", "N": 6}}]
            }
        }
    )

    (instance,) = loaded.units["squad"].specials["resistance"]
    assert instance.args["N"] == 6


def test_an_unknown_special_id_fails_the_race() -> None:
    with pytest.raises(ValidationError, match="is not a Special id"):
        race(unit={"specials": {"resistanse": [{}]}})  # typos: ignore


def test_a_unit_special_in_the_wrong_slot_fails_the_race() -> None:
    with pytest.raises(ValidationError, match="not a unit Special"):
        race(unit={"specials": {"assault_poison": [{"args": {"N": 6, "M": 2}}]}})


def test_an_equipment_grants_into_the_slot_it_names() -> None:
    with pytest.raises(ValidationError, match="not a range Special"):
        race(
            equipment={
                "range": {
                    "range": 12,
                    "angle": [True, False, False, False],
                    "damage": "d6",
                    "ap": 0,
                    "specials": {"resistance": [{}]},
                }
            }
        )


def test_the_error_names_the_holder() -> None:
    with pytest.raises(ValidationError, match="equipment 'Sword'"):
        race(equipment={"unit_specials": {"nonesuch": [{}]}})


def test_a_model_declares_instances_in_two_slots() -> None:
    loaded = race(
        model={
            "unit_specials": {"officer": [{}]},
            "assault": _ASSAULT | {"specials": {"retreat": [{}]}},
        }
    )

    assert loaded.models["soldier"].unit_specials["officer"]
    assert loaded.models["soldier"].assault.specials["retreat"]
