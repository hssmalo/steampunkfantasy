"""The Special instance: one occurrence of a rule in Race data (ADR 0024).

A rule lives once, in a registry under `rules/`, which owns its identifier and
its display name. A Race file writes *instances* of it, keyed by that
identifier, and what an instance carries is a closed set of keys.

An instance takes one of two shapes (ADR 0030): *prose-shaped*, a signature
followed by free `text`, or *case-shaped*, a `preamble` scoping the `cases`
that each supply their own args.

Whichever prose slot the shape allows may be spelled inline or drawn from the
rule's pool of variants by name (ADR 0031). The two are alternative spellings
of one slot, never two layers of it.
"""

from typing import Self

from pydantic import Field, model_validator

from spf.schemas import StrictModel

_TWO_SPELLINGS = (
    "'variant' spells the prose slot rather than adding to it: write the"
    " sentence inline, or name a variant of the rule, never both"
)
"""Why a variant and inline prose cannot share one occurrence (ADR 0031)."""


class SpecialCase(StrictModel):
    """One value-bearing line of a case-shaped instance (ADR 0030).

    Args and a scrap of prose saying when those values apply. It carries
    neither a name nor `replace`: an atmospheric name is per-instance, and
    `replace` operates on whole instances along the source chain.
    """

    text: str | None = None
    """When these values apply: "at point blank range"."""

    variant: str | None = None
    """The rule's name for that prose, drawn from its variants (ADR 0031)."""

    args: dict[str, int | str] = Field(default_factory=dict)
    """Values for the rule's variables, merged over the instance's own."""

    @model_validator(mode="after")
    def _one_spelling_only(self) -> Self:
        """Keep the prose slot spelled one way, inline or by name (ADR 0031)."""
        if self.variant is not None and self.text is not None:
            raise ValueError(_TWO_SPELLINGS)
        return self


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

    preamble: str | None = None
    """Prose printed before the cases it scopes, and only with cases.

    Named for its position rather than its content: some are conditions ("If
    not using aim"), most are instructions ("Choose one hex").
    """

    variant: str | None = None
    """The rule's name for this occurrence's prose, drawn from its variants.

    Which slot it fills is settled by the shape rather than by a second field
    name: with cases it is the `preamble`, without them the `text` (ADR 0031).
    """

    cases: list[SpecialCase] = Field(default_factory=list)
    """The values this occurrence supplies, one line per condition (ADR 0030)."""

    replace: bool = False
    """Clear every instance of this id contributed earlier in the source chain.

    It needs no target field, because the table key is the target.
    """

    args: dict[str, int | str] = Field(default_factory=dict)
    """Values for the rule's variables, and for those of every ref target.

    Nested rather than flat because that arg vocabulary is edited in other
    files: flat args would make `name` / `text` / `replace` a permanent
    constraint on names their author never sees.

    Every case inherits these, and may override or add to them, so a value
    constant across the cases is written once.
    """

    @model_validator(mode="after")
    def _one_shape_only(self) -> Self:
        """Keep an instance prose-shaped or case-shaped, never both (ADR 0030)."""
        if self.text is not None and self.cases:
            msg = (
                "an instance carries either 'text' or 'cases': prose about the"
                " whole occurrence, or the values each case supplies"
            )
            raise ValueError(msg)
        if self.preamble is not None and not self.cases:
            msg = (
                "'preamble' scopes cases; an instance with no cases wants"
                " 'text' or the carrier's 'note'"
            )
            raise ValueError(msg)
        if self.variant is not None and (self.text, self.preamble) != (None, None):
            raise ValueError(_TWO_SPELLINGS)
        return self


type Specials = dict[str, list[SpecialInstance]]
"""Instances in one slot, grouped by the id of the rule each occurs of."""
