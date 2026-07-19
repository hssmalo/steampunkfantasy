"""Shared test doubles for the assets foundation.

A throwaway `FakeService` returning canned bytes and a matching throwaway
`Kind` stand in for the concrete kinds (Lore, Image, Model)
that land in the child issues. Nothing here lives in `src/`.
"""

import operator
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from pathlib import Path

import pytest

from spf.assets import Kind
from spf.assets.kinds import KINDS, Described, Service
from spf.config import config


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


def fake_kind(
    *,
    name: str = "_test",
    service: Service | None = None,
    brief: Callable[[Described], str] = operator.attrgetter("description"),
) -> Kind:
    """Build a throwaway binary kind laid out at `<race>/_test/<name>.txt`.

    Only for tests whose subject is something *other* than the Kind's own
    shape; a test that pins how a field behaves should spell that Kind out in
    full, so the field under test sits next to the assertion. That is why the
    layout fields are fixed here rather than exposed as arguments: the tests
    that vary them are exactly the ones that should not be using this.
    """
    return Kind(
        name=name,
        # Built per call, not shared as a default: a `FakeService` records the
        # seed it last saw, so one instance across tests would leak that.
        service=FakeService() if service is None else service,
        subdir="_test",
        extension="txt",
        targets=frozenset({"race", "unit"}),
        brief=brief,
    )


def register_kind(kind: Kind, monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> Kind:
    """Register `kind` in `KINDS` and point both config roots under `tmp_path`."""
    monkeypatch.setitem(KINDS, kind.name, kind)
    monkeypatch.setattr(config.paths, "candidates", tmp_path / "candidates")
    monkeypatch.setattr(config.paths, "assets", tmp_path / "assets")
    return kind


@pytest.fixture
def test_kind() -> Kind:
    """Return a throwaway binary kind laid out at `<race>/_test/<name>.txt`."""
    return fake_kind()


@pytest.fixture
def refinable_kind() -> Kind:
    """Return a throwaway kind whose Service can refine as well as generate."""
    return fake_kind(name="_refinable", service=FakeRefiner())
