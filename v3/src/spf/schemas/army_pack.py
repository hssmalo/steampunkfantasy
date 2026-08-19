"""Schema for the Army Pack Index (mirroring ADR 0018).

The Index is the authored TOML that says which Armies an Army Pack contains,
in what order, and under what title — a directory scan has no order, silently
promotes a half-finished army file into a published roster, and cannot express
editorial intent (ADR 0018's reasoning, transferred).
"""

from spf.schemas import StrictModel


class PackArmyConfig(StrictModel):
    """One entry in an Army Pack Index."""

    army: str
    """The Army's load name, resolved relative to the Index's own directory."""

    label: str | None = None
    """Combined with the Army's Nick as `"<label>: <nick>"` in the Pack;
    omitted, the Army appears under its Nick alone."""


class ArmyPackConfig(StrictModel):
    """An Army Pack Index: a document title and its ordered Army entries."""

    title: str
    armies: list[PackArmyConfig]
