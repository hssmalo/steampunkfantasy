"""Shared fixtures for the render suites."""

from pathlib import Path

import pytest

from spf.render import environments

ART = Path("/assets/goblin/images/art.png")
"""A committed Image Asset that no test needs to exist on disk."""


class FakeLookup:
    """An `ImageLookup` returning a canned path, recording every call."""

    def __init__(self, path: Path | None) -> None:
        """Answer every lookup with `path` — `None` stands for "no art"."""
        self.path = path
        self.calls: list[tuple[str, str]] = []

    def __call__(self, race: str, name: str) -> Path | None:
        """Record the Target asked about, then return the canned path."""
        self.calls.append((race, name))
        return self.path


PINNED_VERSION = "1999.12.0"
"""A version no release will ever carry, so version-stamped output stays stable."""


@pytest.fixture
def pinned_version(monkeypatch: pytest.MonkeyPatch) -> str:
    """Pin the version the templates stamp, decoupling output from the release."""
    monkeypatch.setattr(environments, "spf_version", lambda: PINNED_VERSION)
    return PINNED_VERSION
