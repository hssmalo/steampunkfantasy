"""Check what Equipment claims against the Holders a Model declares.

Kept apart from `rules.py`, which is deliberately pure string predicates over a
`(key, name)` pair and reads no schema at all. This rule needs the model config
*and* the equipment catalogue, so it does not fit `lint_entries`' shape.

The retention rule (ADR-0020) gives Defaults no tolerance for over-claiming:
a Model whose Defaults exceed its own limits silently loses one, even with no
upgrades bought. This is the check that makes that data defect visible.
"""

from collections.abc import Mapping
from typing import TYPE_CHECKING

from spf.armies import holders
from spf.schemas.race import EquipmentConfig, ModelConfig

if TYPE_CHECKING:
    from spf.schemas import type_aliases as t


def check_default_equipment_fits(
    model: ModelConfig, equipment: Mapping[str, EquipmentConfig]
) -> str | None:
    """Name the over-committed Holders, or return `None` when the defaults fit.

    Defaults are measured together, not one at a time: two items that each fit
    alone can still over-commit a Holder between them.
    """
    capacity = holders.capacity(model)
    claimed: dict[t.EquipmentHolder, int] = {}
    for key in model.equipment:
        # A default naming an equipment key that is not in the catalogue is a
        # different defect: `ArmyList.resolve` raises a KeyError on it. Skipping
        # it keeps the linter reporting the defects it *can* see rather than
        # dying on the data it was asked to inspect.
        if (equip := equipment.get(key)) is None:
            continue
        for holder, count in holders.claims(equip).items():
            claimed[holder] = claimed.get(holder, 0) + count

    over = [
        f"defaults claim {holder}:{count} but the limit is {capacity.get(holder, 0)}"
        for holder, count in claimed.items()
        if count > capacity.get(holder, 0)
    ]
    return "; ".join(over) if over else None


def check_requires_one_holder(equipment: EquipmentConfig) -> str | None:
    """Name any `requires` group offering a choice between two Holders.

    `holders.claims` sums every requirement in every group, which is only
    unambiguous while no group is a choice *between* Holders: a "Hands:1 or
    Tentacles:1" group would be counted as claiming one of each. No such group
    exists in the data, and this is what keeps it that way — the day one is
    wanted, `claims` needs a real answer for OR rather than a wider sum.
    """
    mixed = [
        " or ".join(sorted(named))
        for group in equipment.requires
        if len(named := {req.key for req in group if req.key != "type"}) > 1
    ]
    if not mixed:
        return None
    return "; ".join(f"requires offers a choice of Holders: {group}" for group in mixed)
