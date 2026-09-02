"""Schema for the Site Index.

The authored TOML that says which Army Packs and Races the site publishes, in
what order, and under what heading (ADR 0028, ADR 0035).
"""

from pydantic import Field

from spf.schemas import StrictModel
from spf.schemas import type_aliases as t


class SitePackConfig(StrictModel):
    """One entry in a Site Index: an Army Pack and its Landing Page heading."""

    pack: str
    """The Pack's directory under `armies/`, holding its Army Pack Index."""

    heading: str
    """The Landing Page heading for the Pack's section — not the Pack's own
    title, which belongs to the Army Pack document (ADR 0028)."""


class SiteRacesConfig(StrictModel):
    """The Races the site publishes, and their Landing Page heading.

    One table rather than an entry each: the Races are a single Landing Page
    section over a list, so they share one heading (ADR 0035).
    """

    heading: str
    """The Landing Page heading the Races table appears under."""

    publish: list[t.RaceName] = Field(default_factory=list)
    """The Races to publish, in Landing Page row order. Empty is legal: it says
    the site publishes Races and currently has none."""


class SiteConfig(StrictModel):
    """A Site Index: the ordered Army Packs and the Races the site publishes."""

    packs: list[SitePackConfig] = Field(min_length=1)

    races: SiteRacesConfig | None = None
    """`None` when the index has no `[races]` block: a site that publishes no
    Races at all, as distinct from one publishing an empty list (ADR 0035)."""
