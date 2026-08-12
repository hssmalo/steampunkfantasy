"""Holder arithmetic: what Equipment claims, and which Defaults survive.

A Holder is a named place on a Model where Equipment sits, with a limited
capacity — Hands, Tentacles, Reserve Melee and so on. Equipment claims Holder
capacity through its `requires`; a Model declares capacity through its
`equipment_limit`.

The one authority on that arithmetic. Pure functions over already-loaded
config: nothing here reads disk or looks anything up in a `RaceConfig`.

See ADR-0020 for the retention rule these functions implement.
"""

from spf.schemas import type_aliases as t
from spf.schemas.race import EquipmentConfig, ModelConfig


def claims(equipment: EquipmentConfig) -> dict[t.EquipmentHolder, int]:
    """Holder capacity this equipment consumes, summed across its requires.

    `type:` requirements constrain *who* may take the equipment, not *where* it
    sits, so they are skipped. Every other requirement is counted, in every
    OR-group: across all eight races no OR-group mixes two different holders,
    so summing them all is unambiguous.
    """
    result: dict[t.EquipmentHolder, int] = {}
    for group in equipment.requires:
        for req in group:
            if req.key != "type" and isinstance(req.value, int):
                result[req.key] = result.get(req.key, 0) + req.value
    return result


def capacity(model_config: ModelConfig) -> dict[t.EquipmentHolder, int]:
    """Return declared Holder limits; an undeclared Holder has zero capacity."""
    return {limit.holder: limit.limit for limit in model_config.equipment_limit}


def retained_defaults(
    model_config: ModelConfig,
    *,
    defaults: list[EquipmentConfig],
    upgrades: list[EquipmentConfig],
) -> list[EquipmentConfig]:
    """Return the Defaults that survive alongside `upgrades`, in declaration order.

    Upgrades claim first and are never evicted; the Defaults are then walked in
    declaration order, each kept when its claims still fit and dropped when they
    do not. First-fit, not an optimal eviction search.

    Capacity is exactly what the Model declares — a Model whose Defaults
    over-claim its own limits loses one even with no upgrades bought. That is
    the deliberate simple behaviour, guarded by the `default-equipment-limit`
    lint rule rather than by tolerance logic here.
    """
    remaining = capacity(model_config)
    for upgrade in upgrades:
        for holder, count in claims(upgrade).items():
            remaining[holder] = remaining.get(holder, 0) - count

    retained: list[EquipmentConfig] = []
    for default in defaults:
        default_claims = claims(default)
        if all(
            remaining.get(holder, 0) >= count
            for holder, count in default_claims.items()
        ):
            for holder, count in default_claims.items():
                remaining[holder] -= count
            retained.append(default)
    return retained
