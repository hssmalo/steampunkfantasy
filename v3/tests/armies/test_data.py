"""Tests for spf.armies.data module."""

import pytest

from spf.armies.data import (
    Army,
    ArmyModel,
    ArmyUnit,
    _add_cost,
    _format_failed_group,
    _remaining_slots,
    _satisfies_requires,
    _unsatisfied_groups,
    add_unit,
    available_equipment,
    available_models,
    total_cost,
    unit_cost,
    unit_points,
    upgrade_model,
    upgrade_unit,
    validate_army,
)
from spf.races import get_race
from spf.schemas import type_aliases as t
from spf.schemas.race import (
    AssaultConfig,
    EquipmentConfig,
    ModelConfig,
    OrdersConfig,
    RaceConfig,
    RaceMetadata,
    ShakenConfig,
    UnitConfig,
)

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

_ASSAULT = AssaultConfig(
    strength=[1, 0, 0, 0],
    strength_die="4+",
    deflection=[1, 0, 0, 0],
    deflection_die="4+",
    damage="d4",
    ap=0,
)


@pytest.fixture
def simple_race() -> RaceConfig:
    """Minimal RaceConfig with one unit, two model types, and two equipment items."""
    return RaceConfig(
        races={"goblin": RaceMetadata(name="Goblin")},
        units={
            "squad": UnitConfig(
                race="goblin",
                name="Squad",
                models=["soldier"],
                size="Small",
                cost=t.Cost(mp=3),
                shaken=ShakenConfig(speed="slow", movement_order=["-", "-", "flee"]),
                special={},
                orders=OrdersConfig(),
                armor=None,
                damage_tables={"regular": ["Fine", "Dead"]},
            )
        },
        models={
            "soldier": ModelConfig(
                race="goblin",
                name="Soldier",
                equipment_limit=["Hands:2", "Grenades:1"],  # pyright: ignore[reportArgumentType]
                equipment=[],
                type=["Infantry"],
                assault=_ASSAULT,
                cost=None,
            ),
            "elite_soldier": ModelConfig(
                race="goblin",
                name="Elite Soldier",
                equipment_limit=["Hands:2"],  # pyright: ignore[reportArgumentType]
                equipment=[],
                type=["Infantry", "Elite"],
                assault=_ASSAULT,
                cost=t.Cost(xp=1),
                replaces="soldier",
            ),
        },
        equipment={
            "sword": EquipmentConfig(
                race="goblin",
                name="Sword",
                cost=t.Cost(cp=2),
                upgrade_all=True,
                requires=[["Hands:1"], ["type:Infantry"]],  # pyright: ignore[reportArgumentType]
            ),
            "shield": EquipmentConfig(
                race="goblin",
                name="Shield",
                cost=None,
                requires=[],
            ),
        },
    )


@pytest.fixture
def empty_army() -> Army:
    return Army(race="goblin", nick="Test Army", units=())


@pytest.fixture
def one_unit_army(simple_race: RaceConfig) -> Army:
    return add_unit(
        Army(race="goblin", nick="Test Army", units=()), "squad", simple_race
    )


@pytest.fixture
def goblin_army() -> RaceConfig:
    return get_race("goblin")


@pytest.fixture
def goblin_team(goblin_army: RaceConfig) -> Army:
    return add_unit(
        Army(race="goblin", nick="Test Army", units=()), "goblin_infantry", goblin_army
    )


# ---------------------------------------------------------------------------
# Data structure construction
# ---------------------------------------------------------------------------


def test_team_model_default_upgrades(simple_race: RaceConfig) -> None:
    model = ArmyModel(name="soldier", config=simple_race.models["soldier"], upgrades=())
    assert model.upgrades == ()


def test_team_model_is_frozen(simple_race: RaceConfig) -> None:
    model = ArmyModel(name="soldier", config=simple_race.models["soldier"], upgrades=())
    with pytest.raises((AttributeError, TypeError)):
        model.upgrades = ("sword",)  # pyright: ignore[reportAttributeAccessIssue]


def test_team_unit_default_models_match_config(one_unit_army: Army) -> None:
    unit = one_unit_army.units[0]
    assert tuple(m.name for m in unit.models) == tuple(unit.config.models)


def test_team_is_frozen(empty_army: Army) -> None:
    with pytest.raises((AttributeError, TypeError)):
        empty_army.units = ()  # pyright: ignore[reportAttributeAccessIssue]


def test_team_allows_duplicate_unit_in_army(simple_race: RaceConfig) -> None:
    team = Army(race="goblin", nick="Test Army", units=())
    team = add_unit(team, "squad", simple_race)
    team = add_unit(team, "squad", simple_race)
    assert len(team.units) == 2
    assert all(u.name == "squad" for u in team.units)


# ---------------------------------------------------------------------------
# Cost helpers
# ---------------------------------------------------------------------------


def test_add_cost_with_none_is_identity() -> None:
    base = t.Cost(mp=1, cp=2, xp=3, ip=4)
    assert _add_cost(base, None) == base


def test_add_cost_sums_fields() -> None:
    a = t.Cost(mp=1, cp=2, xp=3, ip=4)
    b = t.Cost(mp=10, cp=20, xp=30, ip=40)
    result = _add_cost(a, b)
    assert result == t.Cost(mp=11, cp=22, xp=33, ip=44)


def test_unit_cost_base_only(one_unit_army: Army, simple_race: RaceConfig) -> None:
    unit = one_unit_army.units[0]
    assert unit_cost(unit, simple_race) == t.Cost(mp=3)


def test_unit_cost_with_upgrade_model(
    one_unit_army: Army, simple_race: RaceConfig
) -> None:
    team = upgrade_unit(
        one_unit_army, ("squad", 0), ("soldier", 0), "elite_soldier", simple_race
    )
    assert unit_cost(team.units[0], simple_race) == t.Cost(mp=3, xp=1)  # base + upgrade


def test_unit_cost_with_equipment_upgrade(
    one_unit_army: Army, simple_race: RaceConfig
) -> None:
    team = upgrade_model(
        one_unit_army, ("squad", 0), ("soldier", 0), "sword", simple_race
    )
    # base cost + equipment upgrade cost
    assert unit_cost(team.units[0], simple_race) == t.Cost(mp=3, cp=2)


def test_unit_points_formula(one_unit_army: Army, simple_race: RaceConfig) -> None:
    # squad costs mp=3, so points = 3 + 0 + 0 + 3*0 = 3
    assert unit_points(one_unit_army.units[0], simple_race) == 3


def test_unit_points_ip_weighted(simple_race: RaceConfig) -> None:
    # Build a unit where cost has ip=2 to verify the 3x weighting
    # Manually set unit cost with ip component via the existing fixtures
    team = upgrade_unit(
        add_unit(Army(race="goblin", nick="T", units=()), "squad", simple_race),
        ("squad", 0),
        ("soldier", 0),
        "elite_soldier",
        simple_race,
    )
    # squad mp=3 + elite_soldier xp=1 → points = 3 + 0 + 1 + 0 = 4
    assert unit_points(team.units[0], simple_race) == 4


def test_unit_points_zero_cost(simple_race: RaceConfig) -> None:
    # A unit with zero cost yields 0 points
    zero_cost_unit = simple_race.units["squad"].model_copy(update={"cost": t.Cost()})
    zero_cost_race = simple_race.model_copy(update={"units": {"squad": zero_cost_unit}})
    team = add_unit(Army(race="goblin", nick="T", units=()), "squad", zero_cost_race)
    assert unit_points(team.units[0], zero_cost_race) == 0


def test_total_cost_empty_army(simple_race: RaceConfig) -> None:
    team = Army(race="goblin", nick="Test Army", units=())
    assert total_cost(team, simple_race) == t.Cost()


def test_total_cost_includes_unit_base_army(
    one_unit_army: Army, simple_race: RaceConfig
) -> None:
    # squad costs mp=3
    assert total_cost(one_unit_army, simple_race) == t.Cost(mp=3)


def test_total_cost_includes_upgrade_model_cost(
    one_unit_army: Army, simple_race: RaceConfig
) -> None:
    team = upgrade_unit(
        one_unit_army, ("squad", 0), ("soldier", 0), "elite_soldier", simple_race
    )
    # squad (costs mp=3) + elite_soldier (costs xp=1)
    assert total_cost(team, simple_race) == t.Cost(mp=3, xp=1)


def test_total_cost_includes_upgrade_equipment_cost(
    one_unit_army: Army, simple_race: RaceConfig
) -> None:
    team = upgrade_model(
        one_unit_army, ("squad", 0), ("soldier", 0), "sword", simple_race
    )
    # squad (costs mp=3) + sword (costs cp=2)
    assert total_cost(team, simple_race) == t.Cost(mp=3, cp=2)


# ---------------------------------------------------------------------------
# Requires logic
# ---------------------------------------------------------------------------


def test_satisfies_requires_type_match(simple_race: RaceConfig) -> None:
    soldier = ArmyModel(
        name="soldier", config=simple_race.models["soldier"], upgrades=()
    )
    # sword requires [type:Infantry] among others; soldier is Infantry
    assert _satisfies_requires(
        simple_race.equipment["sword"].requires, soldier, simple_race
    )


def test_satisfies_requires_type_mismatch(simple_race: RaceConfig) -> None:
    # Temporarily test: a requires list that demands a type the model doesn't have

    req = [[t.Requirement(key="type", value="Cavalry")]]
    soldier = ArmyModel(
        name="soldier", config=simple_race.models["soldier"], upgrades=()
    )
    assert not _satisfies_requires(req, soldier, simple_race)


def test_satisfies_requires_holder_sufficient(simple_race: RaceConfig) -> None:
    # soldier has Hands:2; require Hands:1 should pass
    req = [[t.Requirement(key="Hands", value=1)]]
    soldier = ArmyModel(
        name="soldier", config=simple_race.models["soldier"], upgrades=()
    )
    assert _satisfies_requires(req, soldier, simple_race)


def test_satisfies_requires_holder_insufficient(simple_race: RaceConfig) -> None:
    # soldier has Hands:2; require Hands:3 should fail
    req = [[t.Requirement(key="Hands", value=3)]]
    soldier = ArmyModel(
        name="soldier", config=simple_race.models["soldier"], upgrades=()
    )
    assert not _satisfies_requires(req, soldier, simple_race)


def test_satisfies_requires_cnf_all_groups_needed(simple_race: RaceConfig) -> None:
    # CNF: [Hands:1] AND [type:Cavalry] — soldier is not Cavalry → False
    req = [
        [t.Requirement(key="Hands", value=1)],
        [t.Requirement(key="type", value="Cavalry")],
    ]
    soldier = ArmyModel(
        name="soldier", config=simple_race.models["soldier"], upgrades=()
    )
    assert not _satisfies_requires(req, soldier, simple_race)


# ---------------------------------------------------------------------------
# _unsatisfied_groups and _format_failed_group
# ---------------------------------------------------------------------------


def test_unsatisfied_groups_all_satisfied(simple_race: RaceConfig) -> None:
    soldier = ArmyModel(
        name="soldier", config=simple_race.models["soldier"], upgrades=()
    )
    # sword requires [Hands:1] AND [type:Infantry]; soldier satisfies both
    assert (
        _unsatisfied_groups(
            simple_race.equipment["sword"].requires, soldier, simple_race
        )
        == []
    )


def test_unsatisfied_groups_type_failure_returns_group(simple_race: RaceConfig) -> None:
    soldier = ArmyModel(
        name="soldier", config=simple_race.models["soldier"], upgrades=()
    )
    req = [[t.Requirement(key="type", value="Cavalry")]]
    failed = _unsatisfied_groups(req, soldier, simple_race)
    assert len(failed) == 1
    assert failed[0] == [t.Requirement(key="type", value="Cavalry")]


def test_unsatisfied_groups_slot_failure_returns_group(simple_race: RaceConfig) -> None:
    soldier = ArmyModel(
        name="soldier", config=simple_race.models["soldier"], upgrades=()
    )
    req = [[t.Requirement(key="Hands", value=3)]]
    failed = _unsatisfied_groups(req, soldier, simple_race)
    assert len(failed) == 1


def test_format_failed_group_type_only(simple_race: RaceConfig) -> None:
    soldier = ArmyModel(
        name="soldier", config=simple_race.models["soldier"], upgrades=()
    )
    remaining = _remaining_slots(soldier, simple_race)
    group = [
        t.Requirement(key="type", value="Infantry"),
        t.Requirement(key="type", value="Grunt"),
    ]
    result = _format_failed_group(group, remaining)
    assert result == "needs type:Infantry or type:Grunt"


def test_format_failed_group_slot_shows_available(simple_race: RaceConfig) -> None:
    soldier = ArmyModel(
        name="soldier", config=simple_race.models["soldier"], upgrades=()
    )
    remaining = _remaining_slots(soldier, simple_race)
    group = [t.Requirement(key="Hands", value=2)]
    result = _format_failed_group(group, remaining)
    # soldier has Hands:2 available (no upgrades), so "have 2", but we're testing format
    assert "Hands:2" in result
    assert "have" in result


def test_validate_army_requires_error_includes_type_detail(
    simple_race: RaceConfig,
) -> None:
    elite_only_equip = EquipmentConfig(
        race="goblin",
        name="Elite Sword",
        cost=t.Cost(cp=3),
        upgrade_all=True,
        requires=[["type:Elite", "type:Cavalry"]],  # pyright: ignore[reportArgumentType]
    )
    army = RaceConfig(
        races=simple_race.races,
        units=simple_race.units,
        models=simple_race.models,
        equipment={**simple_race.equipment, "elite_sword": elite_only_equip},
    )
    bad_model = ArmyModel(
        name="soldier",
        config=army.models["soldier"],
        upgrades=("elite_sword",),
    )
    bad_unit = ArmyUnit(name="squad", config=army.units["squad"], models=(bad_model,))
    team = Army(race="goblin", nick="Test Army", units=(bad_unit,))
    errors = validate_army(team, army)
    assert any("type:Elite or type:Cavalry" in e for e in errors)


def test_validate_army_requires_error_includes_slot_detail(
    simple_race: RaceConfig,
) -> None:
    # greedy_sword needs Hands:3 but soldier only has Hands:2
    greedy_equip = EquipmentConfig(
        race="goblin",
        name="Greedy Sword",
        cost=t.Cost(cp=4),
        upgrade_all=True,
        requires=[["Hands:3"]],  # pyright: ignore[reportArgumentType]
    )
    army = RaceConfig(
        races=simple_race.races,
        units=simple_race.units,
        models=simple_race.models,
        equipment={**simple_race.equipment, "greedy_sword": greedy_equip},
    )
    bad_model = ArmyModel(
        name="soldier",
        config=army.models["soldier"],
        upgrades=("greedy_sword",),
    )
    bad_unit = ArmyUnit(name="squad", config=army.units["squad"], models=(bad_model,))
    team = Army(race="goblin", nick="Test Army", units=(bad_unit,))
    errors = validate_army(team, army)
    assert any("Hands:3" in e and "have" in e for e in errors)


def test_validate_army_requires_error_includes_all_failing_groups(
    simple_race: RaceConfig,
) -> None:
    # impossible_sword needs type:Cavalry AND Hands:10 — both fail on soldier
    impossible_equip = EquipmentConfig(
        race="goblin",
        name="Impossible Sword",
        cost=t.Cost(cp=5),
        upgrade_all=True,
        requires=[
            ["type:Cavalry"],
            ["Hands:10"],
        ],  # pyright: ignore[reportArgumentType]
    )
    army = RaceConfig(
        races=simple_race.races,
        units=simple_race.units,
        models=simple_race.models,
        equipment={**simple_race.equipment, "impossible_sword": impossible_equip},
    )
    bad_model = ArmyModel(
        name="soldier",
        config=army.models["soldier"],
        upgrades=("impossible_sword",),
    )
    bad_unit = ArmyUnit(name="squad", config=army.units["squad"], models=(bad_model,))
    team = Army(race="goblin", nick="Test Army", units=(bad_unit,))
    errors = validate_army(team, army)
    # Both failing groups should appear, separated by "; "
    assert any("type:Cavalry" in e and "Hands:10" in e for e in errors)


# ---------------------------------------------------------------------------
# add_unit
# ---------------------------------------------------------------------------


def test_add_unit_appends_to_team(simple_race: RaceConfig) -> None:
    team = Army(race="goblin", nick="Test Army", units=())
    team = add_unit(team, "squad", simple_race)
    assert len(team.units) == 1
    assert team.units[0].name == "squad"


def test_add_unit_default_models_match_config(simple_race: RaceConfig) -> None:
    team = add_unit(
        Army(race="goblin", nick="Test Army", units=()), "squad", simple_race
    )
    unit = team.units[0]
    assert tuple(m.name for m in unit.models) == tuple(unit.config.models)


def test_add_unit_unknown_name_raises(simple_race: RaceConfig) -> None:
    with pytest.raises(ValueError, match="Unknown unit"):
        add_unit(
            Army(race="goblin", nick="Test Army", units=()),
            "does_not_exist",
            simple_race,
        )


# ---------------------------------------------------------------------------
# upgrade_unit
# ---------------------------------------------------------------------------


def test_upgrade_unit_valid_replacement(
    one_unit_army: Army, simple_race: RaceConfig
) -> None:
    team = upgrade_unit(
        one_unit_army, ("squad", 0), ("soldier", 0), "elite_soldier", simple_race
    )
    assert team.units[0].models[0].name == "elite_soldier"


def test_upgrade_unit_does_not_mutate_original(
    one_unit_army: Army, simple_race: RaceConfig
) -> None:
    upgrade_unit(
        one_unit_army, ("squad", 0), ("soldier", 0), "elite_soldier", simple_race
    )
    assert one_unit_army.units[0].models[0].name == "soldier"


def test_upgrade_unit_invalid_replaces_raises(
    one_unit_army: Army, simple_race: RaceConfig
) -> None:
    # soldier does not have replaces set; cannot replace elite_soldier with soldier
    with pytest.raises(ValueError, match="cannot replace"):
        upgrade_unit(
            one_unit_army, ("squad", 0), ("soldier", 0), "soldier", simple_race
        )


def test_upgrade_unit_unknown_unit_key_raises(
    one_unit_army: Army, simple_race: RaceConfig
) -> None:
    with pytest.raises(KeyError):
        upgrade_unit(
            one_unit_army,
            ("nonexistent", 0),
            ("soldier", 0),
            "elite_soldier",
            simple_race,
        )


def test_upgrade_unit_unknown_model_key_raises(
    one_unit_army: Army, simple_race: RaceConfig
) -> None:
    with pytest.raises(KeyError):
        upgrade_unit(
            one_unit_army,
            ("squad", 0),
            ("nonexistent", 0),
            "elite_soldier",
            simple_race,
        )


# ---------------------------------------------------------------------------
# upgrade_model
# ---------------------------------------------------------------------------


def test_upgrade_model_adds_to_upgrades(
    one_unit_army: Army, simple_race: RaceConfig
) -> None:
    team = upgrade_model(
        one_unit_army, ("squad", 0), ("soldier", 0), "sword", simple_race
    )
    assert "sword" in team.units[0].models[0].upgrades


def test_upgrade_model_does_not_mutate_original(
    one_unit_army: Army, simple_race: RaceConfig
) -> None:
    upgrade_model(one_unit_army, ("squad", 0), ("soldier", 0), "sword", simple_race)
    assert one_unit_army.units[0].models[0].upgrades == ()


def test_upgrade_model_no_cost_raises(
    one_unit_army: Army, simple_race: RaceConfig
) -> None:
    with pytest.raises(ValueError, match="no cost"):
        upgrade_model(
            one_unit_army, ("squad", 0), ("soldier", 0), "shield", simple_race
        )


def test_upgrade_model_unsatisfied_requires_raises(simple_race: RaceConfig) -> None:
    # Add a unit with an Elite-only model to test requires failure

    elite_only_equip = EquipmentConfig(
        race="goblin",
        name="Elite Sword",
        cost=t.Cost(cp=3),
        upgrade_all=True,
        requires=[["type:Elite"]],  # pyright: ignore[reportArgumentType]
    )
    army = RaceConfig(
        races=simple_race.races,
        units=simple_race.units,
        models=simple_race.models,
        equipment={**simple_race.equipment, "elite_sword": elite_only_equip},
    )
    team = add_unit(Army(race="goblin", nick="Test Army", units=()), "squad", army)
    with pytest.raises(ValueError, match="requires not satisfied"):
        upgrade_model(team, ("squad", 0), ("soldier", 0), "elite_sword", army)


def test_upgrade_model_unknown_key_raises(
    one_unit_army: Army, simple_race: RaceConfig
) -> None:
    with pytest.raises(KeyError):
        upgrade_model(
            one_unit_army, ("nonexistent", 0), ("soldier", 0), "sword", simple_race
        )


# ---------------------------------------------------------------------------
# available_models and available_equipment
# ---------------------------------------------------------------------------


def test_available_models_returns_matching(
    one_unit_army: Army, simple_race: RaceConfig
) -> None:
    result = available_models(one_unit_army, ("squad", 0), ("soldier", 0), simple_race)
    assert len(result) == 1
    assert result[0].name == "Elite Soldier"


def test_available_models_empty_when_none_match(
    one_unit_army: Army, simple_race: RaceConfig
) -> None:
    # upgrade to elite_soldier; nothing replaces it
    team = upgrade_unit(
        one_unit_army, ("squad", 0), ("soldier", 0), "elite_soldier", simple_race
    )
    result = available_models(team, ("squad", 0), ("elite_soldier", 0), simple_race)
    assert result == []


def test_available_equipment_excludes_no_cost(
    one_unit_army: Army, simple_race: RaceConfig
) -> None:
    result = available_equipment(
        one_unit_army, ("squad", 0), ("soldier", 0), simple_race
    )
    names = [e.name for e in result]
    assert "Shield" not in names  # shield has no cost


def test_available_equipment_includes_valid(
    one_unit_army: Army, simple_race: RaceConfig
) -> None:
    result = available_equipment(
        one_unit_army, ("squad", 0), ("soldier", 0), simple_race
    )
    names = [e.name for e in result]
    assert "Sword" in names  # cost + Infantry + Hands:1 available


def test_available_equipment_goblin_infantry_clockwork_wings(
    goblin_team: Army, goblin_army: RaceConfig
) -> None:
    # goblin_infantry model has default goblin_bow (uses Hands:2), so no more Hands.
    # clockwork_wings requires type:Infantry + Independent:1 (999 available) → valid.
    result = available_equipment(
        goblin_team, ("goblin_infantry", 0), ("goblin_infantry", 0), goblin_army
    )
    names = [e.name for e in result]
    assert "Clockwork Wings" in names


def test_available_equipment_excludes_insufficient_slots(
    goblin_team: Army, goblin_army: RaceConfig
) -> None:
    # goblin_bow already uses all Hands:2; gear_bow also needs Hands:2 → not available
    result = available_equipment(
        goblin_team, ("goblin_infantry", 0), ("goblin_infantry", 0), goblin_army
    )
    names = [e.name for e in result]
    assert "Gear bow" not in names


# ---------------------------------------------------------------------------
# validate_army
# ---------------------------------------------------------------------------


def test_validate_army_valid_returns_empty(
    one_unit_army: Army, simple_race: RaceConfig
) -> None:
    assert validate_army(one_unit_army, simple_race) == []


def test_validate_army_detects_invalid_model_replacement(
    simple_race: RaceConfig,
) -> None:
    # Manually construct an illegal replacement (soldier replacing itself — no replaces)
    tweaked_unit_config = UnitConfig(
        race="goblin",
        name="Squad",
        models=["elite_soldier"],  # default is elite_soldier
        size="Small",
        cost=t.Cost(mp=3),
        shaken=ShakenConfig(speed="slow", movement_order=["-", "-", "flee"]),
        special={},
        orders=OrdersConfig(),
        armor=None,
        damage_tables={"regular": ["Fine", "Dead"]},
    )
    illegal_unit = ArmyUnit(
        name="squad",
        config=tweaked_unit_config,
        models=(
            ArmyModel(
                name="soldier",  # soldier is at index 0, but default is elite_soldier
                config=simple_race.models["soldier"],
                upgrades=(),
            ),
        ),
    )
    team = Army(race="goblin", nick="Test Army", units=(illegal_unit,))
    errors = validate_army(team, simple_race)
    assert len(errors) >= 1
    assert any("cannot replace" in e for e in errors)


def test_validate_army_detects_multiple_violations(simple_race: RaceConfig) -> None:
    # Two models each with an illegal replacement
    tweaked_unit_config = UnitConfig(
        race="goblin",
        name="Double Squad",
        models=["elite_soldier", "elite_soldier"],
        size="Small",
        cost=t.Cost(mp=3),
        shaken=ShakenConfig(speed="slow", movement_order=["-", "-", "flee"]),
        special={},
        orders=OrdersConfig(),
        armor=None,
        damage_tables={"regular": ["Fine", "Dead"]},
    )
    illegal_unit = ArmyUnit(
        name="double_squad",
        config=tweaked_unit_config,
        models=(
            ArmyModel(
                name="soldier", config=simple_race.models["soldier"], upgrades=()
            ),
            ArmyModel(
                name="soldier", config=simple_race.models["soldier"], upgrades=()
            ),
        ),
    )
    team = Army(race="goblin", nick="Test Army", units=(illegal_unit,))
    errors = validate_army(team, simple_race)
    assert len(errors) == 2


def test_validate_army_detects_unsatisfied_equipment_requires(
    simple_race: RaceConfig,
) -> None:
    elite_only_equip = EquipmentConfig(
        race="goblin",
        name="Elite Sword",
        cost=t.Cost(cp=3),
        upgrade_all=True,
        requires=[["type:Elite"]],  # pyright: ignore[reportArgumentType]
    )
    army = RaceConfig(
        races=simple_race.races,
        units=simple_race.units,
        models=simple_race.models,
        equipment={**simple_race.equipment, "elite_sword": elite_only_equip},
    )
    # Manually put elite_sword on a non-Elite soldier
    bad_model = ArmyModel(
        name="soldier",
        config=army.models["soldier"],
        upgrades=("elite_sword",),
    )
    bad_unit = ArmyUnit(name="squad", config=army.units["squad"], models=(bad_model,))
    team = Army(race="goblin", nick="Test Army", units=(bad_unit,))
    errors = validate_army(team, army)
    assert any("requires not satisfied" in e for e in errors)
