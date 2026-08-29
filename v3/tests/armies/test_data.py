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
from spf.armies.model import Model
from spf.armies.unit import Unit
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
from spf.schemas.special import SpecialInstance

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
                size="small",
                cost=t.Cost(mp=3),
                shaken=ShakenConfig(speed="slow", movement_order=["-", "-", "flee"]),
                orders=OrdersConfig(),
                armor=None,
                damage_tables={"Regular": {"rows": ["1: Fine", "2: Dead"]}},  # pyright: ignore[reportArgumentType]
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
    return ArmyList(race="goblin", nick="Test Army", units=[])


@pytest.fixture
def one_unit_army(simple_race: RaceConfig) -> ArmyList:
    return ArmyList(race="goblin", nick="Test Army", units=[]).add_unit(
        "squad", race_config=simple_race
    )


@pytest.fixture
def goblin_race() -> RaceConfig:
    return get_race("goblin")


@pytest.fixture
def goblin_army(goblin_race: RaceConfig) -> ArmyList:
    return ArmyList(race="goblin", nick="Test Army", units=[]).add_unit(
        "goblin_infantry", race_config=goblin_race
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
    model = ArmyModel(name="soldier", config=simple_race.models["soldier"], upgrades=[])
    assert model.upgrades == []


def test_army_model_is_frozen(simple_race: RaceConfig) -> None:
    model = ArmyModel(name="soldier", config=simple_race.models["soldier"], upgrades=[])
    with pytest.raises((AttributeError, TypeError)):
        model.upgrades = ("sword",)  # pyright: ignore[reportAttributeAccessIssue]


def test_army_unit_default_models_match_config(one_unit_army: ArmyList) -> None:
    unit = one_unit_army.units[0]
    assert tuple(m.name for m in unit.models) == tuple(unit.config.models)


def test_army_list_is_frozen(empty_army: ArmyList) -> None:
    with pytest.raises((AttributeError, TypeError)):
        empty_army.units = ()  # pyright: ignore[reportAttributeAccessIssue]


def test_army_list_allows_duplicate_units(simple_race: RaceConfig) -> None:
    army = ArmyList(race="goblin", nick="Test Army", units=[])
    army = army.add_unit("squad", race_config=simple_race)
    army = army.add_unit("squad", race_config=simple_race)
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


# ---------------------------------------------------------------------------
# Cost rendering and sorting
# ---------------------------------------------------------------------------


def test_cost_str_renders_every_dimension_in_order() -> None:
    assert str(t.Cost(ip=1, mp=2, xp=3, cp=4, vpm=5)) == " 1ip  2mp  3xp  4cp  5vpm"


def test_cost_str_grays_out_only_the_zero_dimensions() -> None:
    assert str(t.Cost(ip=1, cp=4)) == (
        " 1ip [gray30] 0mp[/] [gray30] 0xp[/]  4cp [gray30] 0vpm[/]"
    )


def test_cost_str_grays_out_an_empty_cost_entirely() -> None:
    assert str(t.Cost()) == (
        "[gray30] 0ip[/] [gray30] 0mp[/] [gray30] 0xp[/]"
        " [gray30] 0cp[/] [gray30] 0vpm[/]"
    )


def test_cost_str_does_not_truncate_a_two_digit_value() -> None:
    # The 2-wide field pads, it does not clip.
    assert str(t.Cost(mp=12)) == (
        "[gray30] 0ip[/] 12mp [gray30] 0xp[/] [gray30] 0cp[/] [gray30] 0vpm[/]"
    )


def test_cost_sort_idx_orders_ip_then_mp_then_xp_then_cp() -> None:
    costs = [t.Cost(), t.Cost(cp=1), t.Cost(xp=1), t.Cost(mp=1), t.Cost(ip=1)]
    assert sorted(costs, key=lambda cost: cost.sort_idx) == [
        t.Cost(ip=1),
        t.Cost(mp=1),
        t.Cost(xp=1),
        t.Cost(cp=1),
        t.Cost(),
    ]


def test_cost_sort_idx_is_ip_dominant() -> None:
    """A single ip outranks any pile of the lesser dimensions."""
    assert t.Cost(ip=1).sort_idx < t.Cost(mp=999, xp=999, cp=999).sort_idx


# ---------------------------------------------------------------------------
# Unit and army costs
# ---------------------------------------------------------------------------


def test_unit_cost_base_only(
    one_unit_army: ArmyList, *, simple_race: RaceConfig
) -> None:
    resolved = one_unit_army.resolve(simple_race)
    assert resolved.units[0].cost() == t.Cost(mp=3)


def test_unit_cost_with_upgrade_model(
    one_unit_army: ArmyList, *, simple_race: RaceConfig
) -> None:
    army = one_unit_army.upgrade_unit(
        ("squad", 0),
        model_key=("soldier", 0),
        upgrade_model_name="elite_soldier",
        race_config=simple_race,
    )
    resolved = army.resolve(simple_race)
    assert resolved.units[0].cost() == t.Cost(mp=3, xp=1)  # base + upgrade


def test_unit_cost_with_equipment_upgrade(
    one_unit_army: ArmyList, *, simple_race: RaceConfig
) -> None:
    army = one_unit_army.upgrade_model(
        ("squad", 0),
        model_key=("soldier", 0),
        equipment_name="sword",
        race_config=simple_race,
    )
    resolved = army.resolve(simple_race)
    assert resolved.units[0].cost() == t.Cost(mp=3, cp=2)


def test_unit_points_formula(
    one_unit_army: ArmyList, *, simple_race: RaceConfig
) -> None:
    # squad costs mp=3, so points = 3
    resolved = one_unit_army.resolve(simple_race)
    assert resolved.units[0].cost().to_points() == 3


def test_unit_points_ip_weighted(simple_race: RaceConfig) -> None:
    # elite_soldier adds xp=1 → points = 3 + 1 = 4
    army = (
        ArmyList(race="goblin", nick="T", units=[])
        .add_unit("squad", race_config=simple_race)
        .upgrade_unit(
            ("squad", 0),
            model_key=("soldier", 0),
            upgrade_model_name="elite_soldier",
            race_config=simple_race,
        )
    )
    resolved = army.resolve(simple_race)
    assert resolved.units[0].cost().to_points() == 4


def test_unit_points_zero_cost(simple_race: RaceConfig) -> None:
    zero_cost_unit = simple_race.units["squad"].model_copy(update={"cost": t.Cost()})
    zero_cost_race = simple_race.model_copy(update={"units": {"squad": zero_cost_unit}})
    army = ArmyList(race="goblin", nick="T", units=[]).add_unit(
        "squad", race_config=zero_cost_race
    )
    resolved = army.resolve(zero_cost_race)
    assert resolved.units[0].cost().to_points() == 0


def test_army_cost_empty(simple_race: RaceConfig) -> None:
    resolved = ArmyList(race="goblin", nick="Test Army", units=[]).resolve(simple_race)
    assert resolved.cost() == t.Cost()


def test_army_cost_includes_unit_base(
    one_unit_army: ArmyList, *, simple_race: RaceConfig
) -> None:
    resolved = one_unit_army.resolve(simple_race)
    assert resolved.cost() == t.Cost(mp=3)


def test_army_cost_includes_upgrade_model(
    one_unit_army: ArmyList, *, simple_race: RaceConfig
) -> None:
    army = one_unit_army.upgrade_unit(
        ("squad", 0),
        model_key=("soldier", 0),
        upgrade_model_name="elite_soldier",
        race_config=simple_race,
    )
    resolved = army.resolve(simple_race)
    assert resolved.cost() == t.Cost(mp=3, xp=1)


def test_army_cost_includes_upgrade_equipment(
    one_unit_army: ArmyList, *, simple_race: RaceConfig
) -> None:
    army = one_unit_army.upgrade_model(
        ("squad", 0),
        model_key=("soldier", 0),
        equipment_name="sword",
        race_config=simple_race,
    )
    resolved = army.resolve(simple_race)
    assert resolved.cost() == t.Cost(mp=3, cp=2)


def _soldier(
    race_config: RaceConfig,
    *,
    defaults: list[EquipmentConfig] | None = None,
    upgrades: list[EquipmentConfig] | None = None,
) -> Model:
    """Build a resolved soldier carrying the given equipment."""
    return Model(
        name="soldier",
        config=race_config.models["soldier"],
        default_equipment=defaults or [],
        upgrade_equipment=upgrades or [],
    )


def test_model_cost_without_upgrade_equipment_is_free(simple_race: RaceConfig) -> None:
    assert _soldier(simple_race).cost() == t.Cost()


def test_model_cost_sums_its_upgrade_equipment(simple_race: RaceConfig) -> None:
    grenade = EquipmentConfig(
        race="goblin",
        name="Grenade",
        cost=t.Cost(mp=1, xp=3),
        upgrade_all=False,
        requires=[],
    )
    model = _soldier(simple_race, upgrades=[simple_race.equipment["sword"], grenade])
    assert model.cost() == t.Cost(cp=2, mp=1, xp=3)


def test_model_cost_ignores_priced_default_equipment(simple_race: RaceConfig) -> None:
    """Retained Defaults are free however the catalogue prices them (ADR-0020)."""
    priced_default = EquipmentConfig(
        race="goblin",
        name="Issued Sword",
        cost=t.Cost(cp=7),
        upgrade_all=False,
        requires=[],
    )
    assert _soldier(simple_race, defaults=[priced_default]).cost() == t.Cost()


def test_model_cost_charges_a_unit_fixture_that_unit_cost_charges_once(
    simple_race: RaceConfig,
) -> None:
    """Model.cost() charges an `upgrade_all` Equipment per Model, Unit.cost() once.

    The divergence is intended, not a rounding error: a Model cannot see its
    siblings, so only Unit.cost() can deduplicate a Fixture (ADR-0026).
    """
    sword = simple_race.equipment["sword"]  # upgrade_all, cp=2
    models = [_soldier(simple_race, upgrades=[sword]) for _ in range(2)]
    unit = Unit(
        name="squad",
        config=simple_race.units["squad"].model_copy(
            update={"models": ["soldier", "soldier"]}
        ),
        models=models,
    )

    assert [model.cost() for model in models] == [t.Cost(cp=2), t.Cost(cp=2)]
    assert unit.cost() == t.Cost(mp=3, cp=2)


# ---------------------------------------------------------------------------
# Requires logic
# ---------------------------------------------------------------------------


def test_satisfies_requires_type_match(simple_race: RaceConfig) -> None:
    soldier = ArmyModel(
        name="soldier", config=simple_race.models["soldier"], upgrades=[]
    )
    assert _satisfies_requires(
        simple_race.equipment["sword"].requires, model=soldier, race_config=simple_race
    )


def test_satisfies_requires_type_mismatch(simple_race: RaceConfig) -> None:
    req = [[t.Requirement(key="type", value="Cavalry")]]
    soldier = ArmyModel(
        name="soldier", config=simple_race.models["soldier"], upgrades=[]
    )
    assert not _satisfies_requires(req, model=soldier, race_config=simple_race)


def test_satisfies_requires_holder_sufficient(simple_race: RaceConfig) -> None:
    req = [[t.Requirement(key="Hands", value=1)]]
    soldier = ArmyModel(
        name="soldier", config=simple_race.models["soldier"], upgrades=[]
    )
    assert _satisfies_requires(req, model=soldier, race_config=simple_race)


def test_satisfies_requires_holder_insufficient(simple_race: RaceConfig) -> None:
    req = [[t.Requirement(key="Hands", value=3)]]
    soldier = ArmyModel(
        name="soldier", config=simple_race.models["soldier"], upgrades=[]
    )
    assert not _satisfies_requires(req, model=soldier, race_config=simple_race)


def test_satisfies_requires_cnf_all_groups_needed(simple_race: RaceConfig) -> None:
    req = [
        [t.Requirement(key="Hands", value=1)],
        [t.Requirement(key="type", value="Cavalry")],
    ]
    soldier = ArmyModel(
        name="soldier", config=simple_race.models["soldier"], upgrades=[]
    )
    assert not _satisfies_requires(req, model=soldier, race_config=simple_race)


# ---------------------------------------------------------------------------
# _unsatisfied_groups and _format_failed_group
# ---------------------------------------------------------------------------


def test_unsatisfied_groups_all_satisfied(simple_race: RaceConfig) -> None:
    soldier = ArmyModel(
        name="soldier", config=simple_race.models["soldier"], upgrades=[]
    )
    assert (
        _unsatisfied_groups(
            simple_race.equipment["sword"].requires,
            model=soldier,
            race_config=simple_race,
        )
        == []
    )


def test_unsatisfied_groups_type_failure_returns_group(simple_race: RaceConfig) -> None:
    soldier = ArmyModel(
        name="soldier", config=simple_race.models["soldier"], upgrades=[]
    )
    req = [[t.Requirement(key="type", value="Cavalry")]]
    failed = _unsatisfied_groups(req, model=soldier, race_config=simple_race)
    assert len(failed) == 1
    assert failed[0] == [t.Requirement(key="type", value="Cavalry")]


def test_unsatisfied_groups_slot_failure_returns_group(simple_race: RaceConfig) -> None:
    soldier = ArmyModel(
        name="soldier", config=simple_race.models["soldier"], upgrades=[]
    )
    req = [[t.Requirement(key="Hands", value=3)]]
    failed = _unsatisfied_groups(req, model=soldier, race_config=simple_race)
    assert len(failed) == 1


def test_format_failed_group_type_only(simple_race: RaceConfig) -> None:
    soldier = ArmyModel(
        name="soldier", config=simple_race.models["soldier"], upgrades=[]
    )
    remaining = _remaining_slots(soldier, race_config=simple_race)
    group = [
        t.Requirement(key="type", value="Infantry"),
        t.Requirement(key="type", value="Grunt"),
    ]
    result = _format_failed_group(group, remaining_slots=remaining)
    assert result == "needs type:Infantry or type:Grunt"


def test_format_failed_group_slot_shows_available(simple_race: RaceConfig) -> None:
    soldier = ArmyModel(
        name="soldier", config=simple_race.models["soldier"], upgrades=[]
    )
    remaining = _remaining_slots(soldier, race_config=simple_race)
    group = [t.Requirement(key="Hands", value=2)]
    result = _format_failed_group(group, remaining_slots=remaining)
    assert "Hands:2" in result
    assert "have" in result


# ---------------------------------------------------------------------------
# _remaining_slots — default equipment does not consume slots
# ---------------------------------------------------------------------------


def test_remaining_slots_does_not_count_default_equipment(
    race_with_defaults: RaceConfig,
) -> None:
    # Upgrade legality is decided by the upgrades alone (ADR-0020): defaults
    # yield their holders instead of blocking a purchase, so they must never
    # consume slots. A soldier with a Hands:2 default but no upgrades should
    # still show Hands:2 free.
    soldier = ArmyModel(
        name="soldier", config=race_with_defaults.models["soldier"], upgrades=[]
    )
    remaining = _remaining_slots(soldier, race_config=race_with_defaults)
    assert remaining.get("Hands", 0) == 2


def test_remaining_slots_counts_only_upgrades_when_upgrades_present(
    race_with_defaults: RaceConfig,
) -> None:
    # With a Hands:2 default and a Hands:1 upgrade, only the upgrade is counted.
    soldier = ArmyModel(
        name="soldier",
        config=race_with_defaults.models["soldier"],
        upgrades=[
            "sword",
        ],
    )
    remaining = _remaining_slots(soldier, race_config=race_with_defaults)
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
        upgrades=[
            "elite_sword",
        ],
    )
    bad_unit = ArmyUnit(name="squad", config=race.units["squad"], models=[bad_model])
    army = ArmyList(race="goblin", nick="Test Army", units=[bad_unit])
    errors = validate_army(army, race_config=race)
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
        upgrades=[
            "greedy_sword",
        ],
    )
    bad_unit = ArmyUnit(name="squad", config=race.units["squad"], models=[bad_model])
    army = ArmyList(race="goblin", nick="Test Army", units=[bad_unit])
    errors = validate_army(army, race_config=race)
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
        upgrades=[
            "impossible_sword",
        ],
    )
    bad_unit = ArmyUnit(name="squad", config=race.units["squad"], models=[bad_model])
    army = ArmyList(race="goblin", nick="Test Army", units=[bad_unit])
    errors = validate_army(army, race_config=race)
    assert any("type:Cavalry" in e and "Hands:10" in e for e in errors)


# ---------------------------------------------------------------------------
# add_unit
# ---------------------------------------------------------------------------


def test_add_unit_appends_to_army(simple_race: RaceConfig) -> None:
    army = ArmyList(race="goblin", nick="Test Army", units=[]).add_unit(
        "squad", race_config=simple_race
    )
    assert len(army.units) == 1
    assert army.units[0].name == "squad"


def test_add_unit_default_models_match_config(simple_race: RaceConfig) -> None:
    army = ArmyList(race="goblin", nick="Test Army", units=[]).add_unit(
        "squad", race_config=simple_race
    )
    unit = army.units[0]
    assert tuple(m.name for m in unit.models) == tuple(unit.config.models)


def test_add_unit_unknown_name_raises(simple_race: RaceConfig) -> None:
    with pytest.raises(ValueError, match="Unknown unit"):
        ArmyList(race="goblin", nick="Test Army", units=[]).add_unit(
            "does_not_exist", race_config=simple_race
        )


def test_add_unit_defaults_to_no_nick(simple_race: RaceConfig) -> None:
    army = ArmyList(race="goblin", nick="Test Army", units=[]).add_unit(
        "squad", race_config=simple_race
    )
    assert army.units[0].nick is None
    assert army.units[0].models[0].nick is None


def test_add_unit_stores_nick(simple_race: RaceConfig) -> None:
    army = ArmyList(race="goblin", nick="Test Army", units=[]).add_unit(
        "squad", nick="Boyz", race_config=simple_race
    )
    assert army.units[0].nick == "Boyz"
    assert army.units[0].name == "squad"


def test_add_unit_empty_nick_raises(simple_race: RaceConfig) -> None:
    with pytest.raises(ValueError, match="Nick cannot be empty"):
        ArmyList(race="goblin", nick="Test Army", units=[]).add_unit(
            "squad", nick="  ", race_config=simple_race
        )


# ---------------------------------------------------------------------------
# upgrade_unit
# ---------------------------------------------------------------------------


def test_upgrade_unit_valid_replacement(
    one_unit_army: ArmyList, *, simple_race: RaceConfig
) -> None:
    army = one_unit_army.upgrade_unit(
        ("squad", 0),
        model_key=("soldier", 0),
        upgrade_model_name="elite_soldier",
        race_config=simple_race,
    )
    assert army.units[0].models[0].name == "elite_soldier"


def test_upgrade_unit_does_not_mutate_original(
    one_unit_army: ArmyList, *, simple_race: RaceConfig
) -> None:
    one_unit_army.upgrade_unit(
        ("squad", 0),
        model_key=("soldier", 0),
        upgrade_model_name="elite_soldier",
        race_config=simple_race,
    )
    assert one_unit_army.units[0].models[0].name == "soldier"


def test_upgrade_unit_invalid_replaces_raises(
    one_unit_army: ArmyList, *, simple_race: RaceConfig
) -> None:
    with pytest.raises(ValueError, match="cannot replace"):
        one_unit_army.upgrade_unit(
            ("squad", 0),
            model_key=("soldier", 0),
            upgrade_model_name="soldier",
            race_config=simple_race,
        )


def test_upgrade_unit_unknown_unit_key_raises(
    one_unit_army: ArmyList, *, simple_race: RaceConfig
) -> None:
    with pytest.raises(KeyError):
        one_unit_army.upgrade_unit(
            ("nonexistent", 0),
            model_key=("soldier", 0),
            upgrade_model_name="elite_soldier",
            race_config=simple_race,
        )


def test_upgrade_unit_unknown_model_key_raises(
    one_unit_army: ArmyList, *, simple_race: RaceConfig
) -> None:
    with pytest.raises(KeyError):
        one_unit_army.upgrade_unit(
            ("squad", 0),
            model_key=("nonexistent", 0),
            upgrade_model_name="elite_soldier",
            race_config=simple_race,
        )


# ---------------------------------------------------------------------------
# upgrade_model
# ---------------------------------------------------------------------------


def test_upgrade_model_adds_to_upgrades(
    one_unit_army: ArmyList, *, simple_race: RaceConfig
) -> None:
    army = one_unit_army.upgrade_model(
        ("squad", 0),
        model_key=("soldier", 0),
        equipment_name="sword",
        race_config=simple_race,
    )
    assert "sword" in army.units[0].models[0].upgrades


def test_upgrade_model_does_not_mutate_original(
    one_unit_army: ArmyList, *, simple_race: RaceConfig
) -> None:
    one_unit_army.upgrade_model(
        ("squad", 0),
        model_key=("soldier", 0),
        equipment_name="sword",
        race_config=simple_race,
    )
    assert one_unit_army.units[0].models[0].upgrades == []


def test_upgrade_model_no_cost_raises(
    one_unit_army: ArmyList, *, simple_race: RaceConfig
) -> None:
    with pytest.raises(ValueError, match="no cost"):
        one_unit_army.upgrade_model(
            ("squad", 0),
            model_key=("soldier", 0),
            equipment_name="shield",
            race_config=simple_race,
        )


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
    army = ArmyList(race="goblin", nick="Test Army", units=[]).add_unit(
        "squad", race_config=race
    )
    with pytest.raises(ValueError, match="requires not satisfied"):
        army.upgrade_model(
            ("squad", 0),
            model_key=("soldier", 0),
            equipment_name="elite_sword",
            race_config=race,
        )


def test_upgrade_model_unknown_key_raises(
    one_unit_army: ArmyList, *, simple_race: RaceConfig
) -> None:
    with pytest.raises(KeyError):
        one_unit_army.upgrade_model(
            ("nonexistent", 0),
            model_key=("soldier", 0),
            equipment_name="sword",
            race_config=simple_race,
        )


# ---------------------------------------------------------------------------
# upgrade_full_unit
# ---------------------------------------------------------------------------


def test_upgrade_full_unit_replaces_all_models(
    goblin_race: RaceConfig,
) -> None:
    army = ArmyList(race="goblin", nick="Test", units=[]).add_unit(
        "goblin_infantry", race_config=goblin_race
    )
    assert len(army.units[0].models) == 4
    army = army.upgrade_full_unit(
        ("goblin_infantry", 0),
        upgrade_model_name="elite_goblin_infantry",
        race_config=goblin_race,
    )
    assert all(m.name == "elite_goblin_infantry" for m in army.units[0].models)


def test_upgrade_full_unit_does_not_mutate_original(
    simple_race: RaceConfig,
) -> None:
    army = ArmyList(race="goblin", nick="Test", units=[]).add_unit(
        "squad", race_config=simple_race
    )
    original = army
    army.upgrade_full_unit(
        ("squad", 0), upgrade_model_name="elite_soldier", race_config=simple_race
    )
    assert original.units[0].models[0].name == "soldier"


def test_upgrade_full_unit_invalid_replacement_raises(
    one_unit_army: ArmyList, *, simple_race: RaceConfig
) -> None:
    with pytest.raises(ValueError, match="cannot replace"):
        one_unit_army.upgrade_full_unit(
            ("squad", 0), upgrade_model_name="soldier", race_config=simple_race
        )


def test_upgrade_full_unit_unknown_unit_key_raises(
    one_unit_army: ArmyList, *, simple_race: RaceConfig
) -> None:
    with pytest.raises(KeyError):
        one_unit_army.upgrade_full_unit(
            ("nonexistent", 0),
            upgrade_model_name="elite_soldier",
            race_config=simple_race,
        )


# ---------------------------------------------------------------------------
# upgrade_all_models
# ---------------------------------------------------------------------------


def test_upgrade_all_models_adds_to_all(
    goblin_race: RaceConfig,
) -> None:
    army = ArmyList(race="goblin", nick="Test", units=[]).add_unit(
        "goblin_infantry", race_config=goblin_race
    )
    # Use equipment that doesn't consume limited slots
    army = army.upgrade_all_models(
        ("goblin_infantry", 0),
        equipment_name="poison_deflection_dagger",
        race_config=goblin_race,
    )
    assert all("poison_deflection_dagger" in m.upgrades for m in army.units[0].models)


def test_upgrade_all_models_does_not_mutate_original(
    one_unit_army: ArmyList, *, simple_race: RaceConfig
) -> None:
    original = one_unit_army
    one_unit_army.upgrade_all_models(
        ("squad", 0), equipment_name="sword", race_config=simple_race
    )
    assert original.units[0].models[0].upgrades == []


def test_upgrade_all_models_no_cost_raises(
    one_unit_army: ArmyList, *, simple_race: RaceConfig
) -> None:
    with pytest.raises(ValueError, match="no cost"):
        one_unit_army.upgrade_all_models(
            ("squad", 0), equipment_name="shield", race_config=simple_race
        )


def test_upgrade_all_models_unsatisfied_requires_raises(
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
    army = ArmyList(race="goblin", nick="Test Army", units=[]).add_unit(
        "squad", race_config=race
    )
    with pytest.raises(ValueError, match="requires not satisfied"):
        army.upgrade_all_models(
            ("squad", 0), equipment_name="elite_sword", race_config=race
        )


def test_upgrade_all_models_unknown_unit_key_raises(
    one_unit_army: ArmyList, *, simple_race: RaceConfig
) -> None:
    with pytest.raises(KeyError):
        one_unit_army.upgrade_all_models(
            ("nonexistent", 0), equipment_name="sword", race_config=simple_race
        )


# ---------------------------------------------------------------------------
# duplicate_unit
# ---------------------------------------------------------------------------


def test_duplicate_unit_appends_copy(one_unit_army: ArmyList) -> None:
    army = one_unit_army.duplicate_unit(("squad", 0))
    assert len(army.units) == 2
    assert army.units[0].name == army.units[1].name
    assert army.units[0].models[0].name == army.units[1].models[0].name


def test_duplicate_unit_is_independent(
    one_unit_army: ArmyList, *, simple_race: RaceConfig
) -> None:
    army = one_unit_army.duplicate_unit(("squad", 0))
    upgraded = army.upgrade_unit(
        ("squad", 1),
        model_key=("soldier", 0),
        upgrade_model_name="elite_soldier",
        race_config=simple_race,
    )
    assert upgraded.units[0].models[0].name == "soldier"
    assert upgraded.units[1].models[0].name == "elite_soldier"


def test_duplicate_unit_drops_nicks(nicked_army: ArmyList) -> None:
    army = nicked_army.duplicate_unit(("squad", 0))
    assert army.units[1].nick is None
    assert army.units[1].models[0].nick is None
    # The original keeps both of its nicks.
    assert army.units[0].nick == "Da Lads"
    assert army.units[0].models[0].nick == "Grubnak"


def test_duplicate_unit_can_re_nick_in_one_call(nicked_army: ArmyList) -> None:
    army = nicked_army.duplicate_unit(("squad", 0), nick="Da Gals")
    assert army.units[1].nick == "Da Gals"
    # Only the unit is re-nicked; the copied model slots stay un-nicked.
    assert army.units[1].models[0].nick is None


def test_duplicate_unit_empty_nick_raises(nicked_army: ArmyList) -> None:
    with pytest.raises(ValueError, match="Nick cannot be empty"):
        nicked_army.duplicate_unit(("squad", 0), nick=" ")


def test_duplicate_unit_does_not_share_model_list(nicked_army: ArmyList) -> None:
    army = nicked_army.duplicate_unit(("squad", 0))
    assert army.units[0].models is not army.units[1].models


def test_duplicate_unit_unknown_unit_key_raises(one_unit_army: ArmyList) -> None:
    with pytest.raises(KeyError):
        one_unit_army.duplicate_unit(("nonexistent", 0))


# ---------------------------------------------------------------------------
# nick_unit / nick_model
# ---------------------------------------------------------------------------


def test_nick_unit_sets_nick(one_unit_army: ArmyList) -> None:
    army = one_unit_army.nick_unit(("squad", 0), nick="Da Lads")
    assert army.units[0].nick == "Da Lads"


def test_nick_unit_addresses_the_right_occurrence(one_unit_army: ArmyList) -> None:
    army = one_unit_army.duplicate_unit(("squad", 0)).nick_unit(
        ("squad", 1), nick="Da Lads"
    )
    assert army.units[0].nick is None
    assert army.units[1].nick == "Da Lads"


def test_nick_unit_does_not_mutate_original(one_unit_army: ArmyList) -> None:
    one_unit_army.nick_unit(("squad", 0), nick="Da Lads")
    assert one_unit_army.units[0].nick is None


def test_nick_unit_clears_with_none(one_unit_army: ArmyList) -> None:
    army = one_unit_army.nick_unit(("squad", 0), nick="Da Lads")
    assert army.nick_unit(("squad", 0), nick=None).units[0].nick is None


def test_nick_unit_empty_nick_raises(one_unit_army: ArmyList) -> None:
    with pytest.raises(ValueError, match="Nick cannot be empty"):
        one_unit_army.nick_unit(("squad", 0), nick="   ")


def test_nick_unit_unknown_unit_key_raises(one_unit_army: ArmyList) -> None:
    with pytest.raises(KeyError):
        one_unit_army.nick_unit(("nonexistent", 0), nick="Da Lads")


def test_nick_model_sets_nick(one_unit_army: ArmyList) -> None:
    army = one_unit_army.nick_model(
        ("squad", 0), model_key=("soldier", 0), nick="Grubnak"
    )
    assert army.units[0].models[0].nick == "Grubnak"
    assert army.units[0].nick is None


def test_nick_model_leaves_squadmates_alone(simple_race: RaceConfig) -> None:
    two_model_unit = ArmyUnit(
        name="squad",
        config=simple_race.units["squad"],
        models=[
            ArmyModel(name="soldier", config=simple_race.models["soldier"], upgrades=[])
            for _ in range(2)
        ],
    )
    army = ArmyList(race="goblin", nick="Test Army", units=[two_model_unit]).nick_model(
        ("squad", 0), model_key=("soldier", 1), nick="Grubnak"
    )
    assert [m.nick for m in army.units[0].models] == [None, "Grubnak"]


def test_nick_model_empty_nick_raises(one_unit_army: ArmyList) -> None:
    with pytest.raises(ValueError, match="Nick cannot be empty"):
        one_unit_army.nick_model(("squad", 0), model_key=("soldier", 0), nick="")


def test_nick_model_checks_the_nick_before_the_key(one_unit_army: ArmyList) -> None:
    # Same order as nick_unit, so a bad nick reports as a bad nick either way.
    with pytest.raises(ValueError, match="Nick cannot be empty"):
        one_unit_army.nick_model(("nonexistent", 0), model_key=("soldier", 0), nick=" ")


def test_nick_model_unknown_model_key_raises(one_unit_army: ArmyList) -> None:
    with pytest.raises(KeyError):
        one_unit_army.nick_model(
            ("squad", 0), model_key=("nonexistent", 0), nick="Grubnak"
        )


# ---------------------------------------------------------------------------
# Nick survives every upgrade path
#
# Every upgrade_* method rebuilds its dataclass, so each reconstruction site
# has to thread `nick` through or upgrading silently drops it. One test per
# method, deliberately.
# ---------------------------------------------------------------------------


@pytest.fixture
def nicked_army(simple_race: RaceConfig) -> ArmyList:
    """One nicked unit whose single model slot is nicked too."""
    return (
        ArmyList(race="goblin", nick="Test Army", units=[])
        .add_unit("squad", nick="Da Lads", race_config=simple_race)
        .nick_model(("squad", 0), model_key=("soldier", 0), nick="Grubnak")
    )


def test_upgrade_model_preserves_nicks(
    nicked_army: ArmyList, *, simple_race: RaceConfig
) -> None:
    army = nicked_army.upgrade_model(
        ("squad", 0),
        model_key=("soldier", 0),
        equipment_name="sword",
        race_config=simple_race,
    )
    assert army.units[0].nick == "Da Lads"
    assert army.units[0].models[0].nick == "Grubnak"


def test_upgrade_unit_preserves_nicks_across_promotion(
    nicked_army: ArmyList, *, simple_race: RaceConfig
) -> None:
    army = nicked_army.upgrade_unit(
        ("squad", 0),
        model_key=("soldier", 0),
        upgrade_model_name="elite_soldier",
        race_config=simple_race,
    )
    assert army.units[0].models[0].name == "elite_soldier"
    assert army.units[0].nick == "Da Lads"
    # A Nick belongs to the slot, not the model type.
    assert army.units[0].models[0].nick == "Grubnak"


def test_upgrade_full_unit_preserves_nicks(
    nicked_army: ArmyList, *, simple_race: RaceConfig
) -> None:
    army = nicked_army.upgrade_full_unit(
        ("squad", 0), upgrade_model_name="elite_soldier", race_config=simple_race
    )
    assert army.units[0].nick == "Da Lads"
    assert army.units[0].models[0].nick == "Grubnak"


def test_upgrade_all_models_preserves_nicks(
    nicked_army: ArmyList, *, simple_race: RaceConfig
) -> None:
    army = nicked_army.upgrade_all_models(
        ("squad", 0), equipment_name="sword", race_config=simple_race
    )
    assert army.units[0].nick == "Da Lads"
    assert army.units[0].models[0].nick == "Grubnak"


def test_delete_unit_leaves_other_nicks_intact(
    nicked_army: ArmyList, *, simple_race: RaceConfig
) -> None:
    army = nicked_army.add_unit("squad", race_config=simple_race).delete_unit(
        ("squad", 1)
    )
    assert [u.nick for u in army.units] == ["Da Lads"]


# ---------------------------------------------------------------------------
# delete_unit
# ---------------------------------------------------------------------------


def test_delete_unit_removes_unit(one_unit_army: ArmyList) -> None:
    army = one_unit_army.duplicate_unit(("squad", 0))
    assert len(army.units) == 2
    army = army.delete_unit(("squad", 1))
    assert len(army.units) == 1
    assert army.units[0].name == "squad"


def test_delete_unit_does_not_mutate_original(one_unit_army: ArmyList) -> None:
    original = one_unit_army
    one_unit_army.delete_unit(("squad", 0))
    assert len(original.units) == 1


def test_delete_unit_unknown_unit_key_raises(one_unit_army: ArmyList) -> None:
    with pytest.raises(KeyError):
        one_unit_army.delete_unit(("nonexistent", 0))


# ---------------------------------------------------------------------------
# available_models and available_equipment
# ---------------------------------------------------------------------------


def test_available_models_returns_matching(
    one_unit_army: ArmyList, *, simple_race: RaceConfig
) -> None:
    result = available_models(
        one_unit_army,
        unit_key=("squad", 0),
        model_key=("soldier", 0),
        race_config=simple_race,
    )
    assert len(result) == 1
    assert result[0] == "elite_soldier"


def test_available_models_empty_when_none_match(
    one_unit_army: ArmyList, *, simple_race: RaceConfig
) -> None:
    army = one_unit_army.upgrade_unit(
        ("squad", 0),
        model_key=("soldier", 0),
        upgrade_model_name="elite_soldier",
        race_config=simple_race,
    )
    result = available_models(
        army,
        unit_key=("squad", 0),
        model_key=("elite_soldier", 0),
        race_config=simple_race,
    )
    assert result == []


def test_available_equipment_excludes_no_cost(
    one_unit_army: ArmyList, *, simple_race: RaceConfig
) -> None:
    result = available_equipment(
        one_unit_army,
        unit_key=("squad", 0),
        model_key=("soldier", 0),
        race_config=simple_race,
    )
    assert "shield" not in result


def test_available_equipment_includes_valid(
    one_unit_army: ArmyList, *, simple_race: RaceConfig
) -> None:
    result = available_equipment(
        one_unit_army,
        unit_key=("squad", 0),
        model_key=("soldier", 0),
        race_config=simple_race,
    )
    assert "sword" in result


def test_available_equipment_goblin_infantry_clockwork_wings(
    goblin_army: ArmyList, *, goblin_race: RaceConfig
) -> None:
    result = available_equipment(
        goblin_army,
        unit_key=("goblin_infantry", 0),
        model_key=("goblin_infantry", 0),
        race_config=goblin_race,
    )
    assert "clockwork_wings" in result


def test_available_equipment_excludes_truly_insufficient_slots(
    goblin_army: ArmyList, *, goblin_race: RaceConfig
) -> None:
    # After consuming all Hands slots with one upgrade, a second Hands:2 upgrade
    # should no longer be available.
    army_with_upgrade = goblin_army.upgrade_model(
        ("goblin_infantry", 0),
        model_key=("goblin_infantry", 0),
        equipment_name="gear_bow",
        race_config=goblin_race,
    )
    result = available_equipment(
        army_with_upgrade,
        unit_key=("goblin_infantry", 0),
        model_key=("goblin_infantry", 0),
        race_config=goblin_race,
    )
    assert "gear_bow" not in result


def test_available_equipment_defaults_do_not_consume_slots(
    race_with_defaults: RaceConfig,
) -> None:
    # Defaults are replaced by upgrades, so a model with a Hands:2 default weapon
    # should still be able to receive a Hands:2 upgrade — the default is gone once
    # any upgrade is added.
    army = ArmyList(race="goblin", nick="T", units=[]).add_unit(
        "squad", race_config=race_with_defaults
    )
    # sword requires Hands:1 — the default_sword (Hands:2) must NOT consume slots here
    result = available_equipment(
        army,
        unit_key=("squad", 0),
        model_key=("soldier", 0),
        race_config=race_with_defaults,
    )
    assert "sword" in result


# ---------------------------------------------------------------------------
# validate_army
# ---------------------------------------------------------------------------


def test_validate_army_valid_returns_empty(
    one_unit_army: ArmyList, *, simple_race: RaceConfig
) -> None:
    assert validate_army(one_unit_army, race_config=simple_race) == []


def test_validate_army_detects_invalid_model_replacement(
    simple_race: RaceConfig,
) -> None:
    tweaked_unit_config = UnitConfig(
        race="goblin",
        name="Squad",
        models=["elite_soldier"],
        size="small",
        cost=t.Cost(mp=3),
        shaken=ShakenConfig(speed="slow", movement_order=["-", "-", "flee"]),
        orders=OrdersConfig(),
        armor=None,
        damage_tables={"Regular": {"rows": ["1: Fine", "2: Dead"]}},  # pyright: ignore[reportArgumentType]
    )
    illegal_unit = ArmyUnit(
        name="squad",
        config=tweaked_unit_config,
        models=[
            ArmyModel(
                name="soldier",
                config=simple_race.models["soldier"],
                upgrades=[],
            ),
        ],
    )
    army = ArmyList(race="goblin", nick="Test Army", units=[illegal_unit])
    errors = validate_army(army, race_config=simple_race)
    assert len(errors) >= 1
    assert any("cannot replace" in e for e in errors)


def test_validate_army_detects_multiple_violations(simple_race: RaceConfig) -> None:
    tweaked_unit_config = UnitConfig(
        race="goblin",
        name="Double Squad",
        models=["elite_soldier", "elite_soldier"],
        size="small",
        cost=t.Cost(mp=3),
        shaken=ShakenConfig(speed="slow", movement_order=["-", "-", "flee"]),
        orders=OrdersConfig(),
        armor=None,
        damage_tables={"Regular": {"rows": ["1: Fine", "2: Dead"]}},  # pyright: ignore[reportArgumentType]
    )
    illegal_unit = ArmyUnit(
        name="double_squad",
        config=tweaked_unit_config,
        models=[
            ArmyModel(
                name="soldier", config=simple_race.models["soldier"], upgrades=[]
            ),
            ArmyModel(
                name="soldier", config=simple_race.models["soldier"], upgrades=[]
            ),
        ],
    )
    army = ArmyList(race="goblin", nick="Test Army", units=[illegal_unit])
    errors = validate_army(army, race_config=simple_race)
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
        upgrades=[
            "elite_sword",
        ],
    )
    bad_unit = ArmyUnit(name="squad", config=race.units["squad"], models=[bad_model])
    army = ArmyList(race="goblin", nick="Test Army", units=[bad_unit])
    errors = validate_army(army, race_config=race)
    assert any("requires not satisfied" in e for e in errors)


def test_validate_army_upgrade_exactly_filling_slots_is_valid(
    simple_race: RaceConfig,
) -> None:
    # An upgrade that exactly fits remaining slots must not be flagged as invalid.
    # soldier has Hands:2; sword requires Hands:1; two swords exactly fill the slots.
    good_model = ArmyModel(
        name="soldier",
        config=simple_race.models["soldier"],
        upgrades=["sword", "sword"],
    )
    good_unit = ArmyUnit(
        name="squad", config=simple_race.units["squad"], models=[good_model]
    )
    army = ArmyList(race="goblin", nick="Test Army", units=[good_unit])
    errors = validate_army(army, race_config=simple_race)
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
        upgrades=[
            "two_hand_sword",
        ],
    )
    good_unit = ArmyUnit(name="squad", config=race.units["squad"], models=[good_model])
    army = ArmyList(race="goblin", nick="Test Army", units=[good_unit])
    errors = validate_army(army, race_config=race)
    assert errors == []


def test_validate_army_defaults_not_counted_for_slot_check(
    race_with_defaults: RaceConfig,
) -> None:
    # A model with a Hands:2 default and a Hands:1 upgrade must be valid —
    # the default is replaced by the upgrade and does not consume slots.
    good_model = ArmyModel(
        name="soldier",
        config=race_with_defaults.models["soldier"],
        upgrades=[
            "sword",
        ],
    )
    good_unit = ArmyUnit(
        name="squad", config=race_with_defaults.units["squad"], models=[good_model]
    )
    army = ArmyList(race="goblin", nick="Test Army", units=[good_unit])
    errors = validate_army(army, race_config=race_with_defaults)
    assert errors == []


def test_validate_army_still_catches_genuine_slot_overflow(
    simple_race: RaceConfig,
) -> None:
    # Three swords (each Hands:1) on a Hands:2 model must still fail.
    bad_model = ArmyModel(
        name="soldier",
        config=simple_race.models["soldier"],
        upgrades=["sword", "sword", "sword"],
    )
    bad_unit = ArmyUnit(
        name="squad", config=simple_race.units["squad"], models=[bad_model]
    )
    army = ArmyList(race="goblin", nick="Test Army", units=[bad_unit])
    errors = validate_army(army, race_config=simple_race)
    assert len(errors) == 1
    assert "Hands:1" in errors[0]


# ---------------------------------------------------------------------------
# Resolved Model.equipment — defaults yield holders to upgrades (ADR-0020)
# ---------------------------------------------------------------------------


def _race_with_default(simple_race: RaceConfig, default: EquipmentConfig) -> RaceConfig:
    """Give the soldier one default equipment entry, keyed `basic_sword`."""
    return RaceConfig(
        races=simple_race.races,
        units=simple_race.units,
        models={
            **simple_race.models,
            "soldier": simple_race.models["soldier"].model_copy(
                update={"equipment": ["basic_sword"]}
            ),
        },
        equipment={**simple_race.equipment, "basic_sword": default},
    )


def _soldier_with_sword(race: RaceConfig) -> Model:
    """Resolve a one-soldier army that has bought the Hands:1 `sword` upgrade."""
    army = (
        ArmyList(race="goblin", nick="T", units=[])
        .add_unit("squad", race_config=race)
        .upgrade_model(
            ("squad", 0),
            model_key=("soldier", 0),
            equipment_name="sword",
            race_config=race,
        )
    )
    return army.resolve(race).units[0].models[0]


def test_model_equipment_no_upgrades_returns_defaults(simple_race: RaceConfig) -> None:
    """With nothing bought, the model runs exactly its default loadout."""
    sword_free = EquipmentConfig(race="goblin", name="Basic Sword", requires=[])
    race = _race_with_default(simple_race, sword_free)
    army = ArmyList(race="goblin", nick="T", units=[]).add_unit(
        "squad", race_config=race
    )

    model = army.resolve(race).units[0].models[0]

    assert len(model.default_equipment) == 1
    assert model.upgrade_equipment == []
    assert model.equipment == model.default_equipment


def test_model_equipment_keeps_a_default_that_claims_no_holder(
    simple_race: RaceConfig,
) -> None:
    """A default with no `requires` occupies nothing, so no upgrade can evict it."""
    sword_free = EquipmentConfig(race="goblin", name="Basic Sword", requires=[])

    model = _soldier_with_sword(_race_with_default(simple_race, sword_free))

    assert [equip.name for equip in model.equipment] == ["Basic Sword", "Sword"]


def test_model_equipment_evicts_a_default_the_upgrade_crowds_out(
    simple_race: RaceConfig,
) -> None:
    """A Hands:2 default cannot fit beside a Hands:1 upgrade in a Hands:2 model."""
    two_handed = EquipmentConfig(
        race="goblin",
        name="Great Sword",
        requires=[["Hands:2"]],  # pyright: ignore[reportArgumentType]
    )

    model = _soldier_with_sword(_race_with_default(simple_race, two_handed))

    assert [equip.name for equip in model.equipment] == ["Sword"]


def test_model_equipment_keeps_a_default_in_an_untouched_holder(
    simple_race: RaceConfig,
) -> None:
    """The Abomination case: the upgrade takes Hands, the Grenades default stays."""
    grenade = EquipmentConfig(
        race="goblin",
        name="Grenade",
        requires=[["Grenades:1"]],  # pyright: ignore[reportArgumentType]
    )

    model = _soldier_with_sword(_race_with_default(simple_race, grenade))

    assert [equip.name for equip in model.equipment] == ["Grenade", "Sword"]


def test_model_equipment_orders_retained_defaults_before_upgrades(
    simple_race: RaceConfig,
) -> None:
    """Order is load-bearing for specials and Stackers: defaults, then upgrades."""
    banner = EquipmentConfig(race="goblin", name="Banner", requires=[])

    model = _soldier_with_sword(_race_with_default(simple_race, banner))

    assert model.equipment == [*model.default_equipment, *model.upgrade_equipment]


def test_model_specials_take_a_retained_default_before_the_upgrade(
    simple_race: RaceConfig,
) -> None:
    """Order is load-bearing: a retained default's instance precedes the upgrade's."""
    default = EquipmentConfig(
        race="goblin",
        name="Basic Sword",
        requires=[],
        model_specials={"to_hit": [SpecialInstance(text="from the default")]},
    )
    upgrade = EquipmentConfig(
        race="goblin",
        name="Magic Sword",
        cost=t.Cost(cp=5),
        upgrade_all=True,
        requires=[],
        model_specials={"to_hit": [SpecialInstance(text="from the upgrade")]},
    )
    model = Model(
        name="soldier",
        config=simple_race.models["soldier"],
        default_equipment=[default],
        upgrade_equipment=[upgrade],
    )

    assert [instance.text for instance in model.model_specials["to_hit"]] == [
        "from the default",
        "from the upgrade",
    ]


def test_assault_applies_a_retained_default_stacker_before_the_upgrade(
    simple_race: RaceConfig,
) -> None:
    """A retained default's Stacker is applied, and applied first.

    `add` then `replace` lands on the replaced value; the reverse order would
    end on 3, so this pins the sequence and not merely that both ran.
    """
    default = EquipmentConfig(
        race="goblin",
        name="Basic Sword",
        requires=[],
        assault=EquipmentAssaultConfig(strength=Stacker(add=[2, 0, 0, 0])),
    )
    upgrade = EquipmentConfig(
        race="goblin",
        name="Magic Sword",
        cost=t.Cost(cp=5),
        upgrade_all=True,
        requires=[],
        assault=EquipmentAssaultConfig(strength=Stacker(replace=[7, 0, 0, 0])),
    )
    model = Model(
        name="soldier",
        config=simple_race.models["soldier"],
        default_equipment=[default],
        upgrade_equipment=[upgrade],
    )

    assert model.assault().strength == [7, 0, 0, 0]


def test_retained_defaults_do_not_change_what_a_unit_costs(
    simple_race: RaceConfig,
) -> None:
    """Retained defaults are costless and stay costless -- army totals must not move."""
    banner = EquipmentConfig(race="goblin", name="Banner", requires=[])
    race = _race_with_default(simple_race, banner)
    plain = ArmyList(race="goblin", nick="T", units=[]).add_unit(
        "squad", race_config=race
    )
    upgraded = plain.upgrade_model(
        ("squad", 0),
        model_key=("soldier", 0),
        equipment_name="sword",
        race_config=race,
    )

    sword_cost = race.equipment["sword"].cost
    assert sword_cost is not None
    assert plain.resolve(race).units[0].cost() + sword_cost == (
        upgraded.resolve(race).units[0].cost()
    )


# ---------------------------------------------------------------------------
# Resolved Model.assault() Stacker application
# ---------------------------------------------------------------------------


def test_model_assault_no_equipment_returns_base(simple_race: RaceConfig) -> None:
    resolved = (
        ArmyList(race="goblin", nick="T", units=[])
        .add_unit("squad", race_config=simple_race)
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
        ArmyList(race="goblin", nick="T", units=[])
        .add_unit("squad", race_config=race)
        .upgrade_model(
            ("squad", 0),
            model_key=("soldier", 0),
            equipment_name="ap_ammo",
            race_config=race,
        )
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
        ArmyList(race="goblin", nick="T", units=[])
        .add_unit("squad", race_config=race)
        .upgrade_model(
            ("squad", 0),
            model_key=("soldier", 0),
            equipment_name="power_weapon",
            race_config=race,
        )
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
        ArmyList(race="goblin", nick="T", units=[])
        .add_unit("squad", race_config=race)
        .upgrade_model(
            ("squad", 0),
            model_key=("soldier", 0),
            equipment_name="big_weapon",
            race_config=race,
        )
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
        ArmyList(race="goblin", nick="T", units=[])
        .add_unit("squad", race_config=race)
        .upgrade_model(
            ("squad", 0),
            model_key=("soldier", 0),
            equipment_name="bad_weapon",
            race_config=race,
        )
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
        ArmyList(race="goblin", nick="T", units=[])
        .add_unit("squad", race_config=race)
        .upgrade_model(
            ("squad", 0),
            model_key=("soldier", 0),
            equipment_name="ap_boost",
            race_config=race,
        )
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
        size="small",
        cost=None,
        shaken=ShakenConfig(speed="slow", movement_order=["-", "-", "flee"]),
        orders=OrdersConfig(),
        armor=None,
        damage_tables={"Regular": {"rows": ["1: Fine", "2: Dead"]}},  # pyright: ignore[reportArgumentType]
    )
    race = RaceConfig(
        races=simple_race.races,
        units={"two_squad": unit_cfg},
        models=simple_race.models,
        equipment={**simple_race.equipment, "per_model_gear": per_model_equip},
    )
    army = (
        ArmyList(race="goblin", nick="T", units=[])
        .add_unit("two_squad", race_config=race)
        .upgrade_model(
            ("two_squad", 0),
            model_key=("soldier", 0),
            equipment_name="per_model_gear",
            race_config=race,
        )
        .upgrade_model(
            ("two_squad", 0),
            model_key=("soldier", 1),
            equipment_name="per_model_gear",
            race_config=race,
        )
    )
    resolved = army.resolve(race)
    # cost = 1cp * 2 models = 2cp
    assert resolved.units[0].cost() == t.Cost(cp=2)


def test_unit_cost_upgrade_all_true_flat(simple_race: RaceConfig) -> None:
    unit_cfg = UnitConfig(
        race="goblin",
        name="Two Squad",
        models=["soldier", "soldier"],
        size="small",
        cost=None,
        shaken=ShakenConfig(speed="slow", movement_order=["-", "-", "flee"]),
        orders=OrdersConfig(),
        armor=None,
        damage_tables={"Regular": {"rows": ["1: Fine", "2: Dead"]}},  # pyright: ignore[reportArgumentType]
    )
    race = RaceConfig(
        races=simple_race.races,
        units={"two_squad": unit_cfg},
        models=simple_race.models,
        equipment=simple_race.equipment,
    )
    army = (
        ArmyList(race="goblin", nick="T", units=[])
        .add_unit("two_squad", race_config=race)
        .upgrade_model(
            ("two_squad", 0),
            model_key=("soldier", 0),
            equipment_name="sword",
            race_config=race,
        )
    )
    resolved = army.resolve(race)
    # sword upgrade_all=True, cost=cp=2 → flat, regardless of 2 models
    assert resolved.units[0].cost() == t.Cost(cp=2)


# ---------------------------------------------------------------------------
# ArmyList.resolve() structure preservation
# ---------------------------------------------------------------------------


def test_resolve_preserves_unit_count(simple_race: RaceConfig) -> None:
    army = (
        ArmyList(race="goblin", nick="T", units=[])
        .add_unit("squad", race_config=simple_race)
        .add_unit("squad", race_config=simple_race)
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
        ArmyList(race="goblin", nick="T", units=[])
        .add_unit("squad", race_config=race)
        .resolve(race)
    )
    model = resolved.units[0].models[0]
    assert len(model.default_equipment) == 1
    assert model.default_equipment[0].name == "Basic Sword"


def test_resolve_populates_upgrade_equipment(
    one_unit_army: ArmyList, *, simple_race: RaceConfig
) -> None:
    army = one_unit_army.upgrade_model(
        ("squad", 0),
        model_key=("soldier", 0),
        equipment_name="sword",
        race_config=simple_race,
    )
    resolved = army.resolve(simple_race)
    model = resolved.units[0].models[0]
    assert len(model.upgrade_equipment) == 1
    assert model.upgrade_equipment[0].name == "Sword"


# ---------------------------------------------------------------------------
# display_name on the resolved tier
# ---------------------------------------------------------------------------


def test_resolve_carries_nicks_across(
    nicked_army: ArmyList, *, simple_race: RaceConfig
) -> None:
    resolved = nicked_army.resolve(simple_race)
    assert resolved.units[0].nick == "Da Lads"
    assert resolved.units[0].models[0].nick == "Grubnak"


def test_display_name_falls_back_to_catalogue_name(
    one_unit_army: ArmyList, *, simple_race: RaceConfig
) -> None:
    unit = one_unit_army.resolve(simple_race).units[0]
    assert unit.display_name == "Squad"
    assert unit.models[0].display_name == "Soldier"


def test_display_name_uses_the_nick(
    nicked_army: ArmyList, *, simple_race: RaceConfig
) -> None:
    unit = nicked_army.resolve(simple_race).units[0]
    assert unit.display_name == "Da Lads"
    assert unit.models[0].display_name == "Grubnak"


# ---------------------------------------------------------------------------
# Unit.common_types
# ---------------------------------------------------------------------------


def _typed_model(*types: t.ModelType, name: str = "Trooper") -> Model:
    """Build a resolved Model whose only interesting property is its type list."""
    return Model(
        name=name.lower().replace(" ", "_"),
        config=ModelConfig(
            race="goblin",
            name=name,  # pyright: ignore[reportArgumentType]
            equipment_limit=[],  # pyright: ignore[reportArgumentType]
            equipment=[],
            type=list(types),
            assault=_ASSAULT,
            cost=None,
        ),
        default_equipment=[],
        upgrade_equipment=[],
    )


def _typed_unit(*models: Model, race: RaceConfig) -> Unit:
    return Unit(name="squad", config=race.units["squad"], models=list(models))


def test_common_types_identical_models(simple_race: RaceConfig) -> None:
    unit = _typed_unit(
        _typed_model("Bio", "Infantry", "Walking"),
        _typed_model("Bio", "Infantry", "Walking"),
        race=simple_race,
    )
    assert unit.common_types == ["Bio", "Infantry", "Walking"]


def test_common_types_partial_overlap_drops_the_extra(simple_race: RaceConfig) -> None:
    unit = _typed_unit(
        _typed_model("Bio", "Infantry", "Walking"),
        _typed_model("Bio", "Infantry", "Walking", "Elite", name="Elite Trooper"),
        race=simple_race,
    )
    assert unit.common_types == ["Bio", "Infantry", "Walking"]


def test_common_types_uses_canonical_order_not_declaration_order(
    simple_race: RaceConfig,
) -> None:
    # Mechanical/Infantry/Cavalry are canonically in that order, which is
    # neither the declaration order below nor alphabetical order — so this
    # pins the ModelType literal as the sort key and nothing else.
    unit = _typed_unit(
        _typed_model("Cavalry", "Infantry", "Mechanical", name="Rider"),
        _typed_model("Infantry", "Mechanical", "Cavalry", name="Other Rider"),
        race=simple_race,
    )
    assert unit.common_types == ["Mechanical", "Infantry", "Cavalry"]


def test_common_types_zero_overlap_is_empty(simple_race: RaceConfig) -> None:
    unit = _typed_unit(
        _typed_model("Vehicle", "Mechanical", "Bio Crew", "Tracked", name="Wagon"),
        _typed_model("Bio", "Infantry", "Walking"),
        race=simple_race,
    )
    assert unit.common_types == []


def test_common_types_of_a_unit_with_no_models_is_empty(
    simple_race: RaceConfig,
) -> None:
    assert _typed_unit(race=simple_race).common_types == []
