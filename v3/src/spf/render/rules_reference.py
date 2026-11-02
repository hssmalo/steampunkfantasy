"""Rules Reference view-model: the rule Records a document's Specials reach.

A *presentation* transposition (ADR 0007) over the rule registries (ADR 0024),
pure over a `Registry` and whatever holds the Specials: no disk access, no
templates. An Army reaches the rules of the loadout it chose and a Race
catalogue the rules of everything it could field, so both seed the same walk.

The Specials are the seeds. From there the walk follows `places` and `see_also`
at every level, so every rule an entry points at is itself an entry (ADR 0041).

One entry per Record, printing the Record's *general* text with its `{N}`
placeholders intact: the Unit line already prints the filled signature, so the
concrete numbers live with the Unit and the general rule lives here.
"""

from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field
from itertools import chain

from spf.armies.army import Army
from spf.prose import LinkedText, link_refs, linked_prose
from spf.prose import resolve as resolve_prose
from spf.registry import SPECIAL, Registry
from spf.render.anchors import anchor as _anchor
from spf.render.anchors import slug
from spf.schemas.race import RaceConfig, fielded_prose, race_slots
from spf.schemas.special import SpecialInstance, Specials

TITLE = "Rules Reference"

PENDING = "Rule text pending."
"""Shown in place of a Stub's text: omitting the entry silently would let the
Rules Reference lie about what a Unit needs."""

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
    effect: LinkedText = field(default_factory=LinkedText)
    phases: list[str] = field(default_factory=list)
    remove: LinkedText = field(default_factory=LinkedText)
    to_hit: str | None = None
    to_be_hit: str | None = None
    written: bool = False
    places: list[RuleLink] = field(default_factory=list)
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

    @property
    def fields(self) -> bool:
        """Whether the entry has anything to list beneath its rule text."""
        return bool(
            self.phases
            or self.remove
            or self.to_hit
            or self.to_be_hit
            or self.places
            or self.see_also
        )

    @property
    def text(self) -> LinkedText:
        """The rule's general text, or the Stub marker when none is written."""
        return self.effect or linked_prose(PENDING if self.pending else None)


@dataclass(frozen=True)
class RulesReference:
    """An Army's rule entries, flat and alphabetical across every namespace."""

    entries: list[RuleEntry]
    anchors: dict[str, str] = field(default_factory=dict)
    """Where each rule's own entry sits, keyed by its ref, so a Unit line and
    that entry agree on the anchor by construction. An Alias Entry is not in
    here: it is addressed by a name, and nothing links to it."""

    title: str = TITLE

    def anchor_of(self, ref: str) -> str | None:
        """Return the anchor a Ref's entry sits at, or None."""
        return self.anchors.get(ref)


@dataclass(frozen=True)
class Seeds:
    """What an Army contributes before any traversal: refs, and Instance names."""

    refs: list[str]
    aliases: list[tuple[str, str]]
    """(the Instance's atmospheric name, the ref of the Record it occurs of)."""


def seeds_from(
    slots: Iterable[Specials], *, registry: Registry, prose: Iterable[str] = ()
) -> Seeds:
    """Collect every ref the given Slots name, in printed order.

    Slots rather than a carrier: an Army and a Race hold their instances in
    different shapes, and everything past the walk is the same for both. `prose`
    is the fielded text beside the Slots, whose Rule Links are seeds too.
    """
    refs: dict[str, None] = {}
    aliases: dict[tuple[str, str], None] = {}
    for specials in slots:
        _collect(specials, registry, refs=refs, aliases=aliases)
    for text in prose:
        refs.update(dict.fromkeys(link_refs(text)))
    return Seeds(refs=list(refs), aliases=list(aliases))


def seeds(army: Army, *, registry: Registry) -> Seeds:
    """Collect every ref an Army's Specials name, in printed order.

    The Army is walked rather than the collapsed `ArmyReference`: collapsing
    only removes entries identical to one already there, so the ref set is the
    same, and the raw walk cannot drift if the collapsing rules change.
    """
    return seeds_from(_every_slot(army), registry=registry, prose=_fielded_prose(army))


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


def _fielded_prose(army: Army) -> Iterable[str]:
    """Yield the notes and damage table text an Army Reference prints."""
    for unit in army.units:
        yield unit.config.note
        for table in unit.config.damage_tables.values():
            yield from (row.effect for row in table.rows)
            yield from table.notes
        for model in unit.models:
            yield model.config.note
            yield model.assault().note  # holds its Equipment's assault notes too
            for equip in model.equipment:
                # A ranged Equipment prints its range note and not its own, and a
                # walked link with no printed path would dead-end (ADR 0042).
                yield equip.note if equip.range is None else equip.range.note


def _instance_prose(
    instance: SpecialInstance, variants: Mapping[str, str]
) -> Iterable[str | None]:
    """Yield the prose an Instance prints, each Variant as drawn (ADR 0042)."""
    yield resolve_prose(instance.text, instance.variant, variants)
    yield resolve_prose(instance.preamble, instance.variant, variants)
    for case in instance.cases:
        yield resolve_prose(case.text, case.variant, variants)


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
        rule = registry.specials.get(identifier)
        variants = rule.variants if rule is not None else {}
        for instance in instances:
            for prose in _instance_prose(instance, variants):
                refs.update(dict.fromkeys(link_refs(prose)))
            if instance.name:
                aliases[instance.name, ref] = None
            arg_sets = [instance.args, *(case.args for case in instance.cases)]
            for value in chain.from_iterable(args.values() for args in arg_sets):
                # A ref argument is one that resolves; a scalar names no
                # record, so the registry is the whole test.
                if isinstance(value, str) and registry.record(value) is not None:
                    refs[value] = None


def build(army: Army, *, registry: Registry, prefix: str = "") -> RulesReference:
    """Resolve a whole Army's Rules Reference, anchors prefixed with `prefix`."""
    return resolve(seeds(army, registry=registry), registry, prefix=prefix)


def build_for_race(
    race_config: RaceConfig, *, registry: Registry, prefix: str = ""
) -> RulesReference:
    """Resolve a whole Race catalogue's Rules Reference.

    An Army reaches the rules of the loadout it chose; a Race reaches the
    rules of everything it could field. Past the walk the two are the same
    resolution, so they share one.
    """
    return resolve(
        seeds_from(
            race_slots(race_config),
            registry=registry,
            prose=(prose for _, prose in fielded_prose(race_config)),
        ),
        registry,
        prefix=prefix,
    )


def resolve(seeded: Seeds, registry: Registry, *, prefix: str = "") -> RulesReference:
    """Close `seeded` over the rule graph and shape the result into entries."""
    entry_refs = _reachable(seeded.refs, registry)
    anchors = {ref: f"{prefix}{_ANCHOR_PREFIX}-{slug(ref)}" for ref in entry_refs}
    entries = [_entry(ref, registry, anchors=anchors) for ref in entry_refs]
    entries += _aliases(seeded.aliases, registry, anchors=anchors, prefix=prefix)
    entries.sort(key=lambda entry: (entry.name.casefold(), entry.qualifier))
    return RulesReference(entries=entries, anchors=anchors)


def _reachable(refs: Iterable[str], registry: Registry) -> dict[str, None]:
    """Close `refs` over `places`, `see_also` and printed Rule Links (ADR 0041).

    Rule cycles are legal and exist, so a visited-set is what terminates it.
    """
    reached: dict[str, None] = {}
    pending = list(refs)
    while pending:
        ref = pending.pop(0)
        if ref in reached or (record := registry.record(ref)) is None:
            continue
        reached[ref] = None
        # Only what an entry prints is an edge, so no entry is left with no
        # visible path to it (ADR 0042).
        pending += [
            *record.places,
            *record.see_also,
            *link_refs(record.effect),
            *link_refs(getattr(record, "remove", None)),
        ]
    return reached


def _entry(ref: str, registry: Registry, *, anchors: dict[str, str]) -> RuleEntry:
    """Shape one Record into its entry, with its links to other rules."""
    record = registry.record(ref)
    assert record is not None  # noqa: S101  guarded by the caller
    return RuleEntry(
        ref=ref,
        name=record.name,
        qualifier=_qualifier(ref, registry),
        anchor=anchors[ref],
        effect=linked_prose(record.effect, anchors.get),
        phases=[str(phase) for phase in getattr(record, "phases", [])],
        remove=linked_prose(getattr(record, "remove", None), anchors.get),
        to_hit=getattr(record, "to_hit", None),
        to_be_hit=getattr(record, "to_be_hit", None),
        written=record.written,
        places=_links(record.places, registry, anchors=anchors),
        # A target keeps its line even though the walk made it an entry: a Stub
        # whose `see_also` is the only thing explaining it would otherwise print
        # nothing at all.
        see_also=_links(record.see_also, registry, anchors=anchors),
    )


def _links(
    targets: Iterable[str], registry: Registry, *, anchors: dict[str, str]
) -> list[RuleLink]:
    """Shape the `targets` that resolve into links."""
    return [
        _link(target, registry, anchors=anchors)
        for target in targets
        if registry.record(target) is not None
    ]


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
    seen: set[tuple[str, str]] = set()
    # One name may be an Instance of two different Records; each is a real
    # entry, and `anchor` disambiguates the two so neither link lands on the
    # other. Anchors are taken from a shared set for the same reason two names
    # that slug alike must not.
    taken: set[str] = set()
    for name, ref in aliases:
        record = registry.record(ref)
        if record is None or name == record.name or (name, ref) in seen:
            continue
        seen.add((name, ref))
        entries.append(
            RuleEntry(
                ref=ref,
                name=name,
                qualifier="",
                anchor=f"{prefix}{_ALIAS_PREFIX}-{_anchor(name, taken)}",
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
