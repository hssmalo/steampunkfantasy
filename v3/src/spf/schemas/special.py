"""The Special instance: one occurrence of a rule in Race data (ADR 0024).

A rule lives once, in a registry under `rules/`, which owns its identifier and
its display name. A Race file writes *instances* of it, keyed by that
identifier, and what an instance carries is closed at four keys.
"""

from pydantic import Field

from spf.schemas import StrictModel


class SpecialInstance(StrictModel):
    """One occurrence of a rule, keyed in the data by the rule's identifier.

    The id is the table key rather than a field, which is what makes repeats
    native: three `resistance` instances need no `(2)` / `(3)` suffix to stack.
    """

    name: str | None = None
    """An atmospheric display name, overriding the rule's name in the heading.

    It never overrides a ref target's name inside a signature: the vocabulary
    stays in one place, only what is printed may be local.
    """

    text: str | None = None
    """Free prose about this occurrence, not about the rule."""

    replace: bool = False
    """Clear every instance of this id contributed earlier in the source chain.

    It needs no target field, because the table key is the target.
    """

    args: dict[str, int | str] = Field(default_factory=dict)
    """Values for the rule's variables, and for those of every ref target.

    Nested rather than flat because that arg vocabulary is edited in other
    files: flat args would make `name` / `text` / `replace` a permanent
    constraint on names their author never sees.
    """


type Specials = dict[str, list[SpecialInstance]]
"""Instances in one slot, grouped by the id of the rule each occurs of."""
