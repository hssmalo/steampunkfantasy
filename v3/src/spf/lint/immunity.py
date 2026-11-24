"""Check that a Unit with no Bio Model states its own poison immunity.

The rule is deliberately repeated on every such Unit rather than stated once in
the rules: a player reads the card, so the card has to say it.
"""

from collections.abc import Mapping

from spf.schemas import type_aliases as t
from spf.schemas.race import ModelConfig, UnitConfig

POISON = "damage_type.poison"

BIO: t.ModelType = "Bio"


def check_poison_immunity(
    unit: UnitConfig, models: Mapping[str, ModelConfig]
) -> str | None:
    """Say what is missing, or return `None` when the Unit needs nothing."""
    if any(BIO in models[key].type for key in unit.models):
        return None
    if any(
        instance.args.get("feature") == POISON
        for instance in unit.specials.get("immunity", [])
    ):
        return None
    return f"no Model is Bio, so the Unit needs Immunity [{POISON}]"
