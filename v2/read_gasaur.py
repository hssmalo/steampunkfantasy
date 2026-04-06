from typing import Literal

from configaroo import Configuration
from pydantic import BaseModel, ConfigDict, field_validator

gasaur = Configuration.from_file("gasaur.toml")


class Funds(BaseModel):
    model_config = ConfigDict(extra="forbid")

    xp: int = 0
    cp: int = 0
    ip: int = 0
    mp: int = 0


class Unit(BaseModel):
    name: str
    race: str
    models: list[str]
    size: Literal["huge", "medium", "small", "tiny"]
    cost: Funds
    armor: list[int]

    @field_validator("models", mode="before")
    @classmethod
    def require_model_exists(cls, models: list[str]) -> list[str]:
        for model in models:
            if model not in ["troll"]:  # TODO: read from TOML file
                raise ValueError(f"model {model} doesnt exist")
        return models


import IPython

IPython.embed()
