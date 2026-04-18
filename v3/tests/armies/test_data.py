"""Tests for army data structures and functions."""

import pytest

from spf.armies import (
    ArmyList,
    available_equipment,
    available_models,
    validate_army,
)
from spf.armies.build import (
    ArmyModel,
    ArmyUnit,
    _format_failed_group,
    _remaining_slots,
    _satisfies_requires,
    _unsatisfied_groups,
)
from spf.races import get_race
from spf.schemas import type_aliases as t
from spf.schemas.race import (
    AssaultConfig,
    EquipmentAssaultConfig,
    EquipmentConfig,
    ModelConfig,
    OrdersConfig,
    RaceConfig,
    RaceMetadata,
    ShakenConfig,
    Stacker,
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
def empty_army() -> ArmyList:
    return ArmyList(race="goblin", nick="Test Army", units=())


@pytest.fixture
def one_unit_army(simple_race: RaceConfig) -> ArmyList:
    return ArmyList(race="goblin", nick="Test Army", units=()).add_unit(
        "squad", simple_race
    )


@pytest.fixture
def goblin_race() -> RaceConfig:
    return get_race("goblin")


@pytest.fixture
def goblin_army(goblin_race: RaceConfig) -> ArmyList:
    return ArmyList(race="goblin", nick="Test Army", units=()).add_unit(
        "goblin_infantry", goblin_race
    )


@pytest.fixture
def race_with_defaults(simple_race: RaceConfig) -> RaceConfig:
    """Variant of simple_race where soldier has a default Hands:2 weapon."""
    default_sword = EquipmentConfig(
        race="goblin",
        name="Default Sword",
        cost=None,
        requires=[["Hands:2"]],  # pyright: ignore[reportArgumentType]
    )
    soldier_with_default = simple_race.models["soldier"].model_copy(
        update={"equipment": ["default_sword"]}
    )
    return RaceConfig(
        races=simple_race.races,
        units=simple_race.units,
        models={**simple_race.models, "soldier": soldier_with_default},
        equipment={**simple_race.equipment, "default_sword": default_sword},
    )


# ---------------------------------------------------------------------------
# Data structure construction
# ---------------------------------------------------------------------------


def test_army_model_default_upgrades(simple_race: RaceConfig) -> None:
    model = ArmyModel(name="soldier", config=simple_race.models["soldier"], upgrades=())
    assert model.upgrades == ()


def test_army_model_is_frozen(simple_race: RaceConfig) -> None:
    model = ArmyModel(name="soldier", config=simple_race.models["soldier"], upgrades=())
    with pytest.raises((AttributeError, TypeError)):
        model.upgrades = ("sword",)  # pyright: ignore[reportAttributeAccessIssue]


def test_army_unit_default_models_match_config(one_unit_army: ArmyList) -> None:
    unit = one_unit_army.units[0]
    assert tuple(m.name for m in unit.models) == tuple(unit.config.models)


def test_army_list_is_frozen(empty_army: ArmyList) -> None:
    with pytest.raises((AttributeError, TypeError)):
        empty_army.units = ()  # pyright: ignore[reportAttributeAccessIssue]


def test_army_list_allows_duplicate_units(simple_race: RaceConfig) -> None:
    army = ArmyList(race="goblin", nick="Test Army", units=())
    army = army.add_unit("squad", simple_race)
    army = army.add_unit("squad", simple_race)
    assert len(army.units) == 2
    assert all(u.name == "squad" for u in army.units)


# ---------------------------------------------------------------------------
# Cost arithmetic
# ---------------------------------------------------------------------------


def test_cost_add_sums_fields() -> None:
    a = t.Cost(mp=1, cp=2, xp=3, ip=4)
    b = t.Cost(mp=10, cp=20, xp=30, ip=40)
    assert a + b == t.Cost(mp=11, cp=22, xp=33, ip=44)


def test_cost_add_identity() -> None:
    base = t.Cost(mp=1, cp=2, xp=3, ip=4)
    assert base + t.Cost() == base
    assert t.Cost() + base == base


def test_cost_sum_over_list() -> None:
    costs = [t.Cost(mp=1), t.Cost(mp=2), t.Cost(cp=5)]
    assert sum(costs, t.Cost()) == t.Cost(mp=3, cp=5)


def test_cost_mul_scales_all_fields() -> None:
    assert t.Cost(mp=3, cp=1, xp=0, ip=2) * 4 == t.Cost(mp=12, cp=4, xp=0, ip=8)


def test_cost_rmul_is_equivalent() -> None:
    cost = t.Cost(mp=3, cp=1, xp=0, ip=2)
    assert 4 * cost == cost * 4


def test_cost_mul_by_zero() -> None:
    assert t.Cost(mp=5, cp=3, xp=1, ip=2) * 0 == t.Cost()


def test_cost_to_points_formula() -> None:
    assert t.Cost(mp=2, cp=3, xp=1, ip=2).to_points() == 12  # 2+3+1+6


def test_cost_to_points_zero() -> None:
    assert t.Cost().to_points() == 0


def test_unit_cost_base_only(one_unit_army: ArmyList, simple_race: RaceConfig) -> None:
    resolved = one_unit_army.resolve(simple_race)
    assert resolved.units[0].cost() == t.Cost(mp=3)


def test_unit_cost_with_upgrade_model(
    one_unit_army: ArmyList, simple_race: RaceConfig
) -> None:
    army = one_unit_army.upgrade_unit(
        ("squad", 0), ("soldier", 0), "elite_soldier", simple_race
    )
    resolved = army.resolve(simple_race)
    assert resolved.units[0].cost() == t.Cost(mp=3, xp=1)  # base + upgrade


def test_unit_cost_with_equipment_upgrade(
    one_unit_army: ArmyList, simple_race: RaceConfig
) -> None:
    army = one_unit_army.upgrade_model(
        ("squad", 0), ("soldier", 0), "sword", simple_race
    )
    resolved = army.resolve(simple_race)
    assert resolved.units[0].cost() == t.Cost(mp=3, cp=2)


def test_unit_points_formula(one_unit_army: ArmyList, simple_race: RaceConfig) -> None:
    # squad costs mp=3, so points = 3
    resolved = one_unit_army.resolve(simple_race)
    assert resolved.units[0].cost().to_points() == 3


def test_unit_points_ip_weighted(simple_race: RaceConfig) -> None:
    # elite_soldier adds xp=1 → points = 3 + 1 = 4
    army = (
        ArmyList(race="goblin", nick="T", units=())
        .add_unit("squad", simple_race)
        .upgrade_unit(("squad", 0), ("soldier", 0), "elite_soldier", simple_race)
    )
    resolved = army.resolve(simple_race)
    assert resolved.units[0].cost().to_points() == 4


def test_unit_points_zero_cost(simple_race: RaceConfig) -> None:
    zero_cost_unit = simple_race.units["squad"].model_copy(update={"cost": t.Cost()})
    zero_cost_race = simple_race.model_copy(update={"units": {"squad": zero_cost_unit}})
    army = ArmyList(race="goblin", nick="T", units=()).add_unit("squad", zero_cost_race)
    resolved = army.resolve(zero_cost_race)
    assert resolved.units[0].cost().to_points() == 0


def test_army_cost_empty(simple_race: RaceConfig) -> None:
    resolved = ArmyList(race="goblin", nick="Test Army", units=()).resolve(simple_race)
    assert resolved.cost() == t.Cost()


def test_army_cost_includes_unit_base(
    one_unit_army: ArmyList, simple_race: RaceConfig
) -> None:
    resolved = one_unit_army.resolve(simple_race)
    assert resolved.cost() == t.Cost(mp=3)


def test_army_cost_includes_upgrade_model(
    one_unit_army: ArmyList, simple_race: RaceConfig
) -> None:
    army = one_unit_army.upgrade_unit(
        ("squad", 0), ("soldier", 0), "elite_soldier", simple_race
    )
    resolved = army.resolve(simple_race)
    assert resolved.cost() == t.Cost(mp=3, xp=1)


def test_army_cost_includes_upgrade_equipment(
    one_unit_army: ArmyList, simple_race: RaceConfig
) -> None:
    army = one_unit_army.upgrade_model(
        ("squad", 0), ("soldier", 0), "sword", simple_race
    )
    resolved = army.resolve(simple_race)
    assert resolved.cost() == t.Cost(mp=3, cp=2)


# ---------------------------------------------------------------------------
# Requires logic
# ---------------------------------------------------------------------------


def test_satisfies_requires_type_match(simple_race: RaceConfig) -> None:
    soldier = ArmyModel(
        name="soldier", config=simple_race.models["soldier"], upgrades=()
    )
    assert _satisfies_requires(
        simple_race.equipment["sword"].requires, soldier, simple_race
    )


def test_satisfies_requires_type_mismatch(simple_race: RaceConfig) -> None:
    req = [[t.Requirement(key="type", value="Cavalry")]]
    soldier = ArmyModel(
        name="soldier", config=simple_race.models["soldier"], upgrades=()
    )
    assert not _satisfies_requires(req, soldier, simple_race)


def test_satisfies_requires_holder_sufficient(simple_race: RaceConfig) -> None:
    req = [[t.Requirement(key="Hands", value=1)]]
    soldier = ArmyModel(
        name="soldier", config=simple_race.models["soldier"], upgrades=()
    )
    assert _satisfies_requires(req, soldier, simple_race)


def test_satisfies_requires_holder_insufficient(simple_race: RaceConfig) -> None:
    req = [[t.Requirement(key="Hands", value=3)]]
    soldier = ArmyModel(
        name="soldier", config=simple_race.models["soldier"], upgrades=()
    )
    assert not _satisfies_requires(req, soldier, simple_race)


def test_satisfies_requires_cnf_all_groups_needed(simple_race: RaceConfig) -> None:
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
    assert "Hands:2" in result
    assert "have" in result


# ---------------------------------------------------------------------------
# _remaining_slots — default equipment does not consume slots
# ---------------------------------------------------------------------------


def test_remaining_slots_does_not_count_default_equipment(
    race_with_defaults: RaceConfig,
) -> None:
    # Defaults are always discarded when upgrades are added, so they must never
    # consume slots. A soldier with a Hands:2 default but no upgrades should
    # still show Hands:2 free.
    soldier = ArmyModel(
        name="soldier", config=race_with_defaults.models["soldier"], upgrades=()
    )
    remaining = _remaining_slots(soldier, race_with_defaults)
    assert remaining.get("Hands", 0) == 2


def test_remaining_slots_counts_only_upgrades_when_upgrades_present(
    race_with_defaults: RaceConfig,
) -> None:
    # With a Hands:2 default and a Hands:1 upgrade, only the upgrade is counted.
    soldier = ArmyModel(
        name="soldier",
        config=race_with_defaults.models["soldier"],
        upgrades=("sword",),
    )
    remaining = _remaining_slots(soldier, race_with_defaults)
    # sword requires Hands:1 → 2 - 1 = 1 remaining (default_sword NOT counted)
    assert remaining.get("Hands", 0) == 1


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
    race = RaceConfig(
        races=simple_race.races,
        units=simple_race.units,
        models=simple_race.models,
        equipment={**simple_race.equipment, "elite_sword": elite_only_equip},
    )
    bad_model = ArmyModel(
        name="soldier",
        config=race.models["soldier"],
        upgrades=("elite_sword",),
    )
    bad_unit = ArmyUnit(name="squad", config=race.units["squad"], models=(bad_model,))
    army = ArmyList(race="goblin", nick="Test Army", units=(bad_unit,))
    errors = validate_army(army, race)
    assert any("type:Elite or type:Cavalry" in e for e in errors)


def test_validate_army_requires_error_includes_slot_detail(
    simple_race: RaceConfig,
) -> None:
    greedy_equip = EquipmentConfig(
        race="goblin",
        name="Greedy Sword",
        cost=t.Cost(cp=4),
        upgrade_all=True,
        requires=[["Hands:3"]],  # pyright: ignore[reportArgumentType]
    )
    race = RaceConfig(
        races=simple_race.races,
        units=simple_race.units,
        models=simple_race.models,
        equipment={**simple_race.equipment, "greedy_sword": greedy_equip},
    )
    bad_model = ArmyModel(
        name="soldier",
        config=race.models["soldier"],
        upgrades=("greedy_sword",),
    )
    bad_unit = ArmyUnit(name="squad", config=race.units["squad"], models=(bad_model,))
    army = ArmyList(race="goblin", nick="Test Army", units=(bad_unit,))
    errors = validate_army(army, race)
    assert any("Hands:3" in e and "have" in e for e in errors)


def test_validate_army_requires_error_includes_all_failing_groups(
    simple_race: RaceConfig,
) -> None:
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
    race = RaceConfig(
        races=simple_race.races,
        units=simple_race.units,
        models=simple_race.models,
        equipment={**simple_race.equipment, "impossible_sword": impossible_equip},
    )
    bad_model = ArmyModel(
        name="soldier",
        config=race.models["soldier"],
        upgrades=("impossible_sword",),
    )
    bad_unit = ArmyUnit(name="squad", config=race.units["squad"], models=(bad_model,))
    army = ArmyList(race="goblin", nick="Test Army", units=(bad_unit,))
    errors = validate_army(army, race)
    assert any("type:Cavalry" in e and "Hands:10" in e for e in errors)


# ---------------------------------------------------------------------------
# add_unit
# ---------------------------------------------------------------------------


def test_add_unit_appends_to_army(simple_race: RaceConfig) -> None:
    army = ArmyList(race="goblin", nick="Test Army", units=()).add_unit(
        "squad", simple_race
    )
    assert len(army.units) == 1
    assert army.units[0].name == "squad"


def test_add_unit_default_models_match_config(simple_race: RaceConfig) -> None:
    army = ArmyList(race="goblin", nick="Test Army", units=()).add_unit(
        "squad", simple_race
    )
    unit = army.units[0]
    assert tuple(m.name for m in unit.models) == tuple(unit.config.models)


def test_add_unit_unknown_name_raises(simple_race: RaceConfig) -> None:
    with pytest.raises(ValueError, match="Unknown unit"):
        ArmyList(race="goblin", nick="Test Army", units=()).add_unit(
            "does_not_exist", simple_race
        )


# ---------------------------------------------------------------------------
# upgrade_unit
# ---------------------------------------------------------------------------


def test_upgrade_unit_valid_replacement(
    one_unit_army: ArmyList, simple_race: RaceConfig
) -> None:
    army = one_unit_army.upgrade_unit(
        ("squad", 0), ("soldier", 0), "elite_soldier", simple_race
    )
    assert army.units[0].models[0].name == "elite_soldier"


def test_upgrade_unit_does_not_mutate_original(
    one_unit_army: ArmyList, simple_race: RaceConfig
) -> None:
    one_unit_army.upgrade_unit(
        ("squad", 0), ("soldier", 0), "elite_soldier", simple_race
    )
    assert one_unit_army.units[0].models[0].name == "soldier"


def test_upgrade_unit_invalid_replaces_raises(
    one_unit_army: ArmyList, simple_race: RaceConfig
) -> None:
    with pytest.raises(ValueError, match="cannot replace"):
        one_unit_army.upgrade_unit(("squad", 0), ("soldier", 0), "soldier", simple_race)


def test_upgrade_unit_unknown_unit_key_raises(
    one_unit_army: ArmyList, simple_race: RaceConfig
) -> None:
    with pytest.raises(KeyError):
        one_unit_army.upgrade_unit(
            ("nonexistent", 0), ("soldier", 0), "elite_soldier", simple_race
        )


def test_upgrade_unit_unknown_model_key_raises(
    one_unit_army: ArmyList, simple_race: RaceConfig
) -> None:
    with pytest.raises(KeyError):
        one_unit_army.upgrade_unit(
            ("squad", 0), ("nonexistent", 0), "elite_soldier", simple_race
        )


# ---------------------------------------------------------------------------
# upgrade_model
# ---------------------------------------------------------------------------


def test_upgrade_model_adds_to_upgrades(
    one_unit_army: ArmyList, simple_race: RaceConfig
) -> None:
    army = one_unit_army.upgrade_model(
        ("squad", 0), ("soldier", 0), "sword", simple_race
    )
    assert "sword" in army.units[0].models[0].upgrades


def test_upgrade_model_does_not_mutate_original(
    one_unit_army: ArmyList, simple_race: RaceConfig
) -> None:
    one_unit_army.upgrade_model(("squad", 0), ("soldier", 0), "sword", simple_race)
    assert one_unit_army.units[0].models[0].upgrades == ()


def test_upgrade_model_no_cost_raises(
    one_unit_army: ArmyList, simple_race: RaceConfig
) -> None:
    with pytest.raises(ValueError, match="no cost"):
        one_unit_army.upgrade_model(("squad", 0), ("soldier", 0), "shield", simple_race)


def test_upgrade_model_unsatisfied_requires_raises(simple_race: RaceConfig) -> None:
    elite_only_equip = EquipmentConfig(
        race="goblin",
        name="Elite Sword",
        cost=t.Cost(cp=3),
        upgrade_all=True,
        requires=[["type:Elite"]],  # pyright: ignore[reportArgumentType]
    )
    race = RaceConfig(
        races=simple_race.races,
        units=simple_race.units,
        models=simple_race.models,
        equipment={**simple_race.equipment, "elite_sword": elite_only_equip},
    )
    army = ArmyList(race="goblin", nick="Test Army", units=()).add_unit("squad", race)
    with pytest.raises(ValueError, match="requires not satisfied"):
        army.upgrade_model(("squad", 0), ("soldier", 0), "elite_sword", race)


def test_upgrade_model_unknown_key_raises(
    one_unit_army: ArmyList, simple_race: RaceConfig
) -> None:
    with pytest.raises(KeyError):
        one_unit_army.upgrade_model(
            ("nonexistent", 0), ("soldier", 0), "sword", simple_race
        )


# ---------------------------------------------------------------------------
# available_models and available_equipment
# ---------------------------------------------------------------------------


def test_available_models_returns_matching(
    one_unit_army: ArmyList, simple_race: RaceConfig
) -> None:
    result = available_models(one_unit_army, ("squad", 0), ("soldier", 0), simple_race)
    assert len(result) == 1
    assert result[0].name == "Elite Soldier"


def test_available_models_empty_when_none_match(
    one_unit_army: ArmyList, simple_race: RaceConfig
) -> None:
    army = one_unit_army.upgrade_unit(
        ("squad", 0), ("soldier", 0), "elite_soldier", simple_race
    )
    result = available_models(army, ("squad", 0), ("elite_soldier", 0), simple_race)
    assert result == []


def test_available_equipment_excludes_no_cost(
    one_unit_army: ArmyList, simple_race: RaceConfig
) -> None:
    result = available_equipment(
        one_unit_army, ("squad", 0), ("soldier", 0), simple_race
    )
    names = [e.name for e in result]
    assert "Shield" not in names


def test_available_equipment_includes_valid(
    one_unit_army: ArmyList, simple_race: RaceConfig
) -> None:
    result = available_equipment(
        one_unit_army, ("squad", 0), ("soldier", 0), simple_race
    )
    names = [e.name for e in result]
    assert "Sword" in names


def test_available_equipment_goblin_infantry_clockwork_wings(
    goblin_army: ArmyList, goblin_race: RaceConfig
) -> None:
    result = available_equipment(
        goblin_army, ("goblin_infantry", 0), ("goblin_infantry", 0), goblin_race
    )
    names = [e.name for e in result]
    assert "Clockwork Wings" in names


def test_available_equipment_excludes_truly_insufficient_slots(
    goblin_army: ArmyList, goblin_race: RaceConfig
) -> None:
    # After consuming all Hands slots with one upgrade, a second Hands:2 upgrade
    # should no longer be available.
    army_with_upgrade = goblin_army.upgrade_model(
        ("goblin_infantry", 0), ("goblin_infantry", 0), "gear_bow", goblin_race
    )
    result = available_equipment(
        army_with_upgrade, ("goblin_infantry", 0), ("goblin_infantry", 0), goblin_race
    )
    names = [e.name for e in result]
    assert "Gear bow" not in names


def test_available_equipment_defaults_do_not_consume_slots(
    race_with_defaults: RaceConfig,
) -> None:
    # Defaults are replaced by upgrades, so a model with a Hands:2 default weapon
    # should still be able to receive a Hands:2 upgrade — the default is gone once
    # any upgrade is added.
    army = ArmyList(race="goblin", nick="T", units=()).add_unit(
        "squad", race_with_defaults
    )
    # sword requires Hands:1 — the default_sword (Hands:2) must NOT consume slots here
    result = available_equipment(army, ("squad", 0), ("soldier", 0), race_with_defaults)
    names = [e.name for e in result]
    assert "Sword" in names


# ---------------------------------------------------------------------------
# validate_army
# ---------------------------------------------------------------------------


def test_validate_army_valid_returns_empty(
    one_unit_army: ArmyList, simple_race: RaceConfig
) -> None:
    assert validate_army(one_unit_army, simple_race) == []


def test_validate_army_detects_invalid_model_replacement(
    simple_race: RaceConfig,
) -> None:
    tweaked_unit_config = UnitConfig(
        race="goblin",
        name="Squad",
        models=["elite_soldier"],
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
                name="soldier",
                config=simple_race.models["soldier"],
                upgrades=(),
            ),
        ),
    )
    army = ArmyList(race="goblin", nick="Test Army", units=(illegal_unit,))
    errors = validate_army(army, simple_race)
    assert len(errors) >= 1
    assert any("cannot replace" in e for e in errors)


def test_validate_army_detects_multiple_violations(simple_race: RaceConfig) -> None:
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
    army = ArmyList(race="goblin", nick="Test Army", units=(illegal_unit,))
    errors = validate_army(army, simple_race)
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
    race = RaceConfig(
        races=simple_race.races,
        units=simple_race.units,
        models=simple_race.models,
        equipment={**simple_race.equipment, "elite_sword": elite_only_equip},
    )
    bad_model = ArmyModel(
        name="soldier",
        config=race.models["soldier"],
        upgrades=("elite_sword",),
    )
    bad_unit = ArmyUnit(name="squad", config=race.units["squad"], models=(bad_model,))
    army = ArmyList(race="goblin", nick="Test Army", units=(bad_unit,))
    errors = validate_army(army, race)
    assert any("requires not satisfied" in e for e in errors)


def test_validate_army_upgrade_exactly_filling_slots_is_valid(
    simple_race: RaceConfig,
) -> None:
    # An upgrade that exactly fits remaining slots must not be flagged as invalid.
    # soldier has Hands:2; sword requires Hands:1; two swords exactly fill the slots.
    good_model = ArmyModel(
        name="soldier",
        config=simple_race.models["soldier"],
        upgrades=("sword", "sword"),
    )
    good_unit = ArmyUnit(
        name="squad", config=simple_race.units["squad"], models=(good_model,)
    )
    army = ArmyList(race="goblin", nick="Test Army", units=(good_unit,))
    errors = validate_army(army, simple_race)
    assert errors == []


def test_validate_army_upgrade_not_counted_against_itself(
    simple_race: RaceConfig,
) -> None:
    # A single upgrade using the model's entire slot budget must not be self-defeating.
    # soldier has Hands:2; a hypothetical "two_hand_sword" requires Hands:2.
    two_hand_sword = EquipmentConfig(
        race="goblin",
        name="Two-Hand Sword",
        cost=t.Cost(cp=4),
        upgrade_all=True,
        requires=[["Hands:2"]],  # pyright: ignore[reportArgumentType]
    )
    race = RaceConfig(
        races=simple_race.races,
        units=simple_race.units,
        models=simple_race.models,
        equipment={**simple_race.equipment, "two_hand_sword": two_hand_sword},
    )
    good_model = ArmyModel(
        name="soldier",
        config=race.models["soldier"],
        upgrades=("two_hand_sword",),
    )
    good_unit = ArmyUnit(name="squad", config=race.units["squad"], models=(good_model,))
    army = ArmyList(race="goblin", nick="Test Army", units=(good_unit,))
    errors = validate_army(army, race)
    assert errors == []


def test_validate_army_defaults_not_counted_for_slot_check(
    race_with_defaults: RaceConfig,
) -> None:
    # A model with a Hands:2 default and a Hands:1 upgrade must be valid —
    # the default is replaced by the upgrade and does not consume slots.
    good_model = ArmyModel(
        name="soldier",
        config=race_with_defaults.models["soldier"],
        upgrades=("sword",),
    )
    good_unit = ArmyUnit(
        name="squad", config=race_with_defaults.units["squad"], models=(good_model,)
    )
    army = ArmyList(race="goblin", nick="Test Army", units=(good_unit,))
    errors = validate_army(army, race_with_defaults)
    assert errors == []


def test_validate_army_still_catches_genuine_slot_overflow(
    simple_race: RaceConfig,
) -> None:
    # Three swords (each Hands:1) on a Hands:2 model must still fail.
    bad_model = ArmyModel(
        name="soldier",
        config=simple_race.models["soldier"],
        upgrades=("sword", "sword", "sword"),
    )
    bad_unit = ArmyUnit(
        name="squad", config=simple_race.units["squad"], models=(bad_model,)
    )
    army = ArmyList(race="goblin", nick="Test Army", units=(bad_unit,))
    errors = validate_army(army, simple_race)
    assert len(errors) == 1
    assert "Hands:1" in errors[0]


# ---------------------------------------------------------------------------
# Resolved Model.equipment — upgrades replace defaults
# ---------------------------------------------------------------------------


def test_model_equipment_no_upgrades_returns_defaults(simple_race: RaceConfig) -> None:
    # Add default equipment to soldier for this test
    sword_free = EquipmentConfig(
        race="goblin",
        name="Basic Sword",
        cost=None,
        requires=[],
    )
    race = RaceConfig(
        races=simple_race.races,
        units=simple_race.units,
        models={
            "soldier": simple_race.models["soldier"].model_copy(
                update={"equipment": ["basic_sword"]}
            ),
            "elite_soldier": simple_race.models["elite_soldier"],
        },
        equipment={**simple_race.equipment, "basic_sword": sword_free},
    )
    army = ArmyList(race="goblin", nick="T", units=()).add_unit("squad", race)
    resolved = army.resolve(race)
    model = resolved.units[0].models[0]
    assert len(model.default_equipment) == 1
    assert model.upgrade_equipment == ()
    assert model.equipment == model.default_equipment


def test_model_equipment_upgrades_present_discards_defaults(
    simple_race: RaceConfig,
) -> None:
    sword_free = EquipmentConfig(
        race="goblin",
        name="Basic Sword",
        cost=None,
        requires=[],
    )
    race = RaceConfig(
        races=simple_race.races,
        units=simple_race.units,
        models={
            "soldier": simple_race.models["soldier"].model_copy(
                update={"equipment": ["basic_sword"]}
            ),
            "elite_soldier": simple_race.models["elite_soldier"],
        },
        equipment={**simple_race.equipment, "basic_sword": sword_free},
    )
    army = (
        ArmyList(race="goblin", nick="T", units=())
        .add_unit("squad", race)
        .upgrade_model(("squad", 0), ("soldier", 0), "sword", race)
    )
    resolved = army.resolve(race)
    model = resolved.units[0].models[0]
    # defaults have basic_sword; upgrade has sword
    # — upgrades replace defaults, so only sword
    assert model.equipment == model.upgrade_equipment
    assert all(e.name != "Basic Sword" for e in model.equipment)


# ---------------------------------------------------------------------------
# Resolved Model specials stacking
# ---------------------------------------------------------------------------


def test_model_unit_specials_base_from_config(simple_race: RaceConfig) -> None:
    model_cfg = simple_race.models["soldier"].model_copy(
        update={"unit_special": {"Take Cover": "desc"}}
    )
    race = simple_race.model_copy(
        update={"models": {**simple_race.models, "soldier": model_cfg}}
    )
    resolved = (
        ArmyList(race="goblin", nick="T", units=())
        .add_unit("squad", race)
        .resolve(race)
    )
    assert "Take Cover" in resolved.units[0].models[0].unit_specials


def test_model_unit_specials_equipment_overrides(simple_race: RaceConfig) -> None:
    equip = EquipmentConfig(
        race="goblin",
        name="Magic Sword",
        cost=t.Cost(cp=5),
        upgrade_all=True,
        requires=[],
        unit_special={"Terror": "upgraded terror"},
    )
    model_cfg = simple_race.models["soldier"].model_copy(
        update={"unit_special": {"Terror": "base terror"}}
    )
    race = RaceConfig(
        races=simple_race.races,
        units=simple_race.units,
        models={**simple_race.models, "soldier": model_cfg},
        equipment={**simple_race.equipment, "magic_sword": equip},
    )
    army = (
        ArmyList(race="goblin", nick="T", units=())
        .add_unit("squad", race)
        .upgrade_model(("squad", 0), ("soldier", 0), "magic_sword", race)
    )
    resolved = army.resolve(race)
    assert resolved.units[0].models[0].unit_specials["Terror"] == "upgraded terror"


def test_model_model_specials_stacked(simple_race: RaceConfig) -> None:
    equip = EquipmentConfig(
        race="goblin",
        name="Scope",
        cost=t.Cost(cp=1),
        upgrade_all=True,
        requires=[],
        model_special={"To Hit": "improves"},
    )
    race = RaceConfig(
        races=simple_race.races,
        units=simple_race.units,
        models=simple_race.models,
        equipment={**simple_race.equipment, "scope": equip},
    )
    army = (
        ArmyList(race="goblin", nick="T", units=())
        .add_unit("squad", race)
        .upgrade_model(("squad", 0), ("soldier", 0), "scope", race)
    )
    resolved = army.resolve(race)
    assert "To Hit" in resolved.units[0].models[0].model_specials


def test_unit_unit_specials_merges_model_contributions(simple_race: RaceConfig) -> None:
    unit_cfg = simple_race.units["squad"].model_copy(
        update={"special": {"Take Cover": "unit level"}}
    )
    model_cfg = simple_race.models["soldier"].model_copy(
        update={"unit_special": {"Terror": "model contributes"}}
    )
    race = RaceConfig(
        races=simple_race.races,
        units={"squad": unit_cfg},
        models={**simple_race.models, "soldier": model_cfg},
        equipment=simple_race.equipment,
    )
    resolved = (
        ArmyList(race="goblin", nick="T", units=())
        .add_unit("squad", race)
        .resolve(race)
    )
    unit_specials = resolved.units[0].unit_specials
    assert "Take Cover" in unit_specials
    assert "Terror" in unit_specials


# ---------------------------------------------------------------------------
# Resolved Model.assault() Stacker application
# ---------------------------------------------------------------------------


def test_model_assault_no_equipment_returns_base(simple_race: RaceConfig) -> None:
    resolved = (
        ArmyList(race="goblin", nick="T", units=())
        .add_unit("squad", simple_race)
        .resolve(simple_race)
    )
    a = resolved.units[0].models[0].assault()
    base = simple_race.models["soldier"].assault
    assert a.strength == base.strength
    assert a.ap == base.ap
    assert a.damage == base.damage


def test_model_assault_add_scalar_ap(simple_race: RaceConfig) -> None:
    equip = EquipmentConfig(
        race="goblin",
        name="AP Ammo",
        cost=t.Cost(cp=2),
        upgrade_all=True,
        requires=[],
        assault=EquipmentAssaultConfig(ap=Stacker(add=2)),
    )
    race = RaceConfig(
        races=simple_race.races,
        units=simple_race.units,
        models=simple_race.models,
        equipment={**simple_race.equipment, "ap_ammo": equip},
    )
    army = (
        ArmyList(race="goblin", nick="T", units=())
        .add_unit("squad", race)
        .upgrade_model(("squad", 0), ("soldier", 0), "ap_ammo", race)
    )
    resolved = army.resolve(race)
    # base ap=0 + add=2 → 2
    assert resolved.units[0].models[0].assault().ap == 2


def test_model_assault_add_angles_element_wise(simple_race: RaceConfig) -> None:
    equip = EquipmentConfig(
        race="goblin",
        name="Power Weapon",
        cost=t.Cost(cp=3),
        upgrade_all=True,
        requires=[],
        assault=EquipmentAssaultConfig(strength=Stacker(add=[1, 0, 1, 0])),
    )
    race = RaceConfig(
        races=simple_race.races,
        units=simple_race.units,
        models=simple_race.models,
        equipment={**simple_race.equipment, "power_weapon": equip},
    )
    army = (
        ArmyList(race="goblin", nick="T", units=())
        .add_unit("squad", race)
        .upgrade_model(("squad", 0), ("soldier", 0), "power_weapon", race)
    )
    resolved = army.resolve(race)
    # base strength=[1,0,0,0] + add=[1,0,1,0] → [2,0,1,0]
    assert resolved.units[0].models[0].assault().strength == [2, 0, 1, 0]


def test_model_assault_replace_damage(simple_race: RaceConfig) -> None:
    equip = EquipmentConfig(
        race="goblin",
        name="Big Weapon",
        cost=t.Cost(cp=4),
        upgrade_all=True,
        requires=[],
        assault=EquipmentAssaultConfig(damage=Stacker(replace="2d6")),
    )
    race = RaceConfig(
        races=simple_race.races,
        units=simple_race.units,
        models=simple_race.models,
        equipment={**simple_race.equipment, "big_weapon": equip},
    )
    army = (
        ArmyList(race="goblin", nick="T", units=())
        .add_unit("squad", race)
        .upgrade_model(("squad", 0), ("soldier", 0), "big_weapon", race)
    )
    resolved = army.resolve(race)
    assert resolved.units[0].models[0].assault().damage == "2d6"


def test_model_assault_add_on_die_raises(simple_race: RaceConfig) -> None:
    equip = EquipmentConfig(
        race="goblin",
        name="Bad Weapon",
        cost=t.Cost(cp=1),
        upgrade_all=True,
        requires=[],
        assault=EquipmentAssaultConfig(damage=Stacker(add="extra")),
    )
    race = RaceConfig(
        races=simple_race.races,
        units=simple_race.units,
        models=simple_race.models,
        equipment={**simple_race.equipment, "bad_weapon": equip},
    )
    army = (
        ArmyList(race="goblin", nick="T", units=())
        .add_unit("squad", race)
        .upgrade_model(("squad", 0), ("soldier", 0), "bad_weapon", race)
    )
    resolved = army.resolve(race)
    with pytest.raises(ValueError, match=r"'add'.*'damage'|'damage'.*'add'"):
        resolved.units[0].models[0].assault()


def test_model_assault_add_on_na_ap_raises(simple_race: RaceConfig) -> None:
    na_assault = _ASSAULT.model_copy(update={"ap": "N/A"})
    model_cfg = simple_race.models["soldier"].model_copy(update={"assault": na_assault})
    equip = EquipmentConfig(
        race="goblin",
        name="AP Boost",
        cost=t.Cost(cp=2),
        upgrade_all=True,
        requires=[],
        assault=EquipmentAssaultConfig(ap=Stacker(add=1)),
    )
    race = RaceConfig(
        races=simple_race.races,
        units=simple_race.units,
        models={**simple_race.models, "soldier": model_cfg},
        equipment={**simple_race.equipment, "ap_boost": equip},
    )
    army = (
        ArmyList(race="goblin", nick="T", units=())
        .add_unit("squad", race)
        .upgrade_model(("squad", 0), ("soldier", 0), "ap_boost", race)
    )
    resolved = army.resolve(race)
    with pytest.raises(ValueError, match="N/A"):
        resolved.units[0].models[0].assault()


# ---------------------------------------------------------------------------
# Unit.cost() upgrade_all logic
# ---------------------------------------------------------------------------


def test_unit_cost_upgrade_all_false_multiplies_by_unit_size(
    simple_race: RaceConfig,
) -> None:
    # Create a 2-model unit and per-model equipment
    per_model_equip = EquipmentConfig(
        race="goblin",
        name="Per Model Gear",
        cost=t.Cost(cp=1),
        upgrade_all=False,
        requires=[],
    )
    unit_cfg = UnitConfig(
        race="goblin",
        name="Two Squad",
        models=["soldier", "soldier"],
        size="Small",
        cost=None,
        shaken=ShakenConfig(speed="slow", movement_order=["-", "-", "flee"]),
        special={},
        orders=OrdersConfig(),
        armor=None,
        damage_tables={"regular": ["Fine", "Dead"]},
    )
    race = RaceConfig(
        races=simple_race.races,
        units={"two_squad": unit_cfg},
        models=simple_race.models,
        equipment={**simple_race.equipment, "per_model_gear": per_model_equip},
    )
    army = (
        ArmyList(race="goblin", nick="T", units=())
        .add_unit("two_squad", race)
        .upgrade_model(("two_squad", 0), ("soldier", 0), "per_model_gear", race)
    )
    resolved = army.resolve(race)
    # cost = 1cp * 2 models = 2cp
    assert resolved.units[0].cost() == t.Cost(cp=2)


def test_unit_cost_upgrade_all_true_flat(simple_race: RaceConfig) -> None:
    unit_cfg = UnitConfig(
        race="goblin",
        name="Two Squad",
        models=["soldier", "soldier"],
        size="Small",
        cost=None,
        shaken=ShakenConfig(speed="slow", movement_order=["-", "-", "flee"]),
        special={},
        orders=OrdersConfig(),
        armor=None,
        damage_tables={"regular": ["Fine", "Dead"]},
    )
    race = RaceConfig(
        races=simple_race.races,
        units={"two_squad": unit_cfg},
        models=simple_race.models,
        equipment=simple_race.equipment,
    )
    army = (
        ArmyList(race="goblin", nick="T", units=())
        .add_unit("two_squad", race)
        .upgrade_model(("two_squad", 0), ("soldier", 0), "sword", race)
    )
    resolved = army.resolve(race)
    # sword upgrade_all=True, cost=cp=2 → flat, regardless of 2 models
    assert resolved.units[0].cost() == t.Cost(cp=2)


# ---------------------------------------------------------------------------
# ArmyList.resolve() structure preservation
# ---------------------------------------------------------------------------


def test_resolve_preserves_unit_count(simple_race: RaceConfig) -> None:
    army = (
        ArmyList(race="goblin", nick="T", units=())
        .add_unit("squad", simple_race)
        .add_unit("squad", simple_race)
    )
    resolved = army.resolve(simple_race)
    assert len(resolved.units) == 2


def test_resolve_populates_default_equipment(simple_race: RaceConfig) -> None:
    sword_free = EquipmentConfig(
        race="goblin",
        name="Basic Sword",
        cost=None,
        requires=[],
    )
    race = RaceConfig(
        races=simple_race.races,
        units=simple_race.units,
        models={
            "soldier": simple_race.models["soldier"].model_copy(
                update={"equipment": ["basic_sword"]}
            ),
            "elite_soldier": simple_race.models["elite_soldier"],
        },
        equipment={**simple_race.equipment, "basic_sword": sword_free},
    )
    resolved = (
        ArmyList(race="goblin", nick="T", units=())
        .add_unit("squad", race)
        .resolve(race)
    )
    model = resolved.units[0].models[0]
    assert len(model.default_equipment) == 1
    assert model.default_equipment[0].name == "Basic Sword"


def test_resolve_populates_upgrade_equipment(
    one_unit_army: ArmyList, simple_race: RaceConfig
) -> None:
    army = one_unit_army.upgrade_model(
        ("squad", 0), ("soldier", 0), "sword", simple_race
    )
    resolved = army.resolve(simple_race)
    model = resolved.units[0].models[0]
    assert len(model.upgrade_equipment) == 1
    assert model.upgrade_equipment[0].name == "Sword"
