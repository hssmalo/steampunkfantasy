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
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

from spf import rules
from spf.schemas.rulebook import RulebookConfig
from spf.schemas.rules import (
    HexRuleConfig,
    IntVariableConfig,
    SpecialRuleConfig,
    StringVariableConfig,
    TokenRuleConfig,
)

_H1 = re.compile(r"^#\s")
_NON_SLUG = re.compile(r"[^a-z0-9]+")

TOKENS_SOURCE = "tokens.toml"


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
        self._tokens: dict[str, str] | None = None

    def _token_names(self) -> dict[str, str]:
        """Token key -> display name, read once from `tokens.toml`."""
        if self._tokens is None:
            config = rules.get_tokens(self.rules_dir / TOKENS_SOURCE)
            self._tokens = {key: token.name for key, token in config.tokens.items()}
        return self._tokens

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


def constraint_text(variable: IntVariableConfig | StringVariableConfig) -> str:
    """Describe what `variable` may be, as a reader-facing phrase.

    The schema states a constraint as bounds or an enumeration; a rulebook
    states it as English. Enumerated values win over bounds when both are
    given: the list is the stricter, and more useful, statement.
    """
    if variable.values:
        listed = ", ".join(str(value) for value in variable.values)
        return f"one of {listed}"
    if not isinstance(variable, IntVariableConfig):
        return "text"
    match variable.min, variable.max:
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
    """The rule itself — a Special's `explanation`, a Token's or Hex's
    `effect`. Markdown."""

    description: str | None
    """Markdown: what the rule represents, rather than what it does."""

    example: str | None
    """Markdown."""

    phases: list[str]
    remove: str | None
    token: str | None
    """The **display name** of the Token this rule places, already resolved
    from the source's key (decision 17), or None."""

    variables: list[tuple[str, str]]
    """(name, constraint phrase), in the order the source declares them."""

    versions: list[tuple[str, str]]
    """(version, rule text) — a rule that reads differently per damage type."""


@dataclass(frozen=True)
class RuleGroup:
    """A titled run of rules: a Specials group, or a whole Tokens file.

    `title` is None when the source has no grouping of its own, which is what
    the partials key their heading depth off — a group heading is a level the
    reader only pays for when it carries information.
    """

    title: str | None
    rules: list[RuleEntry]


@dataclass(frozen=True)
class RulesBody:
    """The body of a structured Section: optional prose plus grouped rules."""

    explanation: str | None
    """Markdown prose above the rules; only `hexes.toml` has any."""

    groups: list[RuleGroup]


def _variables(
    variables: dict[str, IntVariableConfig | StringVariableConfig] | None,
) -> list[tuple[str, str]]:
    """Render a rule's variable constraints as (name, phrase) pairs."""
    return [(name, constraint_text(spec)) for name, spec in (variables or {}).items()]


def _token_entry(config: TokenRuleConfig | HexRuleConfig) -> RuleEntry:
    """Build the entry for a Token or Hex rule — structurally the same shape."""
    return RuleEntry(
        name=config.name,
        short=config.short,
        body=config.effect,
        description=None,
        example=None,
        phases=list(config.phases),
        remove=config.remove,
        token=None,
        variables=_variables(config.variables),
        versions=[],
    )


def parse_tokens(path: Path, context: RulesContext) -> RulesBody:  # noqa: ARG001  a Token names no other rule
    """Read `tokens.toml` as one untitled group of rules, in file order."""
    config = rules.get_tokens(path)
    entries = [_token_entry(token) for token in config.tokens.values()]
    return RulesBody(explanation=None, groups=[RuleGroup(title=None, rules=entries)])


TOKENS = register_kind(SectionKind(name="tokens", parse=parse_tokens))


def parse_hexes(path: Path, context: RulesContext) -> RulesBody:  # noqa: ARG001  a Hex names no other rule
    """Read `hexes.toml`: its document-level prose, then one untitled group."""
    config = rules.get_hexes(path)
    entries = [_token_entry(hex_rule) for hex_rule in config.hexes.values()]
    return RulesBody(
        explanation=config.explanation,
        groups=[RuleGroup(title=None, rules=entries)],
    )


HEXES = register_kind(SectionKind(name="hexes", parse=parse_hexes))


def _special_entry(
    key: str, config: SpecialRuleConfig, context: RulesContext, source: Path
) -> RuleEntry:
    """Build the entry for one Special, resolving the Token it places.

    Resolution is strict: an unknown Token names the offending rule and its
    file, because a reference that quietly renders as nothing is how
    `token = "minor acid"` survived in the data for as long as it did.
    """
    token = None
    if config.token is not None:
        try:
            token = context.token_name(config.token)
        except ValueError as err:
            msg = f"{source.name}: rule {key!r} references {err}"
            raise ValueError(msg) from None

    return RuleEntry(
        name=config.name,
        short=config.short,
        body=config.explanation,
        description=config.description,
        example=config.example,
        phases=[],
        remove=None,
        token=token,
        variables=_variables(config.variables),
        versions=list((config.versions or {}).items()),
    )


def parse_specials(path: Path, context: RulesContext) -> RulesBody:
    """Read `special.toml` as one titled group per group in the schema.

    Where a Special applies — in an Assault, on a Unit, on a Weapon — is
    information the reader needs, so the groups stay groups rather than being
    flattened into one alphabetical list (decision 15).
    """
    config = rules.get_specials(path)
    groups = [
        RuleGroup(
            title=title,
            rules=[
                _special_entry(key, special, context, path)
                for key, special in specials.items()
            ],
        )
        for title, specials in (
            ("Assault", config.assault),
            ("Unit", config.unit),
            ("Weapon", config.weapon),
        )
    ]
    return RulesBody(explanation=None, groups=groups)


SPECIALS = register_kind(SectionKind(name="specials", parse=parse_specials))


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


def _slug(title: str) -> str:
    """Reduce `title` to a lowercase, dash-separated anchor."""
    return _NON_SLUG.sub("-", title.lower()).strip("-")


def _anchor(title: str, taken: set[str]) -> str:
    """Return a slug of `title` not already in `taken`.

    Two Sections may legitimately share a title, but not an anchor: every link
    to the second would otherwise land on the first.
    """
    slug = _slug(title)
    anchor = slug
    suffix = 1
    while anchor in taken:
        suffix += 1
        anchor = f"{slug}-{suffix}"
    taken.add(anchor)
    return anchor


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
