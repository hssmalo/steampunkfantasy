"""Rules Reference view-model: the rule Records an Army's Specials reach.

A *presentation* transposition (ADR 0007) over the rule registries (ADR 0024),
pure over a `Registry` and a resolved Army: no disk access, no templates.

An Army's Specials are the seeds. From there the walk follows `places`
unbounded, because a rule's mechanical consequence is part of the rule, and
`see_also` exactly one hop, promoting only the targets a player has to resolve
on the table (ADR 0029).

One entry per Record, printing the Record's *general* text with its `{N}`
placeholders intact: the Unit line already prints the filled signature, so the
concrete numbers live with the Unit and the general rule lives here.
"""

from collections.abc import Iterable
from dataclasses import dataclass, field

from spf.armies.army import Army
from spf.registry import SPECIAL, Registry
from spf.render.anchors import slug
from spf.schemas.special import Specials

TITLE = "Rules Reference"

PENDING = "Rule text pending."
"""Shown in place of a Stub's text: omitting the entry silently would let the
Rules Reference lie about what a Unit needs."""

PLAYER_FACING = frozenset({"token", "hex", "damage_type"})
"""The namespaces a one-hop `see_also` promotes to a full entry (ADR 0029)."""

_ANCHOR_PREFIX = "rule"
_ALIAS_PREFIX = "rule-alias"


@dataclass(frozen=True)
class RuleLink:
    """A pointer at a rule: what to call it, and where it sits when it is here."""

    name: str
    qualifier: str
    anchor: str | None
    """`None` when the target is named but is no entry of this Rules Reference."""

    @property
    def heading(self) -> str:
        """The rule's name with its Kind Qualifier: `Fog (hex)`."""
        return f"{self.name} ({self.qualifier})" if self.qualifier else self.name


@dataclass(frozen=True)
class RuleEntry:
    """One Rules Reference entry: a rule's general text, or an Alias Entry."""

    ref: str
    name: str
    qualifier: str
    anchor: str
    effect: str | None = None
    phases: list[str] = field(default_factory=list)
    remove: str | None = None
    to_hit: str | None = None
    to_be_hit: str | None = None
    written: bool = False
    see_also: list[RuleLink] = field(default_factory=list)
    alias_for: RuleLink | None = None
    """Set on an Alias Entry, naming the Record the Instance is an occurrence of."""

    @property
    def heading(self) -> str:
        """The entry's heading: its name, plus a Kind Qualifier when it has one."""
        return f"{self.name} ({self.qualifier})" if self.qualifier else self.name

    @property
    def pending(self) -> bool:
        """Whether nothing about this rule is written down yet.

        Not `written`: a record's meaning fields are its own registry's
        business, so a modifier says everything it has to say in its numbers
        and an unwritten one may still carry prose.
        """
        return not (
            self.effect or self.phases or self.remove or self.to_hit or self.to_be_hit
        )


@dataclass(frozen=True)
class RulesReference:
    """An Army's rule entries, flat and alphabetical across every namespace."""

    entries: list[RuleEntry]
    anchors: dict[str, str] = field(default_factory=dict)
    """Every entry's anchor, keyed by its ref, so a Unit line and its entry
    agree on the anchor by construction."""

    title: str = TITLE

    def anchor_for(self, identifier: str) -> str | None:
        """Return the anchor a Special identifier's entry sits at, or None."""
        return self.anchors.get(f"{SPECIAL}.{identifier}")


@dataclass(frozen=True)
class Seeds:
    """What an Army contributes before any traversal: refs, and Instance names."""

    refs: list[str]
    aliases: list[tuple[str, str]]
    """(the Instance's atmospheric name, the ref of the Record it occurs of)."""


def seeds(army: Army, *, registry: Registry) -> Seeds:
    """Collect every ref an Army's Specials name, in printed order.

    The Army is walked rather than the collapsed `ArmyReference`: collapsing
    only removes entries identical to one already there, so the ref set is the
    same, and the raw walk cannot drift if the collapsing rules change.
    """
    refs: dict[str, None] = {}
    aliases: dict[tuple[str, str], None] = {}
    for specials in _every_slot(army):
        _collect(specials, registry, refs=refs, aliases=aliases)
    return Seeds(refs=list(refs), aliases=list(aliases))


def _every_slot(army: Army) -> Iterable[Specials]:
    """Yield every Slot's instances on an Army, in printed order."""
    for unit in army.units:
        yield unit.unit_specials
        for model in unit.models:
            yield model.unit_specials
            yield model.model_specials
            yield model.assault().specials
            for equip in model.equipment:
                yield equip.unit_specials
                yield equip.model_specials
                if equip.range is not None:
                    yield equip.range.specials
                if equip.assault is not None:
                    yield equip.assault.specials


def _collect(
    specials: Specials,
    registry: Registry,
    *,
    refs: dict[str, None],
    aliases: dict[tuple[str, str], None],
) -> None:
    """Add one Slot's Identifiers, ref arguments and atmospheric names."""
    for identifier, instances in specials.items():
        ref = f"{SPECIAL}.{identifier}"
        refs[ref] = None
        for instance in instances:
            if instance.name:
                aliases[instance.name, ref] = None
            for value in instance.args.values():
                # A ref argument is one that resolves; a scalar names no
                # record, so the registry is the whole test.
                if isinstance(value, str) and registry.record(value) is not None:
                    refs[value] = None


def build(army: Army, *, registry: Registry, prefix: str = "") -> RulesReference:
    """Resolve a whole Army's Rules Reference, anchors prefixed with `prefix`."""
    return resolve(seeds(army, registry=registry), registry, prefix=prefix)


def resolve(seeded: Seeds, registry: Registry, *, prefix: str = "") -> RulesReference:
    """Close `seeded` over the rule graph and shape the result into entries."""
    core = _close_over_places(seeded.refs, registry)
    promoted = _promotions(core, registry)
    entry_refs = core | promoted
    anchors = {ref: f"{prefix}{_ANCHOR_PREFIX}-{slug(ref)}" for ref in entry_refs}
    entries = [
        _entry(ref, registry, anchors=anchors, promoted=promoted)
        for ref in entry_refs
        if registry.record(ref) is not None
    ]
    entries += _aliases(seeded.aliases, registry, anchors=anchors, prefix=prefix)
    entries.sort(key=lambda entry: (entry.name.casefold(), entry.qualifier))
    return RulesReference(entries=entries, anchors=anchors)


def _close_over_places(refs: Iterable[str], registry: Registry) -> dict[str, None]:
    """Close `refs` over `places`, unbounded.

    Rule cycles are legal and exist, so a visited-set is what terminates it.
    """
    core: dict[str, None] = {}
    pending = list(refs)
    while pending:
        ref = pending.pop(0)
        if ref in core or (record := registry.record(ref)) is None:
            continue
        core[ref] = None
        pending += record.places
    return core


def _promotions(core: dict[str, None], registry: Registry) -> dict[str, None]:
    """Collect the one-hop `see_also` targets that become entries themselves."""
    promoted: dict[str, None] = {}
    for ref in core:
        record = registry.record(ref)
        assert record is not None  # noqa: S101  `_close_over_places` only keeps these
        for target in record.see_also:
            namespace = target.partition(".")[0]
            if namespace in PLAYER_FACING and target not in core:
                promoted[target] = None
    return promoted


def _entry(
    ref: str,
    registry: Registry,
    *,
    anchors: dict[str, str],
    promoted: dict[str, None],
) -> RuleEntry:
    """Shape one Record into its entry, with its cross-reference links."""
    record = registry.record(ref)
    assert record is not None  # noqa: S101  guarded by the caller
    return RuleEntry(
        ref=ref,
        name=record.name,
        qualifier=_qualifier(ref, registry),
        anchor=anchors[ref],
        effect=record.effect,
        phases=[str(phase) for phase in getattr(record, "phases", [])],
        remove=getattr(record, "remove", None),
        to_hit=getattr(record, "to_hit", None),
        to_be_hit=getattr(record, "to_be_hit", None),
        written=record.written,
        see_also=[
            _link(target, registry, anchors=anchors)
            for target in record.see_also
            # A promoted target says everything it has to say in its own entry.
            if target not in promoted and registry.record(target) is not None
        ],
    )


def _aliases(
    aliases: Iterable[tuple[str, str]],
    registry: Registry,
    *,
    anchors: dict[str, str],
    prefix: str,
) -> list[RuleEntry]:
    """Build an Alias Entry per atmospheric name.

    Without one, a reader looking up the word their card prints dead-ends:
    the list is alphabetical by the *rule's* name, which the card never said.
    """
    entries: list[RuleEntry] = []
    seen: set[str] = set()
    for name, ref in aliases:
        record = registry.record(ref)
        if record is None or name == record.name or name in seen:
            continue
        seen.add(name)
        entries.append(
            RuleEntry(
                ref=ref,
                name=name,
                qualifier="",
                anchor=f"{prefix}{_ALIAS_PREFIX}-{slug(name)}",
                alias_for=_link(ref, registry, anchors=anchors),
            )
        )
    return entries


def _link(ref: str, registry: Registry, *, anchors: dict[str, str]) -> RuleLink:
    """Name a rule, linked when it is an entry of this Rules Reference."""
    return RuleLink(
        name=registry.display_name(ref),
        qualifier=_qualifier(ref, registry),
        anchor=anchors.get(ref),
    )


def _qualifier(ref: str, registry: Registry) -> str:
    """Return a ref's Kind Qualifier: its namespace's singular label."""
    namespace = registry.namespaces.get(ref.partition(".")[0])
    return namespace.label if namespace is not None else ""
