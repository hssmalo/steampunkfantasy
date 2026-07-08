"""The Kind record and its registry.

A :class:`Kind` is a kind of Asset (Lore, Image, Model). It owns the
:class:`Service` that generates its Candidates and declares, declaratively, how
its files are laid out under a race: ``<race>/[<subdir>/]<name>.<extension>``.

This foundation ships the record type, the :class:`Service` protocol, and the
registry mechanism only. **Zero** concrete kinds are registered here; each kind
issue registers its own.
"""

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Protocol


class Service(Protocol):
    """Generates the raw content for a Kind's Candidates."""

    def generate(
        self, source: str, count: int, *, seed: int | None = None
    ) -> Sequence[bytes | str]:
        """Return ``count`` generated values (text or binary) for ``source``.

        ``seed`` is an optional base seed; a Service derives its own ``count``
        sub-seeds from it, and ``None`` means generate non-deterministically.
        """
        ...


@dataclass(frozen=True)
class Kind:
    """A registered kind of Asset."""

    name: str
    service: Service
    subdir: str | None
    extension: str


KINDS: dict[str, Kind] = {}


def register_kind(kind: Kind) -> Kind:
    """Register a Kind under its name and return it."""
    KINDS[kind.name] = kind
    return kind


def get_kind(name: str) -> Kind:
    """Look up a registered Kind by name."""
    try:
        return KINDS[name]
    except KeyError:
        known = ", ".join(KINDS) or "(none registered)"
        msg = f"Unknown kind {name!r}; known kinds: {known}"
        raise ValueError(msg) from None
