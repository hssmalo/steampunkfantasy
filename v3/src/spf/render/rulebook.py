"""Rulebook view-model: turn an authored Index into the object templates read.

The Rulebook is not "every file in `rules/`" — it is an ordered, authored Index
naming a **Section Kind** per Section (ADR 0018). A Kind binds a source shape to
one parser here and one template partial per family
(`templates/<family>/general-rules/<kind>.<ext>.jinja`, picked by name, nothing
to register).

The registry deliberately mirrors `spf.render.products` and
`spf.render.formats`: same record-plus-dict shape, same "Unknown x; known xs"
failure. Adding a Kind is a registration, never a change to `build_rulebook` or
to `main.<ext>.jinja`.

A bad Index **fails the build**. A Rulebook silently missing a chapter is worse
than one that refuses to build, so every failure names the Section's 1-based
position — what a human counts down the Index file.
"""

import re
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from pathlib import Path

from spf import rules
from spf.render.anchors import anchor as _anchor
from spf.schemas.rulebook import RulebookConfig
from spf.schemas.rules import (
    DieVariableConfig,
    HexRuleConfig,
    ModifierRuleConfig,
    RefVariableConfig,
    RuleRecord,
    SpecialRuleConfig,
    StringVariableConfig,
    TerrainRuleConfig,
    TokenRuleConfig,
    VariableConfig,
)

_H1 = re.compile(r"^#\s")

TOKENS_SOURCE = "tokens.toml"
TERRAIN_SOURCE = "terrain.toml"
HEXES_SOURCE = "hexes.toml"

TOKEN_NAMESPACE = "token."  # noqa: S105  a game Token's namespace, not a credential

type ModifierRecord = (
    ModifierRuleConfig | TerrainRuleConfig | HexRuleConfig | TokenRuleConfig
)
"""Any record that may carry to-hit numbers: the five modifier registries own
nothing else, the other three carry theirs beside their rule."""


class RulesContext:
    """Access to sibling rules files, for cross-referencing parsers.

    A Special names the Token it places, but the Index decides only what is
    *rendered* — a Rulebook may resolve that reference without a Tokens Section
    in it at all. So the context loads what a parser asks for, from beside the
    Index, rather than from what the Index happens to name.

    Loading is lazy and cached: a Rulebook with no cross-references touches no
    file its Index did not name.
    """

    def __init__(self, rules_dir: Path) -> None:
        """Resolve sibling rules files against `rules_dir`."""
        self.rules_dir = rules_dir
        self._tokens: dict[str, TokenRuleConfig] | None = None
        self._terrain: dict[str, TerrainRuleConfig] | None = None
        self._hexes: dict[str, HexRuleConfig] | None = None

    def tokens(self) -> dict[str, TokenRuleConfig]:
        """Return the Token registry, read once from `tokens.toml`."""
        if self._tokens is None:
            self._tokens = rules.get_tokens(self.rules_dir / TOKENS_SOURCE).tokens
        return self._tokens

    def terrain(self) -> dict[str, TerrainRuleConfig]:
        """Return the Terrain registry, read once from `terrain.toml`."""
        if self._terrain is None:
            self._terrain = rules.get_terrain(self.rules_dir / TERRAIN_SOURCE).terrain
        return self._terrain

    def hexes(self) -> dict[str, HexRuleConfig]:
        """Return the Hex Effect registry, read once from `hexes.toml`."""
        if self._hexes is None:
            self._hexes = rules.get_hexes(self.rules_dir / HEXES_SOURCE).hexes
        return self._hexes

    def _token_names(self) -> dict[str, str]:
        """Token key -> display name."""
        return {key: token.name for key, token in self.tokens().items()}

    def token_name(self, key: str) -> str:
        """Display name of Token `key`.

        Raises `ValueError` listing the known keys when there is no such Token:
        a reference that silently renders as nothing is a rule the reader never
        learns about.
        """
        names = self._token_names()
        try:
            return names[key]
        except KeyError:
            known = ", ".join(names) or "(none)"
            msg = f"unknown token {key!r}; known tokens: {known}"
            raise ValueError(msg) from None


@dataclass(frozen=True)
class SectionKind:
    """A registered kind of Rulebook Section: how its source is read."""

    name: str
    parse: Callable[[Path, RulesContext], object]
    """Source path and the build's shared `RulesContext` -> the Section's body,
    in whatever shape the Kind's partials expect. Every parser is handed the
    context whether or not it cross-references anything; the context is lazy,
    so ignoring it costs nothing."""


KINDS: dict[str, SectionKind] = {}


def register_kind(kind: SectionKind) -> SectionKind:
    """Register a Section Kind under its name and return it."""
    KINDS[kind.name] = kind
    return kind


def get_kind(name: str) -> SectionKind:
    """Look up a registered Section Kind by name."""
    try:
        return KINDS[name]
    except KeyError:
        known = ", ".join(KINDS) or "(none registered)"
        msg = f"Unknown kind {name!r}; known kinds: {known}"
        raise ValueError(msg) from None


def constraint_text(variable: VariableConfig) -> str:
    """Describe what `variable` may be, as a reader-facing phrase.

    The schema states a constraint as bounds, an enumeration or a namespace; a
    rulebook states it as English. Enumerated values win over bounds when both
    are given: the list is the stricter, and more useful, statement.
    """
    if isinstance(variable, RefVariableConfig):
        listed = ", ".join(variable.values or variable.namespaces)
        return f"any {listed}"
    if isinstance(variable, DieVariableConfig):
        return "die"
    if variable.values:
        listed = ", ".join(str(value) for value in variable.values)
        return f"one of {listed}"
    if isinstance(variable, StringVariableConfig):
        return "text"
    return _bounds_text(variable.min, variable.max)


def _bounds_text(low: int | None, high: int | None) -> str:
    """Describe an integer variable's bounds as a reader-facing phrase."""
    match low, high:
        case None, None:
            return "integer"
        case low, None:
            return f"integer, at least {low}"
        case None, high:
            return f"integer, at most {high}"
        case low, high:
            return f"integer, {low}-{high}"


def parse_markdown(path: Path, context: RulesContext) -> str:  # noqa: ARG001  every parser takes the context; free text cross-references nothing
    """Read a free-text Markdown Section, dropping its H1 lines.

    A Section's heading always comes from the Index's `title`, so an H1 in the
    source would duplicate it one level too high. Dropping happens here because
    it is family-independent; mapping the *remaining* levels is each family's
    business (`shift_headings` and `md_to_latex`).
    """
    lines = path.read_text(encoding="utf-8").splitlines(keepends=True)
    return "".join(line for line in lines if not _H1.match(line))


MARKDOWN = register_kind(SectionKind(name="markdown", parse=parse_markdown))


@dataclass(frozen=True)
class RuleEntry:
    """One Special, Token, or Hex rule, as the Rulebook shows it.

    Every field the three schemas hold, flattened into one shape: the Army
    Reference carries a Special's `short` override text, while the *full* rule
    text belongs here (CONTEXT.md). A field the source leaves out is `None` or
    empty, and the partials emit nothing for it.
    """

    name: str
    short: str | None
    body: str
    """The rule itself — its `effect`. Markdown."""

    description: str | None
    """Markdown: what the rule represents, rather than what it does."""

    example: str | None
    """Markdown."""

    phases: list[str]
    remove: str | None
    token: str | None
    """The **display name(s)** of the Token this rule places, already resolved
    from the source's ref (decision 17), or None."""

    variables: list[tuple[str, str]]
    """(name, constraint phrase), in the order the source declares them."""

    versions: list[tuple[str, str]]
    """(version, rule text) — a rule that reads differently per damage type."""

    @property
    def has_facts(self) -> bool:
        """Whether the rule has anything for the facts list under its prose."""
        return bool(self.token or self.phases or self.remove or self.variables)


@dataclass(frozen=True)
class RuleGroup:
    """A titled run of rules: a Specials group, or a whole Tokens file.

    `title` is None when the source has no grouping of its own — a group
    heading is a level the reader only pays for when it carries information.
    """

    title: str | None
    rules: list[RuleEntry]

    @property
    def nested(self) -> bool:
        r"""Whether this group's rules sit one heading level deeper.

        The decision is the view-model's, so both families make it the same
        way; mapping the depth to `####` or `\\subsubsection` is each family's
        own business, and stays in its partial (ADR 0005).
        """
        return self.title is not None


@dataclass(frozen=True)
class RulesBody:
    """The body of a structured Section: optional prose plus grouped rules."""

    explanation: str | None
    """Markdown prose above the rules; only `hexes.toml` has any."""

    groups: list[RuleGroup]


def _variables(
    variables: dict[str, VariableConfig],
) -> list[tuple[str, str]]:
    """Render a rule's variable constraints as (name, phrase) pairs."""
    return [(name, constraint_text(spec)) for name, spec in variables.items()]


def _signature(name: str, signature: str | None) -> str | None:
    """Return the heading's suffix: `signature`, unless it is the name again.

    `signature` is the compact form the Army Reference prints in place of the
    full rule; some rules simply repeat their name there, and a Rulebook
    heading reading "Fumble Fumble" is noise the reader has to look past.
    """
    return None if not signature or signature == name else signature


def written[RecordT: RuleRecord](records: dict[str, RecordT]) -> dict[str, RecordT]:
    """Keep the records that carry a rule, dropping the stubs.

    A stub is design intent addressed to the game designer — `spf rules todos`
    is where it is counted. A Rulebook heading with nothing under it promises
    the reader a rule that has not been written.
    """
    return {key: record for key, record in records.items() if record.todo is None}


def _effect_entry(config: TokenRuleConfig | HexRuleConfig) -> RuleEntry:
    """Build the entry for a Token or Hex rule — structurally the same shape."""
    return RuleEntry(
        name=config.name,
        short=_signature(config.name, config.signature),
        body=config.effect or "",
        description=config.flavor,
        example=config.example,
        phases=list(getattr(config, "phases", [])),
        remove=config.remove,
        token=None,
        variables=_variables(config.variables),
        versions=[],
    )


def parse_tokens(path: Path, context: RulesContext) -> RulesBody:  # noqa: ARG001  a Token names no other rule
    """Read `tokens.toml`: its document-level prose, then one untitled group."""
    config = rules.get_tokens(path)
    entries = [_effect_entry(token) for token in written(config.tokens).values()]
    return RulesBody(
        explanation=config.explanation,
        groups=[RuleGroup(title=None, rules=entries)],
    )


TOKENS = register_kind(SectionKind(name="tokens", parse=parse_tokens))


def parse_hexes(path: Path, context: RulesContext) -> RulesBody:  # noqa: ARG001  a Hex names no other rule
    """Read `hexes.toml`: its document-level prose, then one untitled group."""
    config = rules.get_hexes(path)
    entries = [_effect_entry(hex_rule) for hex_rule in written(config.hexes).values()]
    return RulesBody(
        explanation=config.explanation,
        groups=[RuleGroup(title=None, rules=entries)],
    )


HEXES = register_kind(SectionKind(name="hexes", parse=parse_hexes))


def _resolve_tokens(
    key: str, config: SpecialRuleConfig, context: RulesContext, source: Path
) -> str | None:
    """Resolve the Tokens a Special places, to the display names the reader sees.

    Only `token.*` places resolve here: naming a Hex Effect or another Special
    is legal, and rendering the whole reference graph is #73's. Strict on the
    Tokens it does resolve — an unknown one fails the build, naming the
    offending rule and its file, because a reference that quietly renders as
    nothing is how `token = "minor acid"` survived in the data as long as it
    did.
    """
    names: list[str] = []
    for ref in config.places:
        if not ref.startswith(TOKEN_NAMESPACE):
            continue
        try:
            names.append(context.token_name(ref.removeprefix(TOKEN_NAMESPACE)))
        except ValueError as err:
            msg = f"{source.name}: rule {key!r} references {err}"
            raise ValueError(msg) from None
    return ", ".join(names) or None


def _special_entry(config: SpecialRuleConfig, token: str | None) -> RuleEntry:
    """Build the entry for one Special, given its already-resolved Tokens."""
    return RuleEntry(
        name=config.name,
        short=_signature(config.name, config.signature),
        body=config.effect or "",
        description=config.flavor,
        example=config.example,
        phases=[],
        remove=None,
        token=token,
        variables=_variables(config.variables),
        versions=[
            (version, overlay.effect) for version, overlay in config.versions.items()
        ],
    )


SLOT_TITLES = (("assault", "Assault"), ("unit", "Unit"), ("range", "Range"))
"""Special slot -> the heading the reader sees, in reading order. A rule
declaring several slots is listed under each of them."""


def parse_specials(path: Path, context: RulesContext) -> RulesBody:
    """Read `special.toml` as one titled group per slot a Special may sit in.

    Where a Special applies — in an Assault, on a Unit, on a Range — is
    information the reader needs, so the groups stay groups rather than being
    flattened into one alphabetical list (decision 15). The grouping comes from
    each record's `slots`, not from the file's layout (ADR 0024).
    """
    specials = written(rules.get_specials(path).special)
    groups = [
        RuleGroup(
            title=title,
            rules=[
                _special_entry(special, _resolve_tokens(key, special, context, path))
                for key, special in specials.items()
                if slot in special.slots
            ],
        )
        for slot, title in SLOT_TITLES
    ]
    return RulesBody(explanation=None, groups=[g for g in groups if g.rules])


SPECIALS = register_kind(SectionKind(name="specials", parse=parse_specials))


@dataclass(frozen=True)
class ModifierRow:
    """One line of the to-hit table: a source of modifiers and what it does."""

    name: str
    to_hit: str
    to_be_hit: str
    """Modifiers as authored (`+1`, `0`, `-N`) — a signed string, not a number,
    because `-N` stands for a value the rule itself supplies."""

    note: str | None
    """When the modifier applies, or what it stacks with. None when unqualified."""


@dataclass(frozen=True)
class ModifierGroup:
    """A titled run of modifier rows: one category of the to-hit table."""

    title: str
    rows: list[ModifierRow]

    @property
    def has_notes(self) -> bool:
        """Whether any row has a note, and so whether to spend a column on it."""
        return any(row.note for row in self.rows)


@dataclass(frozen=True)
class ToHitBody:
    """The body of the to-hit Section: the table, one group per category."""

    groups: list[ModifierGroup]


TO_HIT_TITLES = {
    "speed": "Speeds",
    "terrain": "Terrain",
    "order": "Orders",
    "range": "Range",
    "angle": "Angle",
    "size": "Size",
    "unit_ability": "Unit Abilities",
    "weapon_ability": "Weapon Abilities",
    "token": "Tokens",
}
"""Category field -> the heading the reader sees. A category missing from here
still renders, under a title derived from its field name: a new category the
author adds to the schema must not silently vanish from the Rulebook."""


def _category_title(field: str) -> str:
    """Heading for a to-hit category, authored or derived from the field name."""
    return TO_HIT_TITLES.get(field, field.replace("_", " ").title())


def _modifier_rows(
    records: Mapping[str, ModifierRecord], *, note: bool = False
) -> list[ModifierRow]:
    """Build the rows for the records in one registry that carry modifiers.

    Membership is a query, not a list: a record belongs in the table when it
    has numbers to contribute. `note` says whether the registry's `effect` is
    the short "when this applies" phrase the note column wants — on a Token it
    is the whole rule, which belongs in the Tokens Section instead.
    """
    return [
        ModifierRow(
            name=record.name,
            to_hit=record.to_hit or "",
            to_be_hit=record.to_be_hit or "",
            note=(record.effect if note else None) or None,
        )
        for record in records.values()
        if record.to_hit or record.to_be_hit
    ]


def parse_to_hit(path: Path, context: RulesContext) -> ToHitBody:
    """Read the to-hit table: one titled group per registry that feeds it.

    The numbers live on whichever record owns the id — a Terrain, a Hex Effect
    and a Token carry their own, so the table is a *view* over the registries
    rather than a second copy of them (ADR 0024). The context reaches the
    sibling registries `modifiers.toml` does not hold. Empty groups are
    dropped: a heading with no rows under it is a promise the table does not
    keep.
    """
    modifiers = rules.get_modifiers(path)
    # Fog is a Hex Effect that behaves like Terrain for to-hit purposes, so it
    # renders among the Terrain rows rather than in a group of its own.
    groups = [
        ("speed", _modifier_rows(modifiers.speed, note=True)),
        (
            "terrain",
            _modifier_rows(context.terrain()) + _modifier_rows(context.hexes()),
        ),
        ("range", _modifier_rows(modifiers.distance, note=True)),
        ("angle", _modifier_rows(modifiers.angle, note=True)),
        ("size", _modifier_rows(modifiers.size, note=True)),
        ("unit_ability", _modifier_rows(modifiers.ability, note=True)),
        ("token", _modifier_rows(context.tokens())),
    ]
    return ToHitBody(
        groups=[
            ModifierGroup(title=_category_title(field), rows=rows)
            for field, rows in groups
            if rows
        ]
    )


TO_HIT = register_kind(SectionKind(name="to_hit", parse=parse_to_hit))


@dataclass(frozen=True)
class Section:
    """One resolved Section: its rendered heading and its parsed body."""

    kind: str
    """Names the partial that renders it: `general-rules/<kind>.<ext>.jinja`."""

    title: str
    anchor: str
    """Slug of the title, unique within the Rulebook, for the Markdown TOC."""

    body: object
    """Whatever the Kind's parser returned."""


@dataclass(frozen=True)
class Rulebook:
    """A whole Rulebook: a document title and its ordered Sections."""

    title: str
    sections: list[Section]


def build_rulebook(index: RulebookConfig, *, rules_dir: Path) -> Rulebook:
    """Resolve an Index into the Rulebook object the templates render.

    Each Section's `kind` is looked up, its `source` located under `rules_dir`,
    and the Kind's parser run over it. An unknown Kind raises `ValueError` and a
    missing source `FileNotFoundError` — both naming the Section's position.
    """
    sections: list[Section] = []
    taken: set[str] = set()
    context = RulesContext(rules_dir)
    for position, config in enumerate(index.sections, start=1):
        where = f"Rulebook Index section {position}"
        try:
            kind = get_kind(config.kind)
        except ValueError as err:
            msg = f"{where}: {err}"
            raise ValueError(msg) from None

        source = rules_dir / config.source
        if not source.is_file():
            msg = f"{where}: source {config.source!r} not found in {rules_dir}"
            raise FileNotFoundError(msg)

        sections.append(
            Section(
                kind=kind.name,
                title=config.title,
                anchor=_anchor(config.title, taken),
                body=kind.parse(source, context),
            )
        )
    return Rulebook(title=index.title, sections=sections)
