"""ArmyModel data structure and model-level slot/requirement helpers."""

from dataclasses import dataclass, field

from spf.schemas import type_aliases as t
from spf.schemas.race import ModelConfig, RaceConfig


@dataclass(frozen=True)
class ArmyModel:
    """One model slot within a army unit, with any equipment upgrades applied."""

    name: str
    config: ModelConfig = field(repr=False)
    upgrades: tuple[str, ...]


def _remaining_slots(
    model: ArmyModel, race_config: RaceConfig
) -> dict[t.EquipmentHolder, int]:
    """Compute remaining holder slots after all current equipment (defaults + upgrades).

    Slot usage is read from each equipment's requires field. In practice, holder
    requirements always appear in single-item OR-groups, so iterating all items
    in all groups gives the correct usage. If an OR-group contained multiple holder
    requirements in the future, this would over-count; revisit then.
    """
    slots: dict[t.EquipmentHolder, int] = {
        limit.holder: limit.limit for limit in model.config.equipment_limit
    }
    for equip_key in (*model.config.equipment, *model.upgrades):
        for req_group in race_config.equipment[equip_key].requires:
            for req in req_group:
                if (
                    req.key != "type"
                    and isinstance(req.value, int)
                    and req.key in slots
                ):
                    slots[req.key] -= req.value  # type: ignore[index]
    return slots


def _satisfies_requirement(
    req: t.Requirement,
    model: ArmyModel,
    remaining_slots: dict[t.EquipmentHolder, int],
) -> bool:
    if req.key == "type":
        return req.value in model.config.type
    available = remaining_slots.get(req.key, 0)
    return isinstance(req.value, int) and available >= req.value


def _unsatisfied_groups(
    requires: list[list[t.Requirement]],
    model: ArmyModel,
    race_config: RaceConfig,
) -> list[list[t.Requirement]]:
    """Return OR-groups from requires that are not satisfied by model.

    An empty list means the model satisfies all requirement groups.
    """
    remaining = _remaining_slots(model, race_config)
    return [
        group
        for group in requires
        if not any(_satisfies_requirement(req, model, remaining) for req in group)
    ]


def _format_failed_group(
    group: list[t.Requirement],
    remaining_slots: dict[t.EquipmentHolder, int],
) -> str:
    """Format a failing OR-group as a human-readable constraint description."""
    parts: list[str] = []
    for req in group:
        if req.key == "type":
            parts.append(f"type:{req.value}")
        else:
            available = remaining_slots.get(req.key, 0)  # type: ignore[arg-type]
            parts.append(f"{req.key}:{req.value} (have {available})")
    return "needs " + " or ".join(parts)


def _satisfies_requires(
    requires: list[list[t.Requirement]],
    model: ArmyModel,
    race_config: RaceConfig,
) -> bool:
    """Evaluate CNF requires: every outer group must have ≥1 satisfied inner req."""
    return not _unsatisfied_groups(requires, model, race_config)
