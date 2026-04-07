"""Tests for spf.teams module."""

import pytest

from spf.armies import get_army
from spf.schemas.army import (
    ArmyConfig,
    AssaultConfig,
    EquipmentConfig,
    ModelConfig,
    OrdersConfig,
    RaceConfig,
    UnitConfig,
)
from spf.schemas.type_aliases import Cost
from spf.teams import (
    Team,
    TeamModel,
    TeamUnit,
    _add_cost,
    _satisfies_requires,
    add_unit,
    available_equipment,
    available_models,
    total_cost,
    upgrade_model,
    upgrade_unit,
    validate_team,
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
def simple_army() -> ArmyConfig:
    """Minimal ArmyConfig with one unit, two model types, and two equipment items."""
    return ArmyConfig(
        races={"goblin": RaceConfig(name="Goblin")},
        units={
            "squad": UnitConfig(
                race="goblin",
                name="Squad",
                models=["soldier"],
                size="Small",
                cost=Cost(mp=3),
                shaken="Shaken",
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
                equipment_limit=["Hands:2", "Grenades:1"],
                equipments=[],
                type=["Infantry"],
                assault=_ASSAULT,
                cost=None,
            ),
            "elite_soldier": ModelConfig(
                race="goblin",
                name="Elite Soldier",
                equipment_limit=["Hands:2"],
                equipments=[],
                type=["Infantry", "Elite"],
                assault=_ASSAULT,
                cost=Cost(xp=1),
                replaces=["soldier"],
            ),
        },
        equipments={
            "sword": EquipmentConfig(
                race="goblin",
                name="Sword",
                cost=Cost(cp=2),
                requires=[["Hands:1"], ["type:Infantry"]],
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
def empty_team(simple_army: ArmyConfig) -> Team:
    return Team(army="goblin", units=())


@pytest.fixture
def one_unit_team(simple_army: ArmyConfig) -> Team:
    return add_unit(Team(army="goblin", units=()), "squad", simple_army)


@pytest.fixture
def goblin_army() -> ArmyConfig:
    return get_army("goblin")


@pytest.fixture
def goblin_team(goblin_army: ArmyConfig) -> Team:
    return add_unit(Team(army="goblin", units=()), "goblin_infantry", goblin_army)


# ---------------------------------------------------------------------------
# 7.1 Data structure construction
# ---------------------------------------------------------------------------


def test_team_model_default_upgrades(simple_army: ArmyConfig) -> None:
    model = TeamModel(
        name="soldier", config=simple_army.models["soldier"], upgrades=()
    )
    assert model.upgrades == ()


def test_team_model_is_frozen(simple_army: ArmyConfig) -> None:
    model = TeamModel(
        name="soldier", config=simple_army.models["soldier"], upgrades=()
    )
    with pytest.raises((AttributeError, TypeError)):
        model.upgrades = ("sword",)  # type: ignore[misc]


def test_team_unit_default_models_match_config(
    one_unit_team: Team, simple_army: ArmyConfig
) -> None:
    unit = one_unit_team.units[0]
    assert tuple(m.name for m in unit.models) == tuple(unit.config.models)


def test_team_is_frozen(empty_team: Team) -> None:
    with pytest.raises((AttributeError, TypeError)):
        empty_team.units = ()  # type: ignore[misc]


def test_team_allows_duplicate_unit_types(simple_army: ArmyConfig) -> None:
    team = Team(army="goblin", units=())
    team = add_unit(team, "squad", simple_army)
    team = add_unit(team, "squad", simple_army)
    assert len(team.units) == 2
    assert all(u.name == "squad" for u in team.units)


# ---------------------------------------------------------------------------
# 7.2 Cost helpers
# ---------------------------------------------------------------------------


def test_add_cost_with_none_is_identity() -> None:
    base = Cost(mp=1, cp=2, xp=3, ip=4)
    assert _add_cost(base, None) == base


def test_add_cost_sums_fields() -> None:
    a = Cost(mp=1, cp=2, xp=3, ip=4)
    b = Cost(mp=10, cp=20, xp=30, ip=40)
    result = _add_cost(a, b)
    assert result == Cost(mp=11, cp=22, xp=33, ip=44)


def test_total_cost_empty_team(simple_army: ArmyConfig) -> None:
    team = Team(army="goblin", units=())
    assert total_cost(team, simple_army) == Cost()


def test_total_cost_includes_unit_base_cost(
    one_unit_team: Team, simple_army: ArmyConfig
) -> None:
    # squad costs mp=3
    assert total_cost(one_unit_team, simple_army) == Cost(mp=3)


def test_total_cost_includes_upgrade_model_cost(
    one_unit_team: Team, simple_army: ArmyConfig
) -> None:
    team = upgrade_unit(one_unit_team, ("squad", 0), ("soldier", 0), "elite_soldier", simple_army)
    # squad(mp=3) + elite_soldier(xp=1)
    assert total_cost(team, simple_army) == Cost(mp=3, xp=1)


def test_total_cost_includes_upgrade_equipment_cost(
    one_unit_team: Team, simple_army: ArmyConfig
) -> None:
    team = upgrade_model(one_unit_team, ("squad", 0), ("soldier", 0), "sword", simple_army)
    # squad(mp=3) + sword(cp=2)
    assert total_cost(team, simple_army) == Cost(mp=3, cp=2)


# ---------------------------------------------------------------------------
# 7.3 Requires logic
# ---------------------------------------------------------------------------


def test_satisfies_requires_type_match(simple_army: ArmyConfig) -> None:
    soldier = TeamModel(
        name="soldier", config=simple_army.models["soldier"], upgrades=()
    )
    # sword requires [type:Infantry] among others; soldier is Infantry
    assert _satisfies_requires(
        simple_army.equipments["sword"].requires, soldier, simple_army
    )


def test_satisfies_requires_type_mismatch(simple_army: ArmyConfig) -> None:
    # Temporarily test: a requires list that demands a type the model doesn't have
    from spf.schemas.type_aliases import Requirement

    req = [[Requirement(key="type", value="Cavalry")]]
    soldier = TeamModel(
        name="soldier", config=simple_army.models["soldier"], upgrades=()
    )
    assert not _satisfies_requires(req, soldier, simple_army)


def test_satisfies_requires_holder_sufficient(simple_army: ArmyConfig) -> None:
    from spf.schemas.type_aliases import Requirement

    # soldier has Hands:2; require Hands:1 should pass
    req = [[Requirement(key="Hands", value=1)]]
    soldier = TeamModel(
        name="soldier", config=simple_army.models["soldier"], upgrades=()
    )
    assert _satisfies_requires(req, soldier, simple_army)


def test_satisfies_requires_holder_insufficient(simple_army: ArmyConfig) -> None:
    from spf.schemas.type_aliases import Requirement

    # soldier has Hands:2; require Hands:3 should fail
    req = [[Requirement(key="Hands", value=3)]]
    soldier = TeamModel(
        name="soldier", config=simple_army.models["soldier"], upgrades=()
    )
    assert not _satisfies_requires(req, soldier, simple_army)


def test_satisfies_requires_cnf_all_groups_needed(simple_army: ArmyConfig) -> None:
    from spf.schemas.type_aliases import Requirement

    # CNF: [Hands:1] AND [type:Cavalry] — soldier is not Cavalry → False
    req = [
        [Requirement(key="Hands", value=1)],
        [Requirement(key="type", value="Cavalry")],
    ]
    soldier = TeamModel(
        name="soldier", config=simple_army.models["soldier"], upgrades=()
    )
    assert not _satisfies_requires(req, soldier, simple_army)


# ---------------------------------------------------------------------------
# 7.4 add_unit
# ---------------------------------------------------------------------------


def test_add_unit_appends_to_team(simple_army: ArmyConfig) -> None:
    team = Team(army="goblin", units=())
    team = add_unit(team, "squad", simple_army)
    assert len(team.units) == 1
    assert team.units[0].name == "squad"


def test_add_unit_default_models_match_config(simple_army: ArmyConfig) -> None:
    team = add_unit(Team(army="goblin", units=()), "squad", simple_army)
    unit = team.units[0]
    assert tuple(m.name for m in unit.models) == tuple(unit.config.models)


def test_add_unit_unknown_name_raises(simple_army: ArmyConfig) -> None:
    with pytest.raises(ValueError, match="Unknown unit"):
        add_unit(Team(army="goblin", units=()), "does_not_exist", simple_army)


# ---------------------------------------------------------------------------
# 7.5 upgrade_unit
# ---------------------------------------------------------------------------


def test_upgrade_unit_valid_replacement(
    one_unit_team: Team, simple_army: ArmyConfig
) -> None:
    team = upgrade_unit(
        one_unit_team, ("squad", 0), ("soldier", 0), "elite_soldier", simple_army
    )
    assert team.units[0].models[0].name == "elite_soldier"


def test_upgrade_unit_does_not_mutate_original(
    one_unit_team: Team, simple_army: ArmyConfig
) -> None:
    upgrade_unit(one_unit_team, ("squad", 0), ("soldier", 0), "elite_soldier", simple_army)
    assert one_unit_team.units[0].models[0].name == "soldier"


def test_upgrade_unit_invalid_replaces_raises(
    one_unit_team: Team, simple_army: ArmyConfig
) -> None:
    # soldier does not have replaces set; cannot replace elite_soldier with soldier
    with pytest.raises(ValueError, match="cannot replace"):
        upgrade_unit(
            one_unit_team, ("squad", 0), ("soldier", 0), "soldier", simple_army
        )


def test_upgrade_unit_unknown_unit_key_raises(
    one_unit_team: Team, simple_army: ArmyConfig
) -> None:
    with pytest.raises(KeyError):
        upgrade_unit(
            one_unit_team, ("nonexistent", 0), ("soldier", 0), "elite_soldier", simple_army
        )


def test_upgrade_unit_unknown_model_key_raises(
    one_unit_team: Team, simple_army: ArmyConfig
) -> None:
    with pytest.raises(KeyError):
        upgrade_unit(
            one_unit_team, ("squad", 0), ("nonexistent", 0), "elite_soldier", simple_army
        )


# ---------------------------------------------------------------------------
# 7.6 upgrade_model
# ---------------------------------------------------------------------------


def test_upgrade_model_adds_to_upgrades(
    one_unit_team: Team, simple_army: ArmyConfig
) -> None:
    team = upgrade_model(one_unit_team, ("squad", 0), ("soldier", 0), "sword", simple_army)
    assert "sword" in team.units[0].models[0].upgrades


def test_upgrade_model_does_not_mutate_original(
    one_unit_team: Team, simple_army: ArmyConfig
) -> None:
    upgrade_model(one_unit_team, ("squad", 0), ("soldier", 0), "sword", simple_army)
    assert one_unit_team.units[0].models[0].upgrades == ()


def test_upgrade_model_no_cost_raises(
    one_unit_team: Team, simple_army: ArmyConfig
) -> None:
    with pytest.raises(ValueError, match="no cost"):
        upgrade_model(one_unit_team, ("squad", 0), ("soldier", 0), "shield", simple_army)


def test_upgrade_model_unsatisfied_requires_raises(simple_army: ArmyConfig) -> None:
    # Add a unit with an Elite-only model to test requires failure
    from spf.schemas.type_aliases import Requirement

    elite_only_equip = EquipmentConfig(
        race="goblin",
        name="Elite Sword",
        cost=Cost(cp=3),
        requires=[["type:Elite"]],  # requires Elite type, soldier is not Elite
    )
    army = ArmyConfig(
        races=simple_army.races,
        units=simple_army.units,
        models=simple_army.models,
        equipments={**simple_army.equipments, "elite_sword": elite_only_equip},
    )
    team = add_unit(Team(army="goblin", units=()), "squad", army)
    with pytest.raises(ValueError, match="requires are not satisfied"):
        upgrade_model(team, ("squad", 0), ("soldier", 0), "elite_sword", army)


def test_upgrade_model_unknown_key_raises(
    one_unit_team: Team, simple_army: ArmyConfig
) -> None:
    with pytest.raises(KeyError):
        upgrade_model(
            one_unit_team, ("nonexistent", 0), ("soldier", 0), "sword", simple_army
        )


# ---------------------------------------------------------------------------
# 7.7 available_models and available_equipment
# ---------------------------------------------------------------------------


def test_available_models_returns_matching(
    one_unit_team: Team, simple_army: ArmyConfig
) -> None:
    # elite_soldier.replaces = ["soldier"]
    result = available_models(one_unit_team, ("squad", 0), ("soldier", 0), simple_army)
    assert len(result) == 1
    assert result[0].name == "Elite Soldier"


def test_available_models_empty_when_none_match(
    one_unit_team: Team, simple_army: ArmyConfig
) -> None:
    # upgrade to elite_soldier; nothing replaces it
    team = upgrade_unit(
        one_unit_team, ("squad", 0), ("soldier", 0), "elite_soldier", simple_army
    )
    result = available_models(team, ("squad", 0), ("elite_soldier", 0), simple_army)
    assert result == []


def test_available_equipment_excludes_no_cost(
    one_unit_team: Team, simple_army: ArmyConfig
) -> None:
    result = available_equipment(one_unit_team, ("squad", 0), ("soldier", 0), simple_army)
    names = [e.name for e in result]
    assert "Shield" not in names  # shield has no cost


def test_available_equipment_includes_valid(
    one_unit_team: Team, simple_army: ArmyConfig
) -> None:
    result = available_equipment(one_unit_team, ("squad", 0), ("soldier", 0), simple_army)
    names = [e.name for e in result]
    assert "Sword" in names  # cost + Infantry + Hands:1 available


def test_available_equipment_goblin_infantry_clockwork_wings(
    goblin_team: Team, goblin_army: ArmyConfig
) -> None:
    # goblin_infantry model has default goblin_bow (uses Hands:2), so no more Hands.
    # clockwork_wings requires type:Infantry + Independent:1 (999 available) → valid.
    result = available_equipment(
        goblin_team, ("goblin_infantry", 0), ("goblin_infantry", 0), goblin_army
    )
    names = [e.name for e in result]
    assert "Clockwork Wings" in names


def test_available_equipment_excludes_insufficient_slots(
    goblin_team: Team, goblin_army: ArmyConfig
) -> None:
    # goblin_bow already uses all Hands:2; gear_bow also needs Hands:2 → not available
    result = available_equipment(
        goblin_team, ("goblin_infantry", 0), ("goblin_infantry", 0), goblin_army
    )
    names = [e.name for e in result]
    assert "Gear bow" not in names


# ---------------------------------------------------------------------------
# 7.8 validate_team
# ---------------------------------------------------------------------------


def test_validate_team_valid_returns_empty(
    one_unit_team: Team, simple_army: ArmyConfig
) -> None:
    assert validate_team(one_unit_team, simple_army) == []


def test_validate_team_detects_invalid_model_replacement(
    one_unit_team: Team, simple_army: ArmyConfig
) -> None:
    # Manually construct an illegal replacement (soldier replacing itself — no replaces)
    bad_model = TeamModel(
        name="soldier",
        config=simple_army.models["soldier"],
        upgrades=(),
    )
    bad_unit = TeamUnit(
        name="squad",
        config=simple_army.units["squad"],
        # default is ["soldier"], but we put soldier at position 0 as if it replaced itself
        # To trigger the violation: put elite_soldier in position but with soldier's config
        models=(
            TeamModel(
                name="elite_soldier",
                config=simple_army.models["elite_soldier"],
                upgrades=(),
            ),
        ),
    )
    # Swap in a model whose replaces does NOT include "soldier" by using a hacked unit
    # where default should be "soldier" but team has elite_soldier — which IS valid.
    # For an actual violation: put soldier config but change config.replaces to be None
    # via a model that has no replaces field and a different name.
    # Simplest: make unit config say default is "elite_soldier" but team has "soldier".
    from spf.schemas.army import UnitConfig

    tweaked_unit_config = UnitConfig(
        race="goblin",
        name="Squad",
        models=["elite_soldier"],  # default is elite_soldier
        size="Small",
        cost=Cost(mp=3),
        shaken="Shaken",
        special={},
        orders=OrdersConfig(),
        armor=None,
        damage_tables={"regular": ["Fine", "Dead"]},
    )
    illegal_unit = TeamUnit(
        name="squad",
        config=tweaked_unit_config,
        models=(
            TeamModel(
                name="soldier",  # soldier is at position 0, but default is elite_soldier
                config=simple_army.models["soldier"],
                upgrades=(),
            ),
        ),
    )
    team = Team(army="goblin", units=(illegal_unit,))
    errors = validate_team(team, simple_army)
    assert len(errors) >= 1
    assert any("cannot replace" in e for e in errors)


def test_validate_team_detects_multiple_violations(simple_army: ArmyConfig) -> None:
    # Two models each with an illegal replacement
    tweaked_unit_config = UnitConfig(
        race="goblin",
        name="Double Squad",
        models=["elite_soldier", "elite_soldier"],
        size="Small",
        cost=Cost(mp=3),
        shaken="Shaken",
        special={},
        orders=OrdersConfig(),
        armor=None,
        damage_tables={"regular": ["Fine", "Dead"]},
    )
    illegal_unit = TeamUnit(
        name="double_squad",
        config=tweaked_unit_config,
        models=(
            TeamModel(name="soldier", config=simple_army.models["soldier"], upgrades=()),
            TeamModel(name="soldier", config=simple_army.models["soldier"], upgrades=()),
        ),
    )
    team = Team(army="goblin", units=(illegal_unit,))
    errors = validate_team(team, simple_army)
    assert len(errors) == 2


def test_validate_team_detects_unsatisfied_equipment_requires(
    simple_army: ArmyConfig,
) -> None:
    elite_only_equip = EquipmentConfig(
        race="goblin",
        name="Elite Sword",
        cost=Cost(cp=3),
        requires=[["type:Elite"]],
    )
    army = ArmyConfig(
        races=simple_army.races,
        units=simple_army.units,
        models=simple_army.models,
        equipments={**simple_army.equipments, "elite_sword": elite_only_equip},
    )
    # Manually put elite_sword on a non-Elite soldier
    bad_model = TeamModel(
        name="soldier",
        config=army.models["soldier"],
        upgrades=("elite_sword",),
    )
    bad_unit = TeamUnit(
        name="squad", config=army.units["squad"], models=(bad_model,)
    )
    team = Team(army="goblin", units=(bad_unit,))
    errors = validate_team(team, army)
    assert any("requires are not satisfied" in e for e in errors)
