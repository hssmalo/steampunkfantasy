"""The closed effect vocabulary a Damage row's text is parsed into."""

from collections.abc import Mapping
from dataclasses import dataclass


@dataclass(frozen=True, kw_only=True)
class Vocabulary:
    """The Token names plain prose may use, mapped to their ids: `shaken`."""

    tokens: Mapping[str, str]
