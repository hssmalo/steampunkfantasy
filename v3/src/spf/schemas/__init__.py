"""Schemas for SteamPunkFantasy."""

from pydantic import BaseModel, ConfigDict


class StrictModel(BaseModel):
    """Require models to be exact."""

    model_config = ConfigDict(extra="forbid")
