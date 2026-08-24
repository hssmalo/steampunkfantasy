"""Tests for Special-instance merging and unit-stat multiplicity (ADR 0024).

These build small configs rather than loading a Race: the merge reads only the
instances, and the multiplicity rules read only `upgrade_all` and how many
Model slots declare a modifier.
"""

import pytest

from spf.armies.model import Model
from spf.armies.specials import merge_specials
from spf.armies.unit import Unit
from spf.schemas.race import (
    AssaultConfig,
    EquipmentConfig,
    ModelConfig,
    OrdersConfig,
    ShakenConfig,
    UnitConfig,
    UnitStatModifierConfig,
)
from spf.schemas.special import SpecialInstance, Specials

_ASSAULT = AssaultConfig(
    strength=[1, 0, 0, 0],
    strength_die="4+",
    deflection=[1, 0, 0, 0],
    deflection_die="4+",
    damage="d4",
    ap=0,
)


def instance(text: str, *, replace: bool = False) -> SpecialInstance:
    """Build an instance identified in assertions by its prose."""
    return SpecialInstance(text=text, replace=replace)


def texts(specials: Specials, identifier: str) -> list[str | None]:
    """Read the prose of every surviving instance of one id, in chain order."""
    return [one.text for one in specials.get(identifier, [])]


# ---------------------------------------------------------------------------
# Merge: extend is the default
# ---------------------------------------------------------------------------


def test_instances_from_two_sources_accumulate() -> None:
    merged = merge_specials({"heal": [instance("unit")]}, {"heal": [instance("kit")]})

    assert texts(merged, "heal") == ["unit", "kit"]


def test_two_instances_of_one_id_are_never_merged_into_one() -> None:
    # Joining their prose is a rendering decision, and unimplementable the
    # moment the two carry different args -- which is the majority case.
    merged = merge_specials({"resistance": [instance("fire"), instance("poison")]})

    assert texts(merged, "resistance") == ["fire", "poison"]


def test_different_ids_do_not_interact() -> None:
    merged = merge_specials({"heal": [instance("a")]}, {"repair": [instance("b")]})

    assert texts(merged, "heal") == ["a"]
    assert texts(merged, "repair") == ["b"]


def test_ids_keep_the_order_they_were_first_contributed_in() -> None:
    merged = merge_specials({"heal": [instance("a")]}, {"repair": [instance("b")]})

    assert list(merged) == ["heal", "repair"]


# ---------------------------------------------------------------------------
# Merge: replace is a reset point in the chain
# ---------------------------------------------------------------------------


def test_replace_clears_what_earlier_sources_contributed() -> None:
    merged = merge_specials(
        {"to_hit": [instance("base")]}, {"to_hit": [instance("kit", replace=True)]}
    )

    assert texts(merged, "to_hit") == ["kit"]


def test_replace_keeps_what_later_sources_contribute() -> None:
    # Order-dependent by design: an order-independent version would let a
    # default equipment's replace eat a paid upgrade's contribution.
    merged = merge_specials(
        {"to_hit": [instance("base")]},
        {"to_hit": [instance("kit", replace=True)]},
        {"to_hit": [instance("paid")]},
    )

    assert texts(merged, "to_hit") == ["kit", "paid"]


def test_replace_clears_only_its_own_id() -> None:
    merged = merge_specials(
        {"to_hit": [instance("base")], "heal": [instance("keep")]},
        {"to_hit": [instance("kit", replace=True)]},
    )

    assert texts(merged, "to_hit") == ["kit"]
    assert texts(merged, "heal") == ["keep"]


def test_every_source_replacing_leaves_exactly_one_instance() -> None:
    # Four Model slots each granting the same unit Special, each replacing:
    # the printed result is one line, exactly as `dict |=` produced.
    merged = merge_specials(
        *(
            {"pre_assault_retreat": [instance(f"slot {n}", replace=True)]}
            for n in range(4)
        )
    )

    assert texts(merged, "pre_assault_retreat") == ["slot 3"]


def test_a_replacing_sibling_clears_the_instance_beside_it() -> None:
    merged = merge_specials(
        {"to_hit": [instance("first"), instance("second", replace=True)]}
    )

    assert texts(merged, "to_hit") == ["second"]


def test_merging_never_mutates_a_source() -> None:
    source: Specials = {"heal": [instance("a")]}

    merge_specials(source, {"heal": [instance("b", replace=True)]})

    assert texts(source, "heal") == ["a"]


# ---------------------------------------------------------------------------
# Merge: along the existing source chain
# ---------------------------------------------------------------------------


def equipment(  # noqa: PLR0913
    name: str,
    *,
    unit_specials: Specials | None = None,
    model_specials: Specials | None = None,
    assault_specials: Specials | None = None,
    unit: UnitStatModifierConfig | None = None,
    upgrade_all: bool | None = None,
) -> EquipmentConfig:
    """Build an equipment carrying only what it contributes to a Model or Unit."""
    return EquipmentConfig.model_validate(
        {
            "race": "goblin",
            "name": name,
            "cost": None if upgrade_all is None else {"cp": 1},
            "upgrade_all": upgrade_all,
            "unit_specials": unit_specials or {},
            "model_specials": model_specials or {},
            "assault": {"specials": assault_specials or {}},
            "unit": unit,
        }
    )


def model(
    *,
    unit_specials: Specials | None = None,
    specials: Specials | None = None,
    assault_specials: Specials | None = None,
    unit: UnitStatModifierConfig | None = None,
    upgrades: list[EquipmentConfig] | None = None,
) -> Model:
    """Build a resolved Model slot carrying only its Specials and its upgrades."""
    config = ModelConfig.model_validate(
        {
            "race": "goblin",
            "name": "Soldier",
            "equipment_limit": [],
            "equipment": [],
            "type": ["Infantry"],
            "assault": _ASSAULT.model_dump() | {"specials": assault_specials or {}},
            "unit_specials": unit_specials or {},
            "specials": specials or {},
            "unit": unit,
        }
    )
    return Model(
        name="soldier",
        config=config,
        default_equipment=[],
        upgrade_equipment=upgrades or [],
    )


def unit(
    *models: Model,
    armor: list[int] | None = None,
    specials: Specials | None = None,
) -> Unit:
    """Build a resolved Unit over the given Model slots."""
    config = UnitConfig(
        race="goblin",
        name="Squad",  # pyright: ignore[reportArgumentType]
        models=["soldier"] * len(models),
        size="Small",
        shaken=ShakenConfig(speed="slow", movement_order=["-", "-", "flee"]),
        orders=OrdersConfig(),
        armor=armor,
        specials=specials or {},
        damage_tables={},
    )
    return Unit(name="squad", config=config, models=list(models))


def test_a_models_unit_specials_stack_model_config_then_equipment() -> None:
    slot = model(
        unit_specials={"heal": [instance("model")]},
        upgrades=[equipment("kit", unit_specials={"heal": [instance("kit")]})],
    )

    assert texts(slot.unit_special_instances, "heal") == ["model", "kit"]


def test_a_models_specials_stack_model_config_then_equipment() -> None:
    slot = model(
        specials={"to_hit": [instance("model")]},
        upgrades=[equipment("kit", model_specials={"to_hit": [instance("kit")]})],
    )

    assert texts(slot.model_special_instances, "to_hit") == ["model", "kit"]


def test_an_equipment_may_replace_a_special_a_model_declares() -> None:
    slot = model(
        specials={"to_hit": [instance("model")]},
        upgrades=[
            equipment("kit", model_specials={"to_hit": [instance("kit", replace=True)]})
        ],
    )

    assert texts(slot.model_special_instances, "to_hit") == ["kit"]


def test_assault_specials_stack_model_config_then_equipment() -> None:
    slot = model(
        assault_specials={"retreat": [instance("model")]},
        upgrades=[equipment("kit", assault_specials={"retreat": [instance("kit")]})],
    )

    assert texts(slot.assault().specials, "retreat") == ["model", "kit"]


def test_a_units_specials_stack_unit_config_then_each_model() -> None:
    squad = unit(
        model(unit_specials={"heal": [instance("first")]}),
        model(unit_specials={"heal": [instance("second")]}),
        specials={"heal": [instance("unit")]},
    )

    assert texts(squad.unit_special_instances, "heal") == ["unit", "first", "second"]


def test_an_equipment_may_replace_a_special_the_unit_declares() -> None:
    # `replace` crosses levels -- the chain already does, since a Model folds
    # its Equipment's unit_specials into the Unit's set.
    squad = unit(
        model(
            upgrades=[
                equipment(
                    "kit", unit_specials={"heal": [instance("kit", replace=True)]}
                )
            ]
        ),
        specials={"heal": [instance("unit")]},
    )

    assert texts(squad.unit_special_instances, "heal") == ["kit"]


def test_replace_does_not_cross_slots() -> None:
    # `extra_damage` is legal in two slots, and they are separate chains: a
    # model-slot replace would otherwise be replacing a different rule.
    slot = model(
        assault_specials={"extra_damage": [instance("assault")]},
        specials={"extra_damage": [instance("model", replace=True)]},
    )

    assert texts(slot.assault().specials, "extra_damage") == ["assault"]
    assert texts(slot.model_special_instances, "extra_damage") == ["model"]


# ---------------------------------------------------------------------------
# Unit stat modifiers, and multiplicity
# ---------------------------------------------------------------------------


def armor_of(*models: Model, base: list[int] | None = None) -> list[int] | None:
    """Resolve the effective Unit armor over the given Model slots."""
    return unit(*models, armor=base).armor


def test_a_unit_without_modifiers_keeps_its_own_armor() -> None:
    assert armor_of(model(), base=[8, 6, 5, 4]) == [8, 6, 5, 4]


def test_a_model_declared_modifier_multiplies_by_the_slots_declaring_it() -> None:
    stat = UnitStatModifierConfig.model_validate({"armor": {"add": [1, 0, 0, 0]}})

    assert armor_of(model(unit=stat), model(unit=stat), base=[8, 6, 5, 4]) == [
        10,
        6,
        5,
        4,
    ]


def test_an_upgrade_all_equipment_counts_once_however_many_models_carry_it() -> None:
    # One wall for the Unit at +[5,0,0,0], not +[20,0,0,0] on four Models.
    wall = equipment(
        "wheeled_shieldwall",
        upgrade_all=True,
        unit=UnitStatModifierConfig.model_validate({"armor": {"add": [5, 0, 0, 0]}}),
    )
    slots = [model(upgrades=[wall]) for _ in range(4)]

    assert armor_of(*slots, base=[8, 6, 5, 4]) == [13, 6, 5, 4]


def test_a_per_model_equipment_counts_once_per_model_carrying_it() -> None:
    plate = equipment(
        "plate",
        upgrade_all=False,
        unit=UnitStatModifierConfig.model_validate({"armor": {"add": [1, 1, 0, 0]}}),
    )
    slots = [model(upgrades=[plate]) for _ in range(3)]

    assert armor_of(*slots, base=[8, 6, 5, 4]) == [11, 9, 5, 4]


def test_replace_never_multiplies() -> None:
    # Four Models each replacing armor with [6,6,6,6] can only produce
    # [6,6,6,6].
    stat = UnitStatModifierConfig.model_validate({"armor": {"replace": [6, 6, 6, 6]}})
    slots = [model(unit=stat) for _ in range(4)]

    assert armor_of(*slots, base=[8, 6, 5, 4]) == [6, 6, 6, 6]


def test_two_replaces_resolve_last_in_chain() -> None:
    first = model(
        unit=UnitStatModifierConfig.model_validate({"armor": {"replace": [1] * 4}})
    )
    second = model(
        unit=UnitStatModifierConfig.model_validate({"armor": {"replace": [2] * 4}})
    )

    assert armor_of(first, second, base=[8, 6, 5, 4]) == [2, 2, 2, 2]


def test_an_add_after_a_replace_applies_to_the_replacement() -> None:
    replacing = model(
        unit=UnitStatModifierConfig.model_validate({"armor": {"replace": [2, 2, 2, 2]}})
    )
    adding = model(
        unit=UnitStatModifierConfig.model_validate({"armor": {"add": [1, 0, 0, 0]}})
    )

    assert armor_of(replacing, adding, base=[8, 6, 5, 4]) == [3, 2, 2, 2]


def test_a_unit_with_no_armor_of_its_own_is_granted_what_is_added() -> None:
    stat = UnitStatModifierConfig.model_validate({"armor": {"add": [5, 0, 0, 0]}})

    assert armor_of(model(unit=stat)) == [5, 0, 0, 0]


def test_extend_is_meaningless_on_a_unit_stat() -> None:
    stat = UnitStatModifierConfig.model_validate({"armor": {"extend": [1]}})

    with pytest.raises(ValueError, match="extend"):
        armor_of(model(unit=stat), base=[8, 6, 5, 4])


def test_an_empty_stacker_is_rejected() -> None:
    stat = UnitStatModifierConfig.model_validate({"armor": {}})

    with pytest.raises(ValueError, match="empty Stacker"):
        armor_of(model(unit=stat), base=[8, 6, 5, 4])


def test_only_the_seven_named_stats_may_be_modified() -> None:
    # The scope fence is the field list, enforced by `extra="forbid"`.
    with pytest.raises(ValueError, match="extra_forbidden"):
        UnitStatModifierConfig.model_validate({"cost": {"add": 1}})
