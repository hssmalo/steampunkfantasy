"""Shared test doubles for the assets foundation.

A throwaway `FakeService` returning canned bytes and a matching throwaway
`Kind` stand in for the concrete kinds (Lore, Image, Model)
that land in the child issues. Nothing here lives in `src/`.
"""

import operator
from collections.abc import Callable, Sequence
from dataclasses import dataclass

import pytest

from spf.assets import Kind


@dataclass
class FakeService:
    """A `Service` returning a fixed list of canned bytes.

    Records the `seed` it was last called with so tests can assert threading.
    """

    values: Sequence[bytes | str] = (b"one", b"two", b"three")
    seen_seed: int | None = None

    def generate(
        self,
        source: str,
        count: int,
        *,
        seed: int | None = None,
        on_result: Callable[[bytes | str], None] | None = None,
    ) -> Sequence[bytes | str]:
        """Return the first `count` canned values, recording `seed`."""
        self.seen_seed = seed
        values = list(self.values)[:count]
        if on_result is not None:
            for value in values:
                on_result(value)
        return values


@dataclass
class FakeRefiner(FakeService):
    """A `FakeService` that additionally refines, recording what it was given."""

    seen_init: bytes | None = None
    seen_source: str | None = None

    def refine(
        self,
        source: str,
        init: bytes,
        count: int,
        *,
        seed: int | None = None,
        on_result: Callable[[bytes | str], None] | None = None,
    ) -> Sequence[bytes | str]:
        """Return the first `count` canned values, recording the Correction."""
        self.seen_init = init
        self.seen_source = source
        return self.generate(source, count, seed=seed, on_result=on_result)


@pytest.fixture
def test_kind() -> Kind:
    """Return a throwaway binary kind laid out at `<race>/_test/<name>.txt`."""
    return Kind(
        name="_test",
        service=FakeService(),
        subdir="_test",
        extension="txt",
        targets=frozenset({"race", "unit"}),
        brief=operator.attrgetter("description"),
    )


@pytest.fixture
def refinable_kind() -> Kind:
    """Return a throwaway kind whose Service can refine as well as generate."""
    return Kind(
        name="_refinable",
        service=FakeRefiner(),
        subdir="_test",
        extension="txt",
        targets=frozenset({"race", "unit"}),
        brief=operator.attrgetter("description"),
    )
