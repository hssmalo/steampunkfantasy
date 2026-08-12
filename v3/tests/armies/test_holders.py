"""Tests for holder arithmetic: what equipment claims, and which defaults survive.

These mostly build small `EquipmentConfig`/`ModelConfig` values rather than
loading a Race: the arithmetic only reads `requires` and `equipment_limit`, so a
real Race would add noise without adding coverage. The one exception reads every
race, because it pins an assumption about the shipped data itself.
"""

from spf.armies import holders
from spf.races import get_race
from spf.schemas import type_aliases as t
from spf.schemas.race import AssaultConfig, EquipmentConfig, ModelConfig

_ASSAULT = AssaultConfig(
    strength=[1, 0, 0, 0],
    strength_die="4+",
    deflection=[1, 0, 0, 0],
    deflection_die="4+",
    damage="d4",
    ap=0,
)


def equipment(name: str, *, requires: list[list[str]] | None = None) -> EquipmentConfig:
    """Build an equipment entry carrying only a name and its holder claims."""
    return EquipmentConfig(
        race="goblin",
        name=name,  # pyright: ignore[reportArgumentType]
        requires=requires or [],  # pyright: ignore[reportArgumentType]
    )


def model(*, limits: list[str], equipment_keys: list[str] | None = None) -> ModelConfig:
    """Build a model config carrying only its holder limits and default keys."""
    return ModelConfig(
        race="goblin",
        name="Soldier",  # pyright: ignore[reportArgumentType]
        equipment_limit=limits,  # pyright: ignore[reportArgumentType]
        equipment=equipment_keys or [],
        type=["Infantry"],
        assault=_ASSAULT,
    )


# ---------------------------------------------------------------------------
# What equipment claims
# ---------------------------------------------------------------------------


def test_equipment_without_requires_claims_nothing() -> None:
    """No requires means no holder is touched -- such equipment is never evicted."""
    assert holders.claims(equipment("Banner")) == {}


def test_claims_reads_the_holder_and_its_count() -> None:
    """A single holder requirement is reported as holder to count."""
    assert holders.claims(equipment("Rifle", requires=[["Hands:2"]])) == {"Hands": 2}


def test_claims_ignores_type_requirements() -> None:
    """`type:` constrains who may take the equipment, not where it sits."""
    mortar = equipment("Mortar", requires=[["Tentacles:2"], ["type:Infantry"]])

    assert holders.claims(mortar) == {"Tentacles": 2}


def test_no_or_group_in_the_real_data_mixes_two_holders() -> None:
    """Pin the data assumption that lets `claims` sum every item in every group.

    `claims` sums both sides of an OR-group. That is only unambiguous while no
    group offers a choice *between* holders -- a `Hands:1 or Tentacles:1` group
    would be counted as claiming both. No such group exists in any race today.
    If this test ever fails, `claims` needs a real answer for OR, not a wider
    sum.
    """
    mixed = [
        (race, key, group)
        for race in t.RaceName.__value__.__args__
        for key, equip in get_race(race).equipment.items()
        for group in equip.requires
        if len({req.key for req in group if req.key != "type"}) > 1
    ]

    assert mixed == []


def test_claims_sums_repeated_holders() -> None:
    """Claims on the same holder across groups add up."""
    rig = equipment("Rig", requires=[["Hands:1"], ["Hands:1"], ["Grenades:2"]])

    assert holders.claims(rig) == {"Hands": 2, "Grenades": 2}


# ---------------------------------------------------------------------------
# What a model offers
# ---------------------------------------------------------------------------


def test_capacity_reports_declared_limits() -> None:
    """Capacity is exactly what the model declares -- no more, no less."""
    assert holders.capacity(model(limits=["Hands:2", "Grenades:1"])) == {
        "Hands": 2,
        "Grenades": 1,
    }


def test_capacity_omits_undeclared_holders() -> None:
    """A holder the model never declares has no capacity at all."""
    assert "Reserve Melee" not in holders.capacity(model(limits=["Hands:2"]))


def test_infinite_limit_becomes_a_large_number() -> None:
    """`Independent:∞` parses to a number big enough to never bind."""
    assert holders.capacity(model(limits=["Independent:∞"]))["Independent"] >= 999


# ---------------------------------------------------------------------------
# Which defaults survive
# ---------------------------------------------------------------------------


def test_default_survives_an_upgrade_in_a_different_holder() -> None:
    """The Abomination Infantry case: a Hands gun outlives a Tentacles mortar."""
    config = model(limits=["Independent:∞", "Hands:2", "Tentacles:4"])
    gun = equipment("Multipurpose Gun", requires=[["Hands:2"]])
    mortar = equipment("Fog Grenade Mortar", requires=[["Tentacles:4"]])

    assert holders.retained_defaults(config, defaults=[gun], upgrades=[mortar]) == [gun]


def test_default_is_evicted_by_an_upgrade_in_the_same_holder() -> None:
    """The Dark Elf Infantry case: the crossbow takes the hands the rifle needs."""
    config = model(limits=["Hands:2"])
    rifle = equipment("Rifle", requires=[["Hands:2"]])
    crossbow = equipment("Crossbow", requires=[["Hands:2"]])

    assert (
        holders.retained_defaults(config, defaults=[rifle], upgrades=[crossbow]) == []
    )


def test_every_default_is_kept_when_nothing_is_upgraded() -> None:
    """With no upgrades bought, a well-formed model keeps its whole loadout."""
    config = model(limits=["Hands:2", "Grenades:1"])
    rifle = equipment("Rifle", requires=[["Hands:2"]])
    grenade = equipment("Grenade", requires=[["Grenades:1"]])

    assert holders.retained_defaults(
        config, defaults=[rifle, grenade], upgrades=[]
    ) == [rifle, grenade]


def test_a_default_claiming_no_holder_is_never_evicted() -> None:
    """Nothing can take a holder it does not occupy, so it survives any upgrade."""
    config = model(limits=["Hands:2"])
    main_gun = equipment("Main Gun")
    crossbow = equipment("Crossbow", requires=[["Hands:2"]])

    assert holders.retained_defaults(
        config, defaults=[main_gun], upgrades=[crossbow]
    ) == [main_gun]


def test_eviction_follows_declaration_order() -> None:
    """Under pressure the first-declared default is kept and the later one drops."""
    config = model(limits=["Hands:2"])
    first = equipment("First Knife", requires=[["Hands:1"]])
    second = equipment("Second Knife", requires=[["Hands:1"]])
    pistol = equipment("Pistol", requires=[["Hands:1"]])

    assert holders.retained_defaults(
        config, defaults=[first, second], upgrades=[pistol]
    ) == [first]


def test_an_unlimited_holder_evicts_nothing() -> None:
    """`Independent:∞` has room for every claim, so no default yields to it."""
    config = model(limits=["Independent:∞"])
    banner = equipment("Banner", requires=[["Independent:1"]])
    horn = equipment("War Horn", requires=[["Independent:1"]])

    assert holders.retained_defaults(config, defaults=[banner], upgrades=[horn]) == [
        banner
    ]


def test_defaults_that_over_claim_their_own_limits_are_dropped() -> None:
    """Over-claiming data costs the model its weapon -- deliberately, with no upgrades.

    Tolerating the overdraft was considered and ruled out (ADR-0020): the lint
    rule `default-equipment-limit` catches this data defect instead. Do not add
    a `max()` or baseline to make this test pass differently.
    """
    config = model(limits=["Hands:2"])
    sword = equipment("Sword", requires=[["Reserve Melee:1"]])

    assert holders.retained_defaults(config, defaults=[sword], upgrades=[]) == []


def test_upgrades_are_never_evicted_even_when_they_over_claim() -> None:
    """Upgrades consume capacity unconditionally; only defaults yield."""
    config = model(limits=["Hands:2"])
    knife = equipment("Knife", requires=[["Hands:1"]])
    first = equipment("First Rifle", requires=[["Hands:2"]])
    second = equipment("Second Rifle", requires=[["Hands:2"]])

    assert (
        holders.retained_defaults(config, defaults=[knife], upgrades=[first, second])
        == []
    )
