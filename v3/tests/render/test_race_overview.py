"""Tests for the Race Overview product: build_overview()."""

import pytest

from spf.races import get_race
from spf.render.race_overview import RaceLink, build_overview
from spf.render.specials import SpecialLine
from spf.schemas.race import (
    AssaultConfig,
    EquipmentConfig,
    ModelConfig,
    OrdersConfig,
    RaceConfig,
    RaceMetadata,
    ShakenConfig,
    Stacker,
    UnitConfig,
    UnitStatModifierConfig,
)
from spf.schemas.special import SpecialInstance, Specials
from spf.schemas.type_aliases import Cost, ModelType
from tests.render.conftest import ART, FakeLookup

RACE = "goblin"

_ASSAULT = AssaultConfig(
    strength=[1, 0, 0, 0],
    strength_die="4+",
    deflection=[1, 0, 0, 0],
    deflection_die="4+",
    damage="d4",
    ap=0,
)


def _model_config(  # noqa: PLR0913  the fixture covers every field under test
    *,
    name: str = "Grunt",
    equipment: list[str] | None = None,
    equipment_limit: list[str] | None = None,
    types: list[ModelType] | None = None,
    cost: Cost | None = None,
    replaces: str | None = None,
    unit: UnitStatModifierConfig | None = None,
    unit_specials: Specials | None = None,
    specials: Specials | None = None,
    assault_specials: Specials | None = None,
    assault_note: str = "",
    description: str = "",
    note: str = "",
) -> ModelConfig:
    return ModelConfig(
        race=RACE,
        name=name,  # pyright: ignore[reportArgumentType]
        description=description,
        equipment_limit=equipment_limit or [],  # pyright: ignore[reportArgumentType]
        equipment=equipment or [],
        type=types or ["Infantry"],
        assault=_ASSAULT.model_copy(
            update={"specials": assault_specials or {}, "note": assault_note}
        ),
        cost=cost,
        replaces=replaces,  # pyright: ignore[reportArgumentType]
        unit_specials=unit_specials or {},
        specials=specials or {},
        unit=unit,
        note=note,
    )


def _unit_config(  # noqa: PLR0913  the fixture covers every field under test
    *,
    name: str = "Squad",
    models: list[str] | None = None,
    size: str = "small",
    cost: Cost | None = None,
    lore: str = "",
    tip: str = "",
    description: str = "",
    note: str = "",
    armor: list[int] | None = None,
    specials: Specials | None = None,
    orders: OrdersConfig | None = None,
) -> UnitConfig:
    return UnitConfig(
        race=RACE,
        name=name,  # pyright: ignore[reportArgumentType]
        description=description,
        tip=tip,
        lore=lore,
        models=models or ["grunt"],
        size=size,
        cost=cost,
        shaken=ShakenConfig(
            speed="slow", movement_order=["-", "-", "Flee"], fire_order="No weapons"
        ),
        specials=specials or {},
        note=note,
        orders=orders or OrdersConfig(),
        armor=armor,
        damage_tables={  # pyright: ignore[reportArgumentType]
            "Regular": {"rows": ["1: Fine", "2-3: Hurt", "4+: Dead"], "notes": ["Calm"]}
        },
    )


def _equipment_config(*, name: str = "Club") -> EquipmentConfig:
    return EquipmentConfig(race=RACE, name=name)  # pyright: ignore[reportArgumentType]


def _race_config(
    *,
    units: dict[str, UnitConfig] | None = None,
    models: dict[str, ModelConfig] | None = None,
    equipment: dict[str, EquipmentConfig] | None = None,
    description: str = "A race",
) -> RaceConfig:
    return RaceConfig(
        races={RACE: RaceMetadata(name="Goblin", description=description)},
        units=units or {"squad": _unit_config()},
        models=models or {"grunt": _model_config()},
        equipment=equipment or {},
    )


# --- build_overview: the title block ----------------------------------------


def test_build_overview_title_block_comes_from_the_race_metadata() -> None:
    race = _race_config(description="Small, sneaky and numerous.")

    overview = build_overview(race, stem="goblin", image_for=FakeLookup(ART))

    assert overview.stem == "goblin"
    assert overview.race == RACE
    assert overview.title == "Goblin"
    # The Race-level description is the one flavor field a record's is not.
    assert overview.description == "Small, sneaky and numerous."
    assert overview.race_image == ART


def test_build_overview_asks_the_lookup_about_the_race_and_every_unit_key() -> None:
    lookup = FakeLookup(ART)
    race = _race_config(units={"snake_cavalry": _unit_config(name="Snake Cavalry")})

    build_overview(race, stem="goblin", image_for=lookup)

    # An Asset is addressed by the TOML key, never by the display name.
    assert (RACE, RACE) in lookup.calls
    assert (RACE, "snake_cavalry") in lookup.calls
    assert (RACE, "Snake Cavalry") not in lookup.calls


# --- Unit entries -----------------------------------------------------------


def test_unit_entry_carries_the_declared_catalogue_fields() -> None:
    race = _race_config(
        units={
            "squad": _unit_config(
                name="Goblin Squad",
                armor=[10, 8, 6, 4],
                cost=Cost(mp=8),
                specials={"evasion": [SpecialInstance(args={"N": 4})]},
                orders=OrdersConfig(
                    fire={"sneak": [["Fire", "Fire"]]},
                    movement={"slow": [["360°", "F", "B"]]},
                ),
            )
        }
    )

    overview = build_overview(race, stem="goblin", image_for=FakeLookup(None))

    (unit,) = overview.units
    assert unit.key == "squad"
    assert unit.name == "Goblin Squad"
    assert unit.anchor == "unit-squad"
    assert unit.image is None
    assert unit.size == "Small"
    assert unit.armor == [10, 8, 6, 4]
    assert unit.types == ["Infantry"]
    assert unit.cost == "8mp"
    assert unit.cost_columns == ["", "8", "", "", ""]
    assert unit.points == 8
    assert unit.shaken_speed == "slow"
    assert unit.shaken_movement == ["-", "-", "Flee"]
    assert unit.shaken_fire == "No weapons"
    assert unit.specials == [SpecialLine("Evasion", "[4+]", None)]
    assert unit.fire_rows == [("sneak", ["Fire", "Fire"])]
    assert unit.movement_rows == [("slow", ["360°", "F", "B"])]
    assert unit.damage_tables == [
        ("Regular", [("1", "Fine"), ("2-3", "Hurt"), ("4+", "Dead")], ["Calm"]),
    ]


def test_unit_entry_keeps_the_flavor_text_but_drops_the_description() -> None:
    race = _race_config(
        units={
            "squad": _unit_config(
                lore="They were born in the dark.",
                tip="Field two, never one.",
                note="Counts as Infantry.",
                description="A goblin with a bow, art prompt and all.",
            )
        }
    )

    overview = build_overview(race, stem="goblin", image_for=FakeLookup(None))

    (unit,) = overview.units
    assert unit.lore == "They were born in the dark."
    assert unit.tip == "Field two, never one."
    assert unit.note == "Counts as Infantry."
    # `description` doubles as the image-generation prompt, so no entry prints it.
    assert not hasattr(unit, "description")


def test_unit_entry_with_no_cost_is_unpriced_rather_than_free() -> None:
    race = _race_config(units={"squad": _unit_config(cost=None)})

    overview = build_overview(race, stem="goblin", image_for=FakeLookup(None))

    (unit,) = overview.units
    assert unit.cost == ""
    assert unit.cost_columns == ["", "", "", "", ""]
    assert unit.points == 0


def test_unit_entry_costs_carry_no_rich_markup() -> None:
    race = _race_config(units={"squad": _unit_config(cost=Cost(ip=3, mp=2))})

    overview = build_overview(race, stem="goblin", image_for=FakeLookup(None))

    (unit,) = overview.units
    assert unit.cost == "3ip 2mp"
    assert "[" not in unit.cost


# --- Model links and common Types -------------------------------------------


def test_unit_links_each_distinct_model_of_its_declared_roster_once() -> None:
    race = _race_config(
        units={"squad": _unit_config(models=["grunt", "grunt", "grunt", "boss"])},
        models={
            "grunt": _model_config(name="Goblin Grunt"),
            "boss": _model_config(name="Goblin Boss"),
        },
    )

    overview = build_overview(race, stem="goblin", image_for=FakeLookup(None))

    (unit,) = overview.units
    assert unit.models == [
        RaceLink("Goblin Grunt", "model-grunt"),
        RaceLink("Goblin Boss", "model-boss"),
    ]
    # The roster's length is what a summary table calls the Unit's model count.
    assert unit.model_count == 4


def test_unit_types_are_the_ones_every_model_of_the_roster_shares() -> None:
    race = _race_config(
        units={"squad": _unit_config(models=["grunt", "rider"])},
        models={
            "grunt": _model_config(types=["Infantry", "Scout"]),
            "rider": _model_config(types=["Cavalry", "Scout"]),
        },
    )

    overview = build_overview(race, stem="goblin", image_for=FakeLookup(None))

    (unit,) = overview.units
    assert unit.types == ["Scout"]


def test_unit_types_print_in_the_canonical_model_type_order() -> None:
    race = _race_config(
        units={"squad": _unit_config(models=["grunt"])},
        models={"grunt": _model_config(types=["Scout", "Infantry", "Elite"])},
    )

    overview = build_overview(race, stem="goblin", image_for=FakeLookup(None))

    (unit,) = overview.units
    assert unit.types == ["Elite", "Infantry", "Scout"]


# --- Ordering (decision 9) --------------------------------------------------


def test_units_order_by_cost_with_toml_order_breaking_ties() -> None:
    race = _race_config(
        units={
            # Declared cheap-first; `sort_idx` is negated, so the dearest leads.
            "cheap": _unit_config(name="Cheap", cost=Cost(mp=1)),
            "tied_first": _unit_config(name="Tied First", cost=Cost(mp=5)),
            "tied_second": _unit_config(name="Tied Second", cost=Cost(mp=5)),
            "unpriced": _unit_config(name="Unpriced", cost=None),
        }
    )

    overview = build_overview(race, stem="goblin", image_for=FakeLookup(None))

    assert [unit.name for unit in overview.units] == [
        "Tied First",
        "Tied Second",
        "Cheap",
        "Unpriced",
    ]


# --- Anchors (decision 15) --------------------------------------------------


def test_anchors_slug_the_toml_key_under_a_section_prefix() -> None:
    race = _race_config(
        units={"giant_snake_cavalry": _unit_config(name="Giant Snake Cavalry")}
    )

    overview = build_overview(race, stem="goblin", image_for=FakeLookup(None))

    (unit,) = overview.units
    # The key, not the display name: it survives a rename, and the section
    # prefix keeps it out of the Rules Reference's `rule-*` namespace.
    assert unit.anchor == "unit-giant-snake-cavalry"
    assert not unit.anchor.startswith("rule-")


def test_a_key_shared_across_sections_gets_one_anchor_per_section() -> None:
    race = _race_config(
        units={"dwarf_infantry": _unit_config(models=["dwarf_infantry"])},
        models={"dwarf_infantry": _model_config(name="Dwarf Infantry")},
    )

    overview = build_overview(race, stem="goblin", image_for=FakeLookup(None))

    (unit,) = overview.units
    (model_link,) = unit.models
    assert unit.anchor == "unit-dwarf-infantry"
    assert model_link.anchor == "model-dwarf-infantry"


# --- Against the committed catalogue ----------------------------------------


@pytest.mark.parametrize("race_name", ["goblin", "dwarf"])
def test_build_overview_covers_every_unit_of_a_committed_race(race_name: str) -> None:
    race = get_race(race_name)  # pyright: ignore[reportArgumentType]

    overview = build_overview(race, stem=race_name, image_for=FakeLookup(None))

    assert overview.race == race_name
    assert len(overview.units) == len(race.units)
    # Every anchor addresses exactly one Unit, which is what a link rests on.
    anchors = [unit.anchor for unit in overview.units]
    assert len(set(anchors)) == len(anchors)


# --- Model entries ----------------------------------------------------------


def test_model_entry_carries_the_declared_catalogue_fields() -> None:
    race = _race_config(
        units={"squad": _unit_config(models=["boss"])},
        models={
            "boss": _model_config(
                name="Goblin Boss",
                types=["Officer", "Infantry"],
                cost=Cost(ip=1, mp=2),
                equipment_limit=["Hands:2", "Independent:∞"],
                note="Never alone.",
                description="A goblin boss, art prompt and all.",
                assault_note="Swings wide.",
            )
        },
    )

    overview = build_overview(race, stem="goblin", image_for=FakeLookup(None))

    (model,) = overview.models
    assert model.key == "boss"
    assert model.name == "Goblin Boss"
    assert model.anchor == "model-boss"
    assert model.cost == "1ip 2mp"
    assert model.cost_columns == ["1", "2", "", "", ""]
    assert model.points == 5
    # Printed in the canonical Type order, as a Unit's Type line is.
    assert model.types == ["Infantry", "Officer"]
    assert model.assault_strength == [1, 0, 0, 0]
    assert model.assault_strength_die == "4+"
    assert model.assault_deflection == [1, 0, 0, 0]
    assert model.assault_deflection_die == "4+"
    assert model.assault_damage == "d4"
    assert model.assault_ap == 0
    assert model.assault_note == "Swings wide."
    assert model.note == "Never alone."
    # `description` doubles as the image-generation prompt, so no entry prints it.
    assert not hasattr(model, "description")


def test_model_has_no_image_of_its_own() -> None:
    lookup = FakeLookup(ART)
    race = _race_config(
        units={"steampowerarmor": _unit_config(models=["steampowerarmor"])},
        models={"steampowerarmor": _model_config(name="Steampowerarmor")},
    )

    overview = build_overview(race, stem="goblin", image_for=lookup)

    (model,) = overview.models
    assert not hasattr(model, "image")
    # A Model sharing a Unit's key would otherwise answer with the Unit's art.
    assert lookup.calls.count((RACE, "steampowerarmor")) == 1


def test_model_equipment_limits_render_the_uncapped_holder_as_infinity() -> None:
    race = _race_config(
        models={"grunt": _model_config(equipment_limit=["Hands:2", "Grenades:∞"])}
    )

    overview = build_overview(race, stem="goblin", image_for=FakeLookup(None))

    (model,) = overview.models
    assert model.equipment_limits == [("Hands", "2"), ("Grenades", "∞")]


def test_model_links_each_permitted_equipment_once() -> None:
    race = _race_config(
        models={"grunt": _model_config(equipment=["club", "bow", "club"])},
        equipment={
            "club": _equipment_config(name="Club"),
            "bow": _equipment_config(name="Short Bow"),
        },
    )

    overview = build_overview(race, stem="goblin", image_for=FakeLookup(None))

    (model,) = overview.models
    # A second slot for the same Equipment is a capacity fact, which
    # `equipment_limits` carries; the link addresses one entry either way.
    assert model.equipment == [
        RaceLink("Club", "equipment-club"),
        RaceLink("Short Bow", "equipment-bow"),
    ]


# --- Inverse links (decision 3) ---------------------------------------------


def test_model_is_fielded_in_every_unit_whose_roster_names_it() -> None:
    race = _race_config(
        units={
            "squad": _unit_config(name="Squad", models=["grunt"], cost=Cost(mp=9)),
            "warband": _unit_config(name="Warband", models=["grunt", "boss"]),
        },
        models={
            "grunt": _model_config(name="Grunt"),
            "boss": _model_config(name="Boss"),
        },
    )

    overview = build_overview(race, stem="goblin", image_for=FakeLookup(None))

    by_key = {model.key: model for model in overview.models}
    # The exact inverse of the forward link a Unit entry carries.
    assert by_key["grunt"].fielded_in == [
        RaceLink("Squad", "unit-squad"),
        RaceLink("Warband", "unit-warband"),
    ]
    assert by_key["boss"].fielded_in == [RaceLink("Warband", "unit-warband")]


def test_a_unit_fielding_one_model_many_times_lists_it_once() -> None:
    race = _race_config(
        units={"squad": _unit_config(name="Squad", models=["grunt"] * 4)},
        models={"grunt": _model_config()},
    )

    overview = build_overview(race, stem="goblin", image_for=FakeLookup(None))

    (model,) = overview.models
    assert model.fielded_in == [RaceLink("Squad", "unit-squad")]


def test_replaces_renders_on_both_ends() -> None:
    race = _race_config(
        units={"squad": _unit_config(models=["grunt"])},
        models={
            "grunt": _model_config(name="Grunt"),
            "elite": _model_config(name="Elite Grunt", replaces="grunt"),
        },
    )

    overview = build_overview(race, stem="goblin", image_for=FakeLookup(None))

    by_key = {model.key: model for model in overview.models}
    assert by_key["elite"].replaces == RaceLink("Grunt", "model-grunt")
    assert by_key["elite"].replaced_by == []
    assert by_key["grunt"].replaces is None
    assert by_key["grunt"].replaced_by == [RaceLink("Elite Grunt", "model-elite")]


def test_an_upgrade_model_is_reached_through_the_model_it_replaces() -> None:
    race = _race_config(
        units={"squad": _unit_config(name="Squad", models=["grunt"])},
        models={
            "grunt": _model_config(name="Grunt"),
            "elite": _model_config(name="Elite Grunt", replaces="grunt"),
        },
    )

    overview = build_overview(race, stem="goblin", image_for=FakeLookup(None))

    (unit,) = overview.units
    by_key = {model.key: model for model in overview.models}
    # A Unit's roster names no upgrade, so `fielded_in` is empty on one and the
    # way in is the base Model's `replaced_by`.
    assert unit.models == [RaceLink("Grunt", "model-grunt")]
    assert by_key["elite"].fielded_in == []


# --- Declared deltas and Specials slots -------------------------------------


def test_model_declares_its_unit_modifiers_rather_than_stacking_them() -> None:
    race = _race_config(
        units={"squad": _unit_config(armor=[8, 6, 5, 4], models=["grunt"])},
        models={
            "grunt": _model_config(
                unit=UnitStatModifierConfig(armor=Stacker(add=[3, 2, 0, 0]))
            )
        },
    )

    overview = build_overview(race, stem="goblin", image_for=FakeLookup(None))

    (model,) = overview.models
    (unit,) = overview.units
    assert model.unit_modifiers == ["Armor: +3/+2/0/0 to its Unit"]
    # The grant has no value until a Unit is fielded under it, so the Unit's
    # own declaration is untouched.
    assert unit.armor == [8, 6, 5, 4]


def test_model_keeps_its_three_specials_slots_apart() -> None:
    race = _race_config(
        models={
            "grunt": _model_config(
                unit_specials={"evasion": [SpecialInstance(args={"N": 4})]},
                specials={"escape_artist": [SpecialInstance()]},
                assault_specials={"retreat": [SpecialInstance()]},
            )
        }
    )

    overview = build_overview(race, stem="goblin", image_for=FakeLookup(None))

    (model,) = overview.models
    assert [line.name for line in model.unit_specials] == ["Evasion"]
    assert [line.name for line in model.specials] == ["Escape Artist"]
    assert [line.name for line in model.assault_specials] == ["Retreat"]


# --- Ordering (decision 9) --------------------------------------------------


def test_models_order_by_cost_with_toml_order_breaking_ties() -> None:
    race = _race_config(
        units={"squad": _unit_config(models=["cheap"])},
        models={
            "cheap": _model_config(name="Cheap", cost=Cost(mp=1)),
            "tied_first": _model_config(name="Tied First", cost=Cost(mp=5)),
            "tied_second": _model_config(name="Tied Second", cost=Cost(mp=5)),
            "unpriced": _model_config(name="Unpriced", cost=None),
        },
    )

    overview = build_overview(race, stem="goblin", image_for=FakeLookup(None))

    assert [model.name for model in overview.models] == [
        "Tied First",
        "Tied Second",
        "Cheap",
        "Unpriced",
    ]


# --- Against the committed catalogue ----------------------------------------


@pytest.mark.parametrize("race_name", ["goblin", "dwarf"])
def test_build_overview_covers_every_model_of_a_committed_race(race_name: str) -> None:
    race = get_race(race_name)  # pyright: ignore[reportArgumentType]

    overview = build_overview(race, stem=race_name, image_for=FakeLookup(None))

    assert len(overview.models) == len(race.models)
    anchors = [model.anchor for model in overview.models]
    assert len(set(anchors)) == len(anchors)


@pytest.mark.parametrize("race_name", ["goblin", "dwarf", "ogre"])
def test_fielded_in_is_the_exact_inverse_of_every_unit_roster(race_name: str) -> None:
    race = get_race(race_name)  # pyright: ignore[reportArgumentType]

    overview = build_overview(race, stem=race_name, image_for=FakeLookup(None))

    forward = {
        (unit.anchor, link.anchor) for unit in overview.units for link in unit.models
    }
    inverse = {
        (link.anchor, model.anchor)
        for model in overview.models
        for link in model.fielded_in
    }
    assert forward == inverse
