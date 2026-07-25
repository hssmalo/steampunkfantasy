"""Schema for the Rulebook Index (ADR 0018).

The Index is the authored TOML that says what the Rulebook contains, and in
what order.

`kind` stays a plain `str` here rather than an enum: it is checked against the
Section Kind registry when the Rulebook is built, so the failure can name the
registered kinds in the house style (`get_format`/`get_product`) instead of
surfacing a Pydantic enum error.
"""

from spf.schemas import StrictModel


class SectionConfig(StrictModel):
    """One entry in a Rulebook Index."""

    kind: str
    source: str
    title: str


class RulebookConfig(StrictModel):
    """A Rulebook Index: a document title and its ordered Sections."""

    title: str
    sections: list[SectionConfig]
