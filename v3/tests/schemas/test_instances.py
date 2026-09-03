"""Tests for the Special instance envelope (ADR 0024)."""

import pytest
from pydantic import ValidationError

from spf.registry import load_registry
from spf.schemas.race import RaceConfig, race_slots
from spf.schemas.special import SpecialInstance
from tests.conftest import committed_args


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
# The two shapes: prose-shaped and case-shaped (ADR 0030)
# ---------------------------------------------------------------------------


def test_an_instance_is_prose_shaped_by_default() -> None:
    instance = SpecialInstance.model_validate({"text": "Only against Beasts."})

    assert instance.preamble is None
    assert instance.cases == []


def test_a_case_shaped_instance_carries_a_preamble_and_cases() -> None:
    instance = SpecialInstance.model_validate(
        {
            "preamble": "If not using aim",
            "cases": [
                {"args": {"N": 5}, "text": "at point blank range"},
                {"args": {"N": 6}, "text": "at normal and long range"},
            ],
        }
    )

    assert instance.preamble == "If not using aim"
    assert [case.args["N"] for case in instance.cases] == [5, 6]
    assert instance.cases[0].text == "at point blank range"


def test_a_case_needs_neither_text_nor_args() -> None:
    (case,) = SpecialInstance.model_validate({"cases": [{}]}).cases

    assert case.text is None
    assert case.args == {}


def test_the_case_envelope_is_closed() -> None:
    with pytest.raises(ValidationError, match="extra_forbidden"):
        SpecialInstance.model_validate({"cases": [{"N": 6}]})


def test_prose_and_cases_are_mutually_exclusive() -> None:
    with pytest.raises(ValidationError, match="either 'text' or 'cases'"):
        SpecialInstance.model_validate(
            {"text": "at point blank range", "cases": [{"args": {"N": 5}}]}
        )


def test_a_preamble_without_cases_is_rejected() -> None:
    # The message teaches the three homes prose has: cases, 'text', 'note'.
    with pytest.raises(ValidationError, match="'preamble' scopes cases"):
        SpecialInstance.model_validate({"preamble": "If not using aim"})


def test_cases_without_a_preamble_are_legal() -> None:
    instance = SpecialInstance.model_validate({"cases": [{"args": {"N": 5}}]})

    assert instance.preamble is None


# ---------------------------------------------------------------------------
# Drawing the prose slot from the rule's variants (ADR 0032)
# ---------------------------------------------------------------------------


def test_an_instance_may_draw_its_prose_from_a_variant() -> None:
    instance = SpecialInstance.model_validate({"variant": "always_loaded"})

    assert instance.variant == "always_loaded"
    assert instance.text is None


def test_a_case_may_draw_its_prose_from_a_variant() -> None:
    (case,) = SpecialInstance.model_validate(
        {"cases": [{"variant": "point_blank", "args": {"N": 4}}]}
    ).cases

    assert case.variant == "point_blank"


def test_a_variant_on_a_case_shaped_instance_is_its_preamble() -> None:
    # The shape decides the role: with cases, the prose slot is the preamble,
    # so one `variant` field needs no second spelling.
    instance = SpecialInstance.model_validate(
        {"variant": "choose_one_hex", "cases": [{"args": {"N": 5}}]}
    )

    assert instance.variant == "choose_one_hex"
    assert instance.preamble is None


def test_a_variant_named_like_a_ref_is_rejected() -> None:
    # A variant id is a bare Identifier the rule owns, so a two-segment name
    # is a shape error rather than a lookup that happens to miss.
    with pytest.raises(ValidationError):
        SpecialInstance.model_validate({"variant": "special.always_loaded"})


def test_a_variant_beside_text_is_rejected() -> None:
    # A variant is a way of spelling `text`, not a layer under it.
    with pytest.raises(ValidationError, match="spells the prose slot"):
        SpecialInstance.model_validate(
            {"variant": "always_loaded", "text": "Always treated as loaded"}
        )


def test_a_variant_beside_a_preamble_is_rejected() -> None:
    with pytest.raises(ValidationError, match="spells the prose slot"):
        SpecialInstance.model_validate(
            {
                "variant": "choose_one_hex",
                "preamble": "Choose one hex",
                "cases": [{"args": {"N": 5}}],
            }
        )


def test_a_case_carrying_both_a_variant_and_text_is_rejected() -> None:
    with pytest.raises(ValidationError, match="spells the prose slot"):
        SpecialInstance.model_validate(
            {"cases": [{"variant": "point_blank", "text": "at point blank"}]}
        )


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
    "size": "small",
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
    # The arguments are read out of `rules/` rather than written here: this
    # test is about an Instance surviving the load, not about what the
    # Resistance rule currently takes.
    args = committed_args(load_registry(), "resistance")

    loaded = race(unit={"specials": {"resistance": [{"args": args}]}})

    (instance,) = loaded.units["squad"].specials["resistance"]
    assert instance.args == args


def test_an_unknown_special_id_fails_the_race() -> None:
    with pytest.raises(ValidationError, match="is not a Special id"):
        race(unit={"specials": {"resistanse": [{}]}})  # typos: ignore


def test_a_unit_special_in_the_wrong_slot_fails_the_race() -> None:
    with pytest.raises(ValidationError, match="not a unit Special"):
        race(
            unit={
                "specials": {
                    "assault_extra_damage": [
                        {"args": {"version": "token.poison", "N": 6, "M": 2}}
                    ]
                }
            }
        )


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


# ---------------------------------------------------------------------------
# The walk over a Race's Slots
# ---------------------------------------------------------------------------


def test_race_slots_yields_every_slot_a_race_holds() -> None:
    """A distinct id per Slot, so a Slot dropped from the walk fails here.

    Every surface asking what rules a Race reaches -- the countdowns, a Rules
    Reference built off a `RaceConfig` -- walks through here, so a missing
    Slot would silently shrink all of them at once.
    """
    loaded = race(
        unit={"specials": {"officer": [{}]}},
        model={
            "unit_specials": {"chase": [{}]},
            "specials": {"escape_artist": [{}]},
            "assault": _ASSAULT | {"specials": {"retreat": [{}]}},
        },
        equipment={
            "unit_specials": {"trap": [{}]},
            "model_specials": {"fog": [{}]},
            "assault": {"specials": {"weakest_armor": [{}]}},
            "range": {
                "range": 12,
                "angle": [True, False, False, False],
                "damage": "d6",
                "ap": 0,
                "specials": {"forced_break": [{}]},
            },
        },
    )

    assert [list(slot) for slot in race_slots(loaded)] == [
        ["officer"],
        ["chase"],
        ["escape_artist"],
        ["retreat"],
        ["trap"],
        ["fog"],
        ["weakest_armor"],
        ["forced_break"],
    ]


def test_a_model_declares_instances_in_two_slots() -> None:
    loaded = race(
        model={
            "unit_specials": {"officer": [{}]},
            "assault": _ASSAULT | {"specials": {"retreat": [{}]}},
        }
    )

    assert loaded.models["soldier"].unit_specials["officer"]
    assert loaded.models["soldier"].assault.specials["retreat"]


# ---------------------------------------------------------------------------
# The vocabularies the modifier registries own
# ---------------------------------------------------------------------------


def test_a_unit_names_a_size_the_registry_declares() -> None:
    assert race(unit={"size": "huge"}).units["squad"].size == "huge"


def test_a_size_spelled_as_a_display_name_fails_the_race() -> None:
    with pytest.raises(ValidationError, match="'Medium' is not a size"):
        race(unit={"size": "Medium"})


def test_an_unknown_shaken_speed_fails_the_race() -> None:
    with pytest.raises(ValidationError, match="'crawling' is not a speed"):
        race(unit={"shaken": {"speed": "crawling", "movement_order": ["-"]}})


def test_an_unknown_speed_in_an_orders_table_fails_the_race() -> None:
    with pytest.raises(ValidationError, match="'dawdle' is not a speed"):
        race(unit={"orders": {"movement": {"dawdle": [["-"]]}}})


def test_an_unknown_speed_in_gained_orders_fails_the_race() -> None:
    with pytest.raises(ValidationError, match="'dawdle' is not a speed"):
        race(equipment={"orders_gained": {"fire": {"dawdle": [["Fire"]]}}})
