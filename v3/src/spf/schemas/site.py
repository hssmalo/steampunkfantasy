"""Schema for the Site Index (mirroring ADR 0018).

The Index is the authored TOML that says which Army Packs the site publishes,
in what order, and under what heading. Publishing is an editorial act — a glob
over `armies/*/pack.toml` would publish whatever directory happens to exist,
which is the reasoning ADR 0018 already applied one level down.
"""

from pydantic import Field

from spf.schemas import StrictModel


class SitePackConfig(StrictModel):
    """One entry in a Site Index: an Army Pack and its Landing Page heading."""

    pack: str
    """The Pack's directory under `armies/`, holding its Army Pack Index."""

    heading: str
    """The Landing Page heading for the Pack's section. Deliberately not the
    Pack's own title: that titles the Army Pack document, and retitling the
    document must not reflow the site."""


class SiteConfig(StrictModel):
    """A Site Index: the ordered Army Packs the site publishes."""

    packs: list[SitePackConfig] = Field(min_length=1)
