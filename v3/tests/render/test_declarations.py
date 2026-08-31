"""Tests for the declared-constraint formatters in `spf.render.declarations`."""

from spf.render.declarations import (
    assault_modifier_lines,
    limit_rows,
    modifier_line,
    requirement_lines,
    unit_modifier_lines,
)
from spf.schemas.race import EquipmentAssaultConfig, Stacker, UnitStatModifierConfig
from spf.schemas.type_aliases import ArmorPenetration, EquipmentLimit, Requirement

# --- Holder limits ---------------------------------------------------------


def test_limit_rows_pair_each_holder_with_its_limit() -> None:
    limits = [EquipmentLimit(holder="Hands", limit=2)]

    assert limit_rows(limits) == [("Hands", "2")]


def test_an_unlimited_holder_renders_back_as_the_infinity_it_was_written_as() -> None:
    limits = [EquipmentLimit(holder="Independent", limit=999)]

    assert limit_rows(limits) == [("Independent", "∞")]


def test_limit_rows_keep_declaration_order() -> None:
    limits = [
        EquipmentLimit(holder="Independent", limit=999),
        EquipmentLimit(holder="Hands", limit=2),
    ]

    assert [holder for holder, _ in limit_rows(limits)] == ["Independent", "Hands"]


# --- Requirements ----------------------------------------------------------
#
# `requires` is CNF: every group must be satisfied, and a group is satisfied by
# any one of its members (see `spf.armies.build`). So one line per group, and
# the caller joins the lines conjunctively.


def test_a_holder_requirement_names_the_capacity_it_claims() -> None:
    requires = [[Requirement(key="Hands", value=2)]]

    assert requirement_lines(requires) == ["2 Hands"]


def test_a_type_requirement_names_the_model_type_it_demands() -> None:
    requires = [[Requirement(key="type", value="Orlf")]]

    assert requirement_lines(requires) == ["Model type Orlf"]


def test_the_alternatives_within_one_group_read_as_a_choice() -> None:
    requires = [
        [Requirement(key="Hands", value=2)],
        [
            Requirement(key="type", value="Infantry"),
            Requirement(key="type", value="Cavalry"),
        ],
    ]

    assert requirement_lines(requires) == ["2 Hands", "Model type Infantry or Cavalry"]


def test_a_group_mixing_a_holder_with_a_type_spells_both_out() -> None:
    requires = [
        [
            Requirement(key="Grenades", value=1),
            Requirement(key="type", value="Infantry"),
        ]
    ]

    assert requirement_lines(requires) == ["1 Grenades or Model type Infantry"]


def test_no_requirements_is_no_lines() -> None:
    assert requirement_lines([]) == []


# --- Declared deltas -------------------------------------------------------


def test_an_added_delta_signs_the_values_it_grants() -> None:
    stacker = Stacker[list[int]](add=[3, 2, 0, 0])

    assert modifier_line("Armor", stacker, target="its Unit") == (
        "Armor: +3/+2/0/0 to its Unit"
    )


def test_a_delta_with_no_target_states_the_change_alone() -> None:
    assert modifier_line("AP", Stacker[int](add=4)) == "AP: +4"


def test_a_replacement_reads_as_setting_the_value() -> None:
    assert modifier_line("Damage", Stacker[str](replace="d12")) == "Damage: set to d12"


def test_an_extension_reads_as_adding_to_the_end() -> None:
    stacker = Stacker[list[int]](extend=[1, 1])

    assert modifier_line("Armor", stacker) == "Armor: extended by 1, 1"


def test_a_negative_delta_keeps_its_own_sign() -> None:
    assert modifier_line("AP", Stacker[int](add=-2)) == "AP: -2"


def test_an_empty_stacker_declares_nothing() -> None:
    # Resolving one is an error; a catalogue only reports what it was given.
    assert modifier_line("Armor", Stacker[list[int]]()) == ""


def test_unit_modifiers_name_the_unit_the_grant_lands_on() -> None:
    unit = UnitStatModifierConfig(armor=Stacker[list[int]](add=[5, 0, 0, 0]))

    assert unit_modifier_lines(unit) == ["Armor: +5/0/0/0 to its Unit"]


def test_a_record_modifying_nothing_has_no_modifier_lines() -> None:
    assert unit_modifier_lines(None) == []
    assert unit_modifier_lines(UnitStatModifierConfig()) == []


def test_assault_modifiers_label_every_field_they_touch() -> None:
    assault = EquipmentAssaultConfig(
        strength=Stacker[list[int]](add=[1, 0, 0, 0]),
        deflection_die=Stacker[str](replace="4+"),
        ap=Stacker[ArmorPenetration](replace=5),
    )

    assert assault_modifier_lines(assault) == [
        "Strength: +1/0/0/0",
        "Deflection die: set to 4+",
        "AP: set to 5",
    ]


def test_an_equipment_with_no_assault_declares_no_assault_modifiers() -> None:
    assert assault_modifier_lines(None) == []
