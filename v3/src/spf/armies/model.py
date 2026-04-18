"""Resolved Model data structure with self-contained effective properties."""

from dataclasses import dataclass, field

from spf.schemas import type_aliases as t
from spf.schemas.race import AssaultConfig, EquipmentConfig, ModelConfig, Stacker


@dataclass(frozen=True)
class Model:
    """A fully resolved model slot: equipment configs are stored directly.

    After construction no race_config is needed for any computation.
    """

    name: str
    config: ModelConfig = field(repr=False)
    default_equipment: tuple[EquipmentConfig, ...] = field(repr=False)
    upgrade_equipment: tuple[EquipmentConfig, ...] = field(repr=False)

    @property
    def equipment(self) -> tuple[EquipmentConfig, ...]:
        """Effective equipment.

        When any upgrade equipment is present, all default equipment is discarded.
        """
        return self.upgrade_equipment or self.default_equipment

    @property
    def unit_specials(self) -> dict[t.UnitSpecial, str]:
        """Stacked unit-level specials: model config then each equipment in order."""
        result: dict[t.UnitSpecial, str] = dict(self.config.unit_special)
        for equip in self.equipment:
            result |= equip.unit_special
        return result

    @property
    def model_specials(self) -> dict[t.ModelSpecial, str]:
        """Stacked model-level specials: model config then each equipment in order."""
        result: dict[t.ModelSpecial, str] = dict(self.config.special)
        for equip in self.equipment:
            result |= equip.model_special
        return result

    def cost(self) -> t.Cost:
        """Return intrinsic upgrade cost: sum of upgrade equipment costs.

        Does NOT account for upgrade_all pricing — that belongs to Unit.cost().
        """
        return sum(
            (equip.cost for equip in self.upgrade_equipment if equip.cost is not None),
            t.Cost(),
        )

    def assault(self) -> AssaultConfig:
        """Return resolved AssaultConfig with Stacker modifications applied.

        Stacker semantics:
          - add: int → scalar add; Angles[int] → element-wise addition
          - replace: any type → full replacement
          - extend: list types → list.extend

        Raises ValueError for invalid operations:
          - add or extend on Die/DieResult (string) fields
          - add on ap when current value is "N/A"
        """
        strength = list(self.config.assault.strength)
        strength_die: t.DieResult = self.config.assault.strength_die
        deflection = list(self.config.assault.deflection)
        deflection_die: t.DieResult = self.config.assault.deflection_die
        damage: t.Die = self.config.assault.damage
        ap: t.ArmorPenetration = self.config.assault.ap
        special: dict[t.AssaultSpecial, str] = dict(self.config.assault.special)

        for equip in self.equipment:
            ea = equip.assault
            if ea is None:
                continue
            if ea.strength is not None:
                strength = _apply_angles("strength", strength, ea.strength, equip.name)
            if ea.strength_die is not None:
                strength_die = _apply_die(
                    "strength_die", strength_die, ea.strength_die, equip.name
                )
            if ea.deflection is not None:
                deflection = _apply_angles(
                    "deflection", deflection, ea.deflection, equip.name
                )
            if ea.deflection_die is not None:
                deflection_die = _apply_die(
                    "deflection_die", deflection_die, ea.deflection_die, equip.name
                )
            if ea.damage is not None:
                damage = _apply_die("damage", damage, ea.damage, equip.name)
            if ea.ap is not None:
                ap = _apply_ap(ap, ea.ap, equip.name)
            special |= ea.special

        return AssaultConfig(
            strength=strength,
            strength_die=strength_die,
            deflection=deflection,
            deflection_die=deflection_die,
            damage=damage,
            ap=ap,
            special=special,
        )


# ---------------------------------------------------------------------------
# Stacker application helpers
# ---------------------------------------------------------------------------


def _apply_angles(
    field_name: str,
    current: list[int],
    stacker: Stacker[list[int]],
    equip_name: str,
) -> list[int]:
    """Apply a Stacker to an Angles[int] (list[int]) field."""
    if stacker.replace is not None:
        return list(stacker.replace)
    if stacker.add is not None:
        return [s + a for s, a in zip(current, stacker.add, strict=True)]
    if stacker.extend is not None:
        return [*current, *stacker.extend]
    msg = f"Equipment '{equip_name}': empty Stacker on field '{field_name}'"
    raise ValueError(msg)


def _apply_die(
    field_name: str,
    _current: str,
    stacker: Stacker[str],
    equip_name: str,
) -> str:
    """Apply a Stacker to a Die/DieResult (str) field; only replace is valid."""
    if stacker.replace is not None:
        return stacker.replace
    if stacker.add is not None:
        msg = (
            f"Equipment '{equip_name}': cannot use 'add' on"
            f" Die/DieResult field '{field_name}'; use 'replace'"
        )
        raise ValueError(msg)
    if stacker.extend is not None:
        msg = (
            f"Equipment '{equip_name}': cannot use 'extend' on"
            f" Die/DieResult field '{field_name}'; use 'replace'"
        )
        raise ValueError(msg)
    msg = f"Equipment '{equip_name}': empty Stacker on field '{field_name}'"
    raise ValueError(msg)


def _apply_ap(
    current: t.ArmorPenetration,
    stacker: Stacker[t.ArmorPenetration],
    equip_name: str,
) -> t.ArmorPenetration:
    """Apply a Stacker to an ArmorPenetration field."""
    if stacker.replace is not None:
        return stacker.replace
    if stacker.add is not None:
        if current == "N/A":
            msg = (
                f"Equipment '{equip_name}': cannot use 'add' on"
                " ap='N/A'; use 'replace' to set a numeric value"
            )
            raise ValueError(msg)
        return current + stacker.add  # type: ignore[operator]
    msg = f"Equipment '{equip_name}': empty Stacker on field 'ap'"
    raise ValueError(msg)
