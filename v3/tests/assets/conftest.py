"""Shared test doubles for the assets foundation.

A throwaway :class:`FakeService` returning canned bytes and a matching throwaway
:class:`~spf.assets.Kind` stand in for the concrete kinds (Lore, Image, Model)
that land in the child issues. Nothing here lives in ``src/``.
"""

from collections.abc import Sequence
from dataclasses import dataclass

import pytest

from spf.assets import Kind


@dataclass
class FakeService:
    """A :class:`~spf.assets.Service` returning a fixed list of canned bytes.

    Records the ``seed`` it was last called with so tests can assert threading.
    """

    values: Sequence[bytes | str] = (b"one", b"two", b"three")
    seen_seed: int | None = None

    def generate(
        self, source: str, count: int, *, seed: int | None = None
    ) -> Sequence[bytes | str]:
        """Return the first ``count`` canned values, recording ``seed``."""
        self.seen_seed = seed
        return list(self.values)[:count]


@pytest.fixture
def test_kind() -> Kind:
    """Return a throwaway binary kind laid out at ``<race>/_test/<name>.txt``."""
    return Kind(
        name="_test",
        service=FakeService(),
        subdir="_test",
        extension="txt",
    )
