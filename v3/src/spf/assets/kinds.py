"""The Kind record and its registry.

A `Kind` is a kind of Asset (Lore, Image, Model). It owns the
`Service` that generates its Candidates and declares, declaratively, how
its files are laid out under a race: `<race>/[<subdir>/]<name>.<extension>`.

This foundation ships the record type, the `Service` protocol, and the
registry mechanism only. **Zero** concrete kinds are registered here; each kind
issue registers its own.
"""

from collections.abc import Callable, Sequence
from dataclasses import dataclass
from typing import Literal, Protocol, runtime_checkable

TargetLevel = Literal["race", "unit", "model"]


class Service(Protocol):
    """Generates the raw content for a Kind's Candidates."""

    def generate(
        self,
        source: str,
        count: int,
        *,
        seed: int | None = None,
        on_result: Callable[[bytes | str], None] | None = None,
    ) -> Sequence[bytes | str]:
        """Return `count` generated values (text or binary) for `source`.

        `seed` is an optional base seed; a Service derives its own `count`
        sub-seeds from it, and `None` means generate non-deterministically.

        `on_result`, when given, is called with each value in order as it
        becomes available, so a caller can persist results incrementally instead
        of waiting for the whole batch; the full sequence is still returned.
        """
        ...


@runtime_checkable
class Refiner(Protocol):
    """A `Service` that can additionally refine an existing Candidate.

    An *optional* capability: `Service.generate` stays exactly as it is, so
    Kinds that have no image concept never grow one. A Kind's Service is
    checked against this protocol at refine time, so an unsupported Kind
    fails with a clean message rather than an `AttributeError`.
    """

    def refine(
        self,
        source: str,
        init: bytes,
        count: int,
        *,
        seed: int | None = None,
        on_result: Callable[[bytes | str], None] | None = None,
    ) -> Sequence[bytes | str]:
        """Return `count` values refining `init` by the Correction `source`.

        `source` is the Correction, applied verbatim; `init` is the source
        Candidate's own bytes. `seed` and `on_result` behave exactly as they
        do for `generate`.
        """
        ...


@dataclass(frozen=True)
class Kind:
    """A registered kind of Asset."""

    name: str
    service: Service
    subdir: str | None
    extension: str
    targets: frozenset[TargetLevel]
    """The levels this Kind can depict: an Image targets a Race or a Unit."""


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
