"""Tests for the Race Overview product: build_overview()."""

import pytest

from spf.races import get_race
from spf.render.race_overview import RaceLink, RaceOverview, build_overview
from spf.render.specials import SpecialLine, special_lines
from spf.schemas.race import (
    AssaultConfig,
    EquipmentAssaultConfig,
    EquipmentConfig,
    EquipmentRangeConfig,
    ModelConfig,
    OrdersConfig,
    RaceConfig,
    RaceMetadata,
    ShakenConfig,
    SpawnConfig,
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


def _equipment_config(  # noqa: PLR0913  the fixture covers every field under test
    *,
    name: str = "Club",
    cost: Cost | None = None,
    upgrade_all: bool | None = None,
    requires: list[list[str]] | None = None,
    assault: EquipmentAssaultConfig | None = None,
    ranged: EquipmentRangeConfig | None = None,
    unit_specials: Specials | None = None,
    model_specials: Specials | None = None,
    unit: UnitStatModifierConfig | None = None,
    orders_gained: OrdersConfig | None = None,
    description: str = "",
    note: str = "",
) -> EquipmentConfig:
    return EquipmentConfig(
        race=RACE,
        name=name,  # pyright: ignore[reportArgumentType]
        description=description,
        cost=cost,
        upgrade_all=upgrade_all,
        requires=requires or [],  # pyright: ignore[reportArgumentType]
        assault=assault,
        range=ranged,
        unit_specials=unit_specials or {},
        model_specials=model_specials or {},
        unit=unit,
        note=note,
        orders_gained=orders_gained,
    )


def _race_config(
    *,
    units: dict[str, UnitConfig] | None = None,
    models: dict[str, ModelConfig] | None = None,
    equipment: dict[str, EquipmentConfig] | None = None,
    spawns: dict[str, SpawnConfig] | None = None,
    description: str = "A race",
) -> RaceConfig:
    return RaceConfig(
        races={RACE: RaceMetadata(name="Goblin", description=description)},
        units=units or {"squad": _unit_config()},
        models=models or {"grunt": _model_config()},
        equipment=equipment or {},
        spawns=spawns or {},
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

    # Without a Rules Reference a Special line is its heading and text alone,
    # which is what this inventory of the declared fields is about.
    overview = build_overview(
        race, stem="goblin", image_for=FakeLookup(None), rules=False
    )

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


# --- Equipment entries ------------------------------------------------------


def test_equipment_entry_carries_the_declared_catalogue_fields() -> None:
    race = _race_config(
        equipment={
            "short_bow": _equipment_config(
                name="Short Bow",
                cost=Cost(ip=1, mp=2),
                upgrade_all=False,
                note="Two hands to draw.",
                description="A short bow, art prompt and all.",
            )
        }
    )

    overview = build_overview(race, stem="goblin", image_for=FakeLookup(None))

    (equip,) = overview.equipment
    assert equip.key == "short_bow"
    assert equip.name == "Short Bow"
    assert equip.anchor == "equipment-short-bow"
    assert equip.cost == "1ip 2mp"
    assert equip.cost_columns == ["1", "2", "", "", ""]
    assert equip.note == "Two hands to draw."
    # `description` doubles as the image-generation prompt, so no entry prints it.
    assert not hasattr(equip, "description")
    # An Equipment has no art of its own.
    assert not hasattr(equip, "image")


def test_equipment_has_no_image_of_its_own() -> None:
    lookup = FakeLookup(ART)
    race = _race_config(equipment={"club": _equipment_config(name="Club")})

    build_overview(race, stem="goblin", image_for=lookup)

    assert (RACE, "club") not in lookup.calls


# --- Pricing (decision 4, ADR 0026) -----------------------------------------


def test_a_unit_fixture_says_it_is_charged_once_for_the_whole_unit() -> None:
    race = _race_config(
        equipment={
            "banner": _equipment_config(
                name="Banner", cost=Cost(mp=5), upgrade_all=True
            )
        }
    )

    overview = build_overview(race, stem="goblin", image_for=FakeLookup(None))

    (equip,) = overview.equipment
    assert equip.upgrade_all is True
    assert equip.pricing == "Unit Fixture: charged once for the whole Unit"


def test_other_upgrade_equipment_says_it_is_charged_per_model() -> None:
    race = _race_config(
        equipment={
            "bow": _equipment_config(name="Bow", cost=Cost(mp=2), upgrade_all=False)
        }
    )

    overview = build_overview(race, stem="goblin", image_for=FakeLookup(None))

    (equip,) = overview.equipment
    assert equip.upgrade_all is False
    assert equip.pricing == "Charged for each Model carrying it"


def test_unpriced_default_equipment_states_no_pricing() -> None:
    race = _race_config(equipment={"club": _equipment_config(name="Club")})

    overview = build_overview(race, stem="goblin", image_for=FakeLookup(None))

    (equip,) = overview.equipment
    # Default Equipment is never bought, so there is no pricing rule to state.
    assert equip.upgrade_all is None
    assert equip.cost == ""
    assert equip.pricing == ""


# --- Requirements are a conjunction (decision 4) ----------------------------


def test_every_requirement_line_has_to_hold() -> None:
    race = _race_config(
        equipment={
            "great_axe": _equipment_config(
                name="Great Axe", requires=[["Hands:2"], ["type:Orlf", "type:Dwalf"]]
            )
        }
    )

    overview = build_overview(race, stem="goblin", image_for=FakeLookup(None))

    (equip,) = overview.equipment
    # Both lines must hold: 2 Hands *and* one of the two Model types. Joining
    # these with an "or" would let the catalogue promise a build the engine
    # rejects.
    assert equip.requires_all == ["2 Hands", "Model type Orlf or Dwalf"]


def test_a_requirement_group_offers_a_choice_within_its_own_line() -> None:
    race = _race_config(
        equipment={
            "sidearm": _equipment_config(
                name="Sidearm", requires=[["Hands:1", "type:Officer"]]
            )
        }
    )

    overview = build_overview(race, stem="goblin", image_for=FakeLookup(None))

    (equip,) = overview.equipment
    assert equip.requires_all == ["1 Hands or Model type Officer"]


def test_equipment_with_no_requirements_lists_none() -> None:
    race = _race_config(equipment={"club": _equipment_config()})

    overview = build_overview(race, stem="goblin", image_for=FakeLookup(None))

    (equip,) = overview.equipment
    assert equip.requires_all == []


# --- Inverse links (decision 3) ---------------------------------------------


def test_equipment_is_carried_by_every_model_permitting_it() -> None:
    race = _race_config(
        units={"squad": _unit_config(models=["grunt"])},
        models={
            "grunt": _model_config(name="Grunt", equipment=["club"], cost=Cost(mp=9)),
            "boss": _model_config(name="Boss", equipment=["club", "bow"]),
        },
        equipment={
            "club": _equipment_config(name="Club"),
            "bow": _equipment_config(name="Bow"),
        },
    )

    overview = build_overview(race, stem="goblin", image_for=FakeLookup(None))

    by_key = {equip.key: equip for equip in overview.equipment}
    # The exact inverse of the forward link a Model entry carries, read in the
    # order the Models section prints.
    assert by_key["club"].carried_by == [
        RaceLink("Grunt", "model-grunt"),
        RaceLink("Boss", "model-boss"),
    ]
    assert by_key["bow"].carried_by == [RaceLink("Boss", "model-boss")]


def test_a_model_with_two_slots_for_one_equipment_carries_it_once() -> None:
    race = _race_config(
        models={"grunt": _model_config(name="Grunt", equipment=["club", "club"])},
        equipment={"club": _equipment_config(name="Club")},
    )

    overview = build_overview(race, stem="goblin", image_for=FakeLookup(None))

    (equip,) = overview.equipment
    assert equip.carried_by == [RaceLink("Grunt", "model-grunt")]


# --- Declared deltas (decision 1) -------------------------------------------


def test_equipment_declares_its_assault_and_unit_deltas() -> None:
    race = _race_config(
        units={"squad": _unit_config(armor=[8, 6, 5, 4], models=["grunt"])},
        equipment={
            "shield": _equipment_config(
                name="Shield",
                assault=EquipmentAssaultConfig(
                    strength=Stacker(add=[1, 0, 0, 0]),
                    damage=Stacker(replace="d12"),
                ),
                unit=UnitStatModifierConfig(armor=Stacker(add=[3, 2, 0, 0])),
            )
        },
    )

    overview = build_overview(race, stem="goblin", image_for=FakeLookup(None))

    (equip,) = overview.equipment
    (unit,) = overview.units
    assert equip.assault_modifiers == ["Strength: +1/0/0/0", "Damage: set to d12"]
    assert equip.unit_modifiers == ["Armor: +3/+2/0/0 to its Unit"]
    # A delta has no value until the Equipment is carried into a fielded Unit,
    # so nothing is stacked onto the Unit's own declaration.
    assert unit.armor == [8, 6, 5, 4]


def test_equipment_with_neither_assault_nor_unit_deltas_declares_none() -> None:
    race = _race_config(equipment={"club": _equipment_config()})

    overview = build_overview(race, stem="goblin", image_for=FakeLookup(None))

    (equip,) = overview.equipment
    assert equip.assault_modifiers == []
    assert equip.unit_modifiers == []


# --- Orders stay unmerged (decision 7, ADR 0007) ----------------------------


def test_orders_gained_land_on_the_equipment_rather_than_the_unit() -> None:
    race = _race_config(
        units={
            "squad": _unit_config(
                models=["grunt"],
                orders=OrdersConfig(movement={"slow": [["F", "F"]]}),
            )
        },
        models={"grunt": _model_config(equipment=["jetpack"])},
        equipment={
            "jetpack": _equipment_config(
                name="Jetpack",
                orders_gained=OrdersConfig(
                    fire={"sneak": [["Fire", "-"]]},
                    movement={"fast": [["F", "F", "F"]]},
                ),
            )
        },
    )

    overview = build_overview(race, stem="goblin", image_for=FakeLookup(None))

    (equip,) = overview.equipment
    (unit,) = overview.units
    assert equip.orders_gained_movement_rows == [("fast", ["F", "F", "F"])]
    assert equip.orders_gained_fire_rows == [("sneak", ["Fire", "-"])]
    # `orders_gained` is additive (ADR 0007), and only a fielded Unit has the
    # fixed loadout a merged table would describe.
    assert unit.movement_rows == [("slow", ["F", "F"])]
    assert unit.fire_rows == []


def test_equipment_granting_no_orders_has_no_rows() -> None:
    race = _race_config(equipment={"club": _equipment_config()})

    overview = build_overview(race, stem="goblin", image_for=FakeLookup(None))

    (equip,) = overview.equipment
    assert equip.orders_gained_movement_rows == []
    assert equip.orders_gained_fire_rows == []


# --- The range profile ------------------------------------------------------


def test_ranged_equipment_carries_its_whole_range_profile() -> None:
    race = _race_config(
        equipment={
            "bow": _equipment_config(
                name="Bow",
                ranged=EquipmentRangeConfig(
                    range=12,
                    angle=[True, True, False, False],
                    damage="d8",
                    ap=2,
                    specials={"burst": [SpecialInstance(args={"N": 3})]},
                    note="Reload after firing.",
                ),
            )
        }
    )

    overview = build_overview(race, stem="goblin", image_for=FakeLookup(None))

    (equip,) = overview.equipment
    assert equip.range == 12
    assert equip.range_angle == [True, True, False, False]
    assert equip.range_damage == "d8"
    assert equip.range_ap == 2
    assert [line.name for line in equip.range_specials] == ["Burst"]
    assert equip.range_note == "Reload after firing."


def test_rangeless_equipment_has_no_range_profile() -> None:
    race = _race_config(equipment={"club": _equipment_config()})

    overview = build_overview(race, stem="goblin", image_for=FakeLookup(None))

    (equip,) = overview.equipment
    # `range is None` is the single test of whether an Equipment shoots.
    assert equip.range is None
    assert equip.range_angle == []
    assert equip.range_damage is None
    assert equip.range_ap is None
    assert equip.range_specials == []
    assert equip.range_note == ""


def test_each_note_stays_with_the_profile_it_qualifies() -> None:
    race = _race_config(
        equipment={
            "bow": _equipment_config(
                name="Bow",
                note="Goblin-made.",
                assault=EquipmentAssaultConfig(
                    damage=Stacker(replace="d4"), note="Clumsy in melee."
                ),
                ranged=EquipmentRangeConfig(
                    range=12, angle=[True], damage="d8", ap=0, note="Reload."
                ),
            )
        }
    )

    overview = build_overview(race, stem="goblin", image_for=FakeLookup(None))

    (equip,) = overview.equipment
    assert equip.note == "Goblin-made."
    assert equip.assault_note == "Clumsy in melee."
    assert equip.range_note == "Reload."


# --- Specials slots ---------------------------------------------------------


def test_equipment_keeps_its_four_specials_slots_apart() -> None:
    race = _race_config(
        equipment={
            "bow": _equipment_config(
                name="Bow",
                unit_specials={"evasion": [SpecialInstance(args={"N": 4})]},
                model_specials={"escape_artist": [SpecialInstance()]},
                assault=EquipmentAssaultConfig(
                    specials={"retreat": [SpecialInstance()]}
                ),
                ranged=EquipmentRangeConfig(
                    range=12,
                    angle=[True],
                    damage="d8",
                    ap=0,
                    specials={"burst": [SpecialInstance(args={"N": 3})]},
                ),
            )
        }
    )

    overview = build_overview(race, stem="goblin", image_for=FakeLookup(None))

    (equip,) = overview.equipment
    assert [line.name for line in equip.unit_specials] == ["Evasion"]
    assert [line.name for line in equip.model_specials] == ["Escape Artist"]
    assert [line.name for line in equip.assault_specials] == ["Retreat"]
    assert [line.name for line in equip.range_specials] == ["Burst"]


# --- Ordering (decision 9) --------------------------------------------------


def test_equipment_orders_by_cost_with_toml_order_breaking_ties() -> None:
    race = _race_config(
        equipment={
            "cheap": _equipment_config(
                name="Cheap", cost=Cost(mp=1), upgrade_all=False
            ),
            "tied_first": _equipment_config(
                name="Tied First", cost=Cost(mp=5), upgrade_all=False
            ),
            "tied_second": _equipment_config(
                name="Tied Second", cost=Cost(mp=5), upgrade_all=False
            ),
            "unpriced": _equipment_config(name="Unpriced"),
        }
    )

    overview = build_overview(race, stem="goblin", image_for=FakeLookup(None))

    assert [equip.name for equip in overview.equipment] == [
        "Tied First",
        "Tied Second",
        "Cheap",
        "Unpriced",
    ]


# --- Against the committed catalogue ----------------------------------------


@pytest.mark.parametrize("race_name", ["goblin", "dwarf"])
def test_build_overview_covers_every_equipment_of_a_committed_race(
    race_name: str,
) -> None:
    race = get_race(race_name)  # pyright: ignore[reportArgumentType]

    overview = build_overview(race, stem=race_name, image_for=FakeLookup(None))

    assert len(overview.equipment) == len(race.equipment)
    anchors = [equip.anchor for equip in overview.equipment]
    assert len(set(anchors)) == len(anchors)


@pytest.mark.parametrize("race_name", ["goblin", "dwarf", "ogre"])
def test_carried_by_is_the_exact_inverse_of_every_model_loadout(
    race_name: str,
) -> None:
    race = get_race(race_name)  # pyright: ignore[reportArgumentType]

    overview = build_overview(race, stem=race_name, image_for=FakeLookup(None))

    forward = {
        (model.anchor, link.anchor)
        for model in overview.models
        for link in model.equipment
    }
    inverse = {
        (link.anchor, equip.anchor)
        for equip in overview.equipment
        for link in equip.carried_by
    }
    assert forward == inverse


# --- Spawn entries ----------------------------------------------------------


def test_spawns_keep_their_toml_declaration_order() -> None:
    race = _race_config(
        units={
            "squad": _unit_config(),
            "snake": _unit_config(name="Snake"),
            "rat": _unit_config(name="Rat"),
        },
        spawns={
            "tiny_snake": SpawnConfig(unit="snake"),  # pyright: ignore[reportArgumentType]
            "mechanical_rat": SpawnConfig(unit="rat"),  # pyright: ignore[reportArgumentType]
        },
    )

    overview = build_overview(race, stem="goblin", image_for=FakeLookup(None))

    assert [spawn.key for spawn in overview.spawns] == ["tiny_snake", "mechanical_rat"]


def test_a_spawn_links_to_the_unit_and_equipment_it_places() -> None:
    race = _race_config(
        units={"squad": _unit_config(), "snake": _unit_config(name="Snake")},
        equipment={"fang": _equipment_config(name="Fang")},
        spawns={
            "tiny_snake": SpawnConfig(
                unit="snake",  # pyright: ignore[reportArgumentType]
                equipment=["fang"],  # pyright: ignore[reportArgumentType]
                copy_equipment=True,
            )
        },
    )

    (spawn,) = build_overview(race, stem="goblin", image_for=FakeLookup(None)).spawns

    assert spawn.anchor == "spawn-tiny-snake"
    assert spawn.unit == RaceLink(name="Snake", anchor="unit-snake")
    assert spawn.equipment == [RaceLink(name="Fang", anchor="equipment-fang")]
    assert spawn.copy_equipment is True


def test_a_race_with_no_spawns_has_an_empty_section() -> None:
    overview = build_overview(_race_config(), stem="goblin", image_for=FakeLookup(None))

    assert overview.spawns == []


# --- Spawn links beside the Specials that place them ------------------------


def _spawning(spawn_id: str, *, rule: str = "spawn") -> Specials:
    """One spawning instance, its spawn read off the front of its own prose."""
    return {rule: [SpecialInstance(text=f"{spawn_id}: place it somewhere")]}


def test_a_unit_links_to_the_spawn_its_specials_place() -> None:
    race = _race_config(
        units={
            "cavalry": _unit_config(name="Cavalry", specials=_spawning("tiny_snake")),
            "snake": _unit_config(name="Snake"),
        },
        spawns={"tiny_snake": SpawnConfig(unit="snake")},  # pyright: ignore[reportArgumentType]
    )

    overview = build_overview(race, stem="goblin", image_for=FakeLookup(None))
    cavalry = next(unit for unit in overview.units if unit.key == "cavalry")

    assert cavalry.spawn_links == [
        RaceLink(name="tiny_snake", anchor="spawn-tiny-snake")
    ]


def test_the_spawn_link_leaves_the_interpolated_prose_untouched() -> None:
    specials = _spawning("tiny_snake")
    race = _race_config(
        units={
            "cavalry": _unit_config(name="Cavalry", specials=specials),
            "snake": _unit_config(name="Snake"),
        },
        spawns={"tiny_snake": SpawnConfig(unit="snake")},  # pyright: ignore[reportArgumentType]
    )

    overview = build_overview(race, stem="goblin", image_for=FakeLookup(None))
    cavalry = next(unit for unit in overview.units if unit.key == "cavalry")

    # The link travels beside the line; the spawn id stays in the prose that
    # names it, exactly as `special_lines` rendered it.
    assert overview.rules is not None
    assert cavalry.specials == special_lines(
        specials, anchor_for=overview.rules.anchor_for
    )
    assert "tiny_snake: place it somewhere" in cavalry.specials[0].text


def test_a_model_links_to_the_spawns_of_either_of_its_slots() -> None:
    race = _race_config(
        units={
            "squad": _unit_config(models=["tinkerer"]),
            "rat": _unit_config(name="Rat", models=["tinkerer"]),
        },
        models={
            "tinkerer": _model_config(
                name="Tinkerer",
                unit_specials=_spawning("mechanical_rat"),
                specials=_spawning("mechanical_rat", rule="not_yet_dead"),
            )
        },
        spawns={"mechanical_rat": SpawnConfig(unit="rat")},  # pyright: ignore[reportArgumentType]
    )

    (model,) = build_overview(race, stem="gnome", image_for=FakeLookup(None)).models

    # Both slots name the same spawn, and one link is what the reader needs.
    assert model.spawn_links == [
        RaceLink(name="mechanical_rat", anchor="spawn-mechanical-rat")
    ]


def test_equipment_links_to_the_spawn_its_range_special_places() -> None:
    race = _race_config(
        units={"squad": _unit_config(), "bots": _unit_config(name="Bots")},
        equipment={
            "mortar": _equipment_config(
                name="Mortar",
                ranged=EquipmentRangeConfig(
                    range=4,
                    angle=[True, True, True, True],
                    damage="d6",
                    ap=1,
                    specials=_spawning("assault_bots"),
                ),
            )
        },
        spawns={"assault_bots": SpawnConfig(unit="bots")},  # pyright: ignore[reportArgumentType]
    )

    (equip,) = build_overview(race, stem="gnome", image_for=FakeLookup(None)).equipment

    assert equip.spawn_links == [
        RaceLink(name="assault_bots", anchor="spawn-assault-bots")
    ]


def test_a_record_placing_no_spawn_links_to_none() -> None:
    overview = build_overview(_race_config(), stem="goblin", image_for=FakeLookup(None))

    assert overview.units[0].spawn_links == []
    assert overview.models[0].spawn_links == []


def test_a_spawned_unit_says_which_spawn_places_it() -> None:
    race = _race_config(
        units={"squad": _unit_config(), "snake": _unit_config(name="Snake")},
        spawns={"tiny_snake": SpawnConfig(unit="snake")},  # pyright: ignore[reportArgumentType]
    )

    overview = build_overview(race, stem="goblin", image_for=FakeLookup(None))
    snake = next(unit for unit in overview.units if unit.key == "snake")

    assert snake.spawned_by == [RaceLink(name="tiny_snake", anchor="spawn-tiny-snake")]
    assert overview.units[0].spawned_by == []


# --- Against the committed catalogue ----------------------------------------


@pytest.mark.parametrize("race_name", ["goblin", "ork", "gnome", "darkelf"])
def test_every_spawn_of_a_committed_race_is_reachable(race_name: str) -> None:
    race = get_race(race_name)  # pyright: ignore[reportArgumentType]
    overview = build_overview(race, stem=race_name, image_for=FakeLookup(None))

    assert [spawn.key for spawn in overview.spawns] == list(race.spawns)
    # Every Spawn the catalogue declares is placed by some record's Specials,
    # so no spawn entry is an island the document never points at.
    linked = {
        link.anchor
        for entries in (overview.units, overview.models, overview.equipment)
        for entry in entries
        for link in entry.spawn_links
    }
    assert linked == {spawn.anchor for spawn in overview.spawns}


# --- The Rules Reference (decision 6) ---------------------------------------


def _every_special_line(overview: RaceOverview) -> list[SpecialLine]:
    """Every Special line the four sections print, whatever Slot it came from."""
    lines: list[SpecialLine] = []
    for unit in overview.units:
        lines += unit.specials
    for model in overview.models:
        lines += [*model.unit_specials, *model.specials, *model.assault_specials]
    for equip in overview.equipment:
        lines += [
            *equip.unit_specials,
            *equip.model_specials,
            *equip.assault_specials,
            *equip.range_specials,
        ]
    return lines


def test_a_special_line_links_into_the_rules_reference() -> None:
    race = _race_config(
        units={
            "squad": _unit_config(
                specials={"evasion": [SpecialInstance(args={"N": 4})]}
            )
        }
    )

    overview = build_overview(race, stem="goblin", image_for=FakeLookup(None))

    assert overview.rules is not None
    (line,) = overview.units[0].specials
    # The line takes its anchor from the very entry it points at, so the two
    # cannot disagree.
    assert line.anchor == overview.rules.anchor_for("evasion")
    assert line.anchor is not None


def test_no_rules_leaves_out_the_reference_and_every_link_into_it() -> None:
    race = _race_config(
        units={
            "squad": _unit_config(
                specials={"evasion": [SpecialInstance(args={"N": 4})]}
            )
        }
    )

    overview = build_overview(
        race, stem="goblin", image_for=FakeLookup(None), rules=False
    )

    assert overview.rules is None
    assert [line.anchor for line in _every_special_line(overview)] == [None]


def test_a_record_keyed_like_a_rule_still_anchors_under_its_section() -> None:
    race = _race_config(units={"rule_terror": _unit_config(name="Rule Terror")})

    overview = build_overview(race, stem="goblin", image_for=FakeLookup(None))

    assert overview.units[0].anchor == "unit-rule-terror"


@pytest.mark.parametrize("race_name", ["goblin", "dwarf", "gnome"])
def test_every_special_a_section_prints_reaches_the_rules_reference(
    race_name: str,
) -> None:
    overview = build_overview(
        get_race(race_name),  # pyright: ignore[reportArgumentType]
        stem=race_name,
        image_for=FakeLookup(None),
    )

    assert overview.rules is not None
    entries = set(overview.rules.anchors.values())
    lines = _every_special_line(overview)
    assert lines
    # A Special printed on a record the walk never seeded would render a link
    # into nothing.
    assert {line.anchor for line in lines} <= entries


@pytest.mark.parametrize("race_name", ["goblin", "dwarf", "gnome"])
def test_a_record_anchor_never_collides_with_a_rule_anchor(race_name: str) -> None:
    overview = build_overview(
        get_race(race_name),  # pyright: ignore[reportArgumentType]
        stem=race_name,
        image_for=FakeLookup(None),
    )

    assert overview.rules is not None
    records = [
        entry.anchor
        for entries in (overview.units, overview.models, overview.equipment)
        for entry in entries
    ] + [spawn.anchor for spawn in overview.spawns]
    rules = [entry.anchor for entry in overview.rules.entries]

    # One document, one id space: the section prefix makes every record anchor
    # unique, and none of them can read as a rule's.
    assert len(set(records)) == len(records)
    assert set(records).isdisjoint(rules)
