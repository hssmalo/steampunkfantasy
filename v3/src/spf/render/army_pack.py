"""Army Pack view-model: bind several Armies' Army References into one pack.

Like `spf.render.army_rules`, this is a *presentation* transposition (ADR
0007): frozen dataclasses, no template logic, no disk access except the
injected `ImageLookup`. It is pure — it takes already-resolved Armies, so a
test builds a pack with no filesystem at all — and reuses `build_reference`
per Army rather than reimplementing any of it (issue #100 §3.2).

No cross-Army deduplication of any kind: two players fielding the same Race
each get complete pages, because a Pack's whole point is that a player's own
pages are handable on their own (decision D4).
"""

from collections.abc import Sequence
from dataclasses import dataclass

from spf.armies.army import Army
from spf.render.anchors import anchor as _anchor
from spf.render.army_rules import ArmyReference, build_reference
from spf.render.images import ImageLookup, committed_image


@dataclass(frozen=True)
class PackEntry:
    """One Army's place in an Army Pack: its Label and its Army Reference."""

    label: str
    """The name the Army appears under in the Pack's contents — the Index
    entry's `label`, or the Army's Nick when the Index gives none (D12)."""

    anchor: str
    """Slug of `label`, unique within the Pack, for the Markdown TOC."""

    reference: ArmyReference


@dataclass(frozen=True)
class ArmyPack:
    """A whole Army Pack: a document title and its ordered entries."""

    title: str
    stem: str
    entries: list[PackEntry]


def build_pack(
    armies: Sequence[tuple[str | None, Army]],
    *,
    title: str,
    stem: str,
    image_for: ImageLookup = committed_image,
) -> ArmyPack:
    """Build an `ArmyPack` from already-resolved Armies, in the given order.

    `armies` pairs each Army with an optional Label override — the shape
    `io.load_pack_armies` returns. A missing Label falls back to the Army's
    Nick (D12).
    """
    taken: set[str] = set()
    entries: list[PackEntry] = []
    for label, army in armies:
        resolved_label = label if label is not None else army.nick
        entries.append(
            PackEntry(
                label=resolved_label,
                anchor=_anchor(resolved_label, taken),
                reference=build_reference(army, stem=stem, image_for=image_for),
            )
        )
    return ArmyPack(title=title, stem=stem, entries=entries)
