"""Schema for the Site Index.

The authored TOML that says which Army Packs the site publishes, in what order,
and under what heading (ADR 0028).
"""

from pydantic import Field

from spf.schemas import StrictModel


class SitePackConfig(StrictModel):
    """One entry in a Site Index: an Army Pack and its Landing Page heading."""

    pack: str
    """The Pack's directory under `armies/`, holding its Army Pack Index."""

    heading: str
    """The Landing Page heading for the Pack's section — not the Pack's own
    title, which belongs to the Army Pack document (ADR 0028)."""


class SiteConfig(StrictModel):
    """A Site Index: the ordered Army Packs the site publishes."""

    packs: list[SitePackConfig] = Field(min_length=1)
