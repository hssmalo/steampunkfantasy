"""Tests for the Rulebook product: index, kind registry, view-model, CLI."""

from pathlib import Path

import pytest
from pydantic import ValidationError

from spf.config import config
from spf.frontends.cli.render import GENERAL_RULES, RenderOpts, render_general_rules
from spf.render import render
from spf.render.formats import get_format
from spf.render.products import PRODUCTS
from spf.render.rulebook import (
    HEXES,
    KINDS,
    MARKDOWN,
    SPECIALS,
    TO_HIT,
    TOKENS,
    Rulebook,
    RuleEntry,
    RuleGroup,
    RulesBody,
    RulesContext,
    Section,
    SectionKind,
    build_rulebook,
    constraint_text,
    get_kind,
    parse_hexes,
    parse_markdown,
    parse_specials,
    parse_to_hit,
    parse_tokens,
    register_kind,
)
from spf.rules import get_rulebook
from spf.schemas.rulebook import RulebookConfig, SectionConfig
from spf.schemas.rules import (
    FormulaVariableConfig,
    IntVariableConfig,
    StringVariableConfig,
    UnionVariableConfig,
)
from tests.conftest import unwrapped

VALID_INDEX = """\
title = "Test Rulebook"

[[sections]]
kind = "markdown"
source = "round.md"
title = "The Round"
"""


# --- The index schema -------------------------------------------------------


def test_index_parses_a_valid_document() -> None:
    index = RulebookConfig(
        title="Test Rulebook",
        sections=[SectionConfig(kind="markdown", source="round.md", title="The Round")],
    )

    assert index.title == "Test Rulebook"
    (section,) = index.sections
    assert section.kind == "markdown"
    assert section.source == "round.md"
    assert section.title == "The Round"


def test_index_requires_a_document_title() -> None:
    with pytest.raises(ValidationError, match="title"):
        RulebookConfig(sections=[])  # pyright: ignore[reportCallIssue]


def test_section_requires_a_title() -> None:
    # H1s are dropped from a source (decision 6), so the index is the only
    # place a section heading can come from.
    with pytest.raises(ValidationError, match="title"):
        SectionConfig(kind="markdown", source="round.md")  # pyright: ignore[reportCallIssue]


def test_index_rejects_an_unknown_key() -> None:
    with pytest.raises(ValidationError, match="chapters"):
        RulebookConfig(title="Test", sections=[], chapters=[])  # pyright: ignore[reportCallIssue]


# --- get_rulebook -----------------------------------------------------------


def test_get_rulebook_reads_an_explicit_path(tmp_path: Path) -> None:
    path = tmp_path / "rulebook.toml"
    path.write_text(VALID_INDEX, encoding="utf-8")

    index = get_rulebook(path)

    assert index.title == "Test Rulebook"
    assert [section.source for section in index.sections] == ["round.md"]


def test_get_rulebook_defaults_to_the_committed_index() -> None:
    index = get_rulebook()

    assert index.title
    assert index.sections


# --- The Section Kind registry ----------------------------------------------


def test_markdown_kind_is_registered() -> None:
    assert KINDS["markdown"] is MARKDOWN
    assert get_kind("markdown") is MARKDOWN
    assert MARKDOWN.parse is parse_markdown


def test_registry_registers_and_looks_up() -> None:
    kind = SectionKind(name="_probe", parse=lambda path, _context: path.read_text())
    try:
        assert register_kind(kind) is kind
        assert get_kind("_probe") is kind
    finally:
        KINDS.pop("_probe", None)


def test_unknown_kind_lists_the_known_kinds() -> None:
    with pytest.raises(
        ValueError, match=r"Unknown kind 'orders'; known kinds: .*markdown"
    ):
        get_kind("orders")


# --- RulesContext -----------------------------------------------------------

TOKENS_SOURCE = """\
explanation = "How tokens work."

[tokens]

[tokens.minor_acid]
name = "Minor Acid"
effect = "Roll a die."

[tokens.poison]
name = "Poison"
signature = "[{N}]"
effect = "Roll a d{N}."
"""


def test_rules_context_resolves_a_token_to_its_display_name(tmp_path: Path) -> None:
    rules_dir = _rules_dir(tmp_path, {"tokens.toml": TOKENS_SOURCE})

    assert RulesContext(rules_dir).token_name("minor_acid") == "Minor Acid"


def test_rules_context_rejects_an_unknown_token_listing_the_known_ones(
    tmp_path: Path,
) -> None:
    rules_dir = _rules_dir(tmp_path, {"tokens.toml": TOKENS_SOURCE})

    with pytest.raises(ValueError, match=r"unknown token 'minor acid'") as excinfo:
        RulesContext(rules_dir).token_name("minor acid")

    message = str(excinfo.value)
    assert "known tokens:" in message
    assert "minor_acid" in message
    assert "poison" in message


def test_rules_context_touches_no_file_until_asked(tmp_path: Path) -> None:
    # The Index controls what is *rendered*; a Rulebook with no cross-reference
    # must not need a tokens file to exist at all.
    context = RulesContext(tmp_path)

    with pytest.raises(FileNotFoundError):
        context.token_name("minor_acid")


def test_rules_context_loads_the_tokens_file_once(tmp_path: Path) -> None:
    rules_dir = _rules_dir(tmp_path, {"tokens.toml": TOKENS_SOURCE})
    context = RulesContext(rules_dir)

    assert context.token_name("poison") == "Poison"
    (rules_dir / "tokens.toml").unlink()

    assert context.token_name("minor_acid") == "Minor Acid"


# --- The constraint formatter -----------------------------------------------


@pytest.mark.parametrize(
    ("variable", "expected"),
    [
        (IntVariableConfig(type="int", min=1, max=4), "integer, 1-4"),
        (IntVariableConfig(type="int", values=[2, 4, 6]), "one of 2, 4, 6"),
        (IntVariableConfig(type="int", min=1), "integer, at least 1"),
        (IntVariableConfig(type="int", max=6), "integer, at most 6"),
        (IntVariableConfig(type="int"), "integer"),
        (
            StringVariableConfig(type="str", values=["regular", "psychic"]),
            "one of regular, psychic",
        ),
        (StringVariableConfig(type="str"), "text"),
        (FormulaVariableConfig(type="formula"), "formula"),
        # A union's value set enumerates its numeric member only, so a formula
        # member has to be spelled out or the reader reads it as forbidden.
        (
            UnionVariableConfig(type=["int", "formula"], values=[4, 6]),
            "one of 4, 6, or a formula",
        ),
        (UnionVariableConfig(type=["int", "die"], min=1, max=12), "integer, 1-12"),
        (
            IntVariableConfig(type="int", min=1, max=4, optional=True),
            "integer, 1-4; optional",
        ),
    ],
)
def test_constraint_text_describes_a_variable(
    variable: IntVariableConfig
    | StringVariableConfig
    | FormulaVariableConfig
    | UnionVariableConfig,
    expected: str,
) -> None:
    assert constraint_text(variable) == expected


# --- The markdown kind's parser ---------------------------------------------


def test_markdown_kind_drops_h1_lines(tmp_path: Path) -> None:
    source = tmp_path / "round.md"
    source.write_text("# The Round\n\nBody text.\n\n## Phases\n", encoding="utf-8")

    body = parse_markdown(source, RulesContext(tmp_path))

    assert "# The Round" not in body
    assert "Body text." in body
    assert "## Phases" in body


def test_markdown_kind_keeps_a_hash_that_is_not_a_heading(tmp_path: Path) -> None:
    source = tmp_path / "round.md"
    source.write_text("Roll #1 on the table.\n", encoding="utf-8")

    assert parse_markdown(source, RulesContext(tmp_path)) == "Roll #1 on the table.\n"


# --- The tokens kind's parser -----------------------------------------------

FULL_TOKENS_SOURCE = """\
explanation = "Place two of a token the first time, one thereafter."

[tokens]

[tokens.poison]
name = "Poison"
signature = "[{N}]"
phases = ["Agony 3"]
remove = "When it kills a model"
effect = \"\"\"Roll a d{N}.
- Ignore armor
- Apply the damage
\"\"\"

[tokens.poison.variables]
N = { type = "int", values = [2, 4, 6] }

[tokens.terror]
name = "Terror"
phases = ["Agony 0"]
effect = "Acts as if the unit has Terror."

[tokens.endurance]
name = "Endurance"
todo = "Rule text not yet written."
"""


def test_tokens_kind_is_registered() -> None:
    assert KINDS["tokens"] is TOKENS
    assert TOKENS.parse is parse_tokens


def test_tokens_kind_yields_one_untitled_group_in_file_order(tmp_path: Path) -> None:
    source = tmp_path / "tokens.toml"
    source.write_text(FULL_TOKENS_SOURCE, encoding="utf-8")

    body = parse_tokens(source, RulesContext(tmp_path))

    assert isinstance(body, RulesBody)
    assert body.explanation == "Place two of a token the first time, one thereafter."
    (group,) = body.groups
    assert isinstance(group, RuleGroup)
    assert group.title is None
    # The endurance stub is not a rule the Rulebook can show a reader yet.
    assert [rule.name for rule in group.rules] == ["Poison", "Terror"]


def test_tokens_kind_keeps_the_document_level_explanation(tmp_path: Path) -> None:
    # The twin of the hexes case: both sources carry prose above their table.
    source = tmp_path / "tokens.toml"
    source.write_text(FULL_TOKENS_SOURCE, encoding="utf-8")

    body = parse_tokens(source, RulesContext(tmp_path))

    assert body.explanation == "Place two of a token the first time, one thereafter."


def test_tokens_kind_carries_every_field_across(tmp_path: Path) -> None:
    source = tmp_path / "tokens.toml"
    source.write_text(FULL_TOKENS_SOURCE, encoding="utf-8")

    (group,) = parse_tokens(source, RulesContext(tmp_path)).groups
    poison, terror = group.rules

    assert isinstance(poison, RuleEntry)
    assert poison.short == "[{N}]"
    assert poison.phases == ["Agony 3"]
    assert poison.remove == "When it kills a model"
    assert poison.variables == [("N", "one of 2, 4, 6")]
    # The effect is Markdown and stays Markdown: its bullets are a real list.
    assert poison.body.splitlines()[1] == "- Ignore armor"
    assert poison.token is None
    assert poison.versions == []
    assert terror.short is None
    assert terror.remove is None
    assert terror.variables == []


# --- The hexes kind's parser ------------------------------------------------

HEXES_SOURCE = """\
explanation = "Hex effects trigger during movement."

[hexes]

[hexes.fog]
name = "Fog"
effect = "Blocks line of sight."
remove = "Remove one Fog per hex in the aftermath phase"
"""


def test_hexes_kind_is_registered() -> None:
    assert KINDS["hexes"] is HEXES
    assert HEXES.parse is parse_hexes


def test_hexes_kind_keeps_the_document_level_explanation(tmp_path: Path) -> None:
    # One of the two sources with prose above its table; tokens.toml is the other.
    source = tmp_path / "hexes.toml"
    source.write_text(HEXES_SOURCE, encoding="utf-8")

    body = parse_hexes(source, RulesContext(tmp_path))

    assert body.explanation == "Hex effects trigger during movement."
    (group,) = body.groups
    assert group.title is None
    (fog,) = group.rules
    assert fog.name == "Fog"
    assert fog.body == "Blocks line of sight."
    assert fog.remove == "Remove one Fog per hex in the aftermath phase"


# --- The specials kind's parser ---------------------------------------------

SPECIALS_SOURCE = """\
[special.minor_acid]
name = "Assault Minor Acid"
slots = ["assault"]
signature = "[1 for {N}]"
effect = "Targets get one minor acid token for each {N} hits."
places = ["token.minor_acid"]

[special.minor_acid.variables]
N = { type = "int", min = 1, max = 4 }

[special.cunning_assault]
name = "Cunning Assault"
slots = ["assault"]
signature = "[{N}]"
effect = "Add +1 to all future damage tokens."
example = "Hit four times and you add two tokens."
flavor = "Any cunning way to take out armored units."

[special.resistance]
name = "Resistance"
slots = ["unit"]
signature = "{version}[{N}]"
effect = "Improved resilience versus {version} damage."

[special.resistance.versions."damage_type.regular"]
effect = "Regular damage is reduced by {N}."

[special.resistance.versions."damage_type.psychic"]
effect = "Psychic damage is reduced by {N}."

[special.fumble]
name = "Fumble"
slots = ["range"]
signature = "Fumble"
effect = "A natural 1 to hit is a fumble."

[special.overrun]
name = "Overrun"
slots = ["assault"]
todo = "Rule text not yet written."
"""


def test_specials_kind_is_registered() -> None:
    assert KINDS["specials"] is SPECIALS
    assert SPECIALS.parse is parse_specials


def test_specials_kind_yields_one_titled_group_per_slot(
    tmp_path: Path,
) -> None:
    # Where a rule applies is information, so the groups stay groups rather
    # than being flattened into one alphabetical list. The grouping comes from
    # each record's `slots`, not from the file's layout.
    rules_dir = _rules_dir(
        tmp_path, {"special.toml": SPECIALS_SOURCE, "tokens.toml": TOKENS_SOURCE}
    )

    body = parse_specials(rules_dir / "special.toml", RulesContext(rules_dir))

    assert body.explanation is None

    assert [group.title for group in body.groups] == ["Assault", "Unit", "Range"]
    assault, unit, range_ = body.groups
    # The Overrun stub is not a rule the Rulebook can show a reader yet.
    assert [rule.name for rule in assault.rules] == [
        "Assault Minor Acid",
        "Cunning Assault",
    ]
    assert [rule.name for rule in unit.rules] == ["Resistance"]
    assert [rule.name for rule in range_.rules] == ["Fumble"]


def test_specials_kind_resolves_a_token_to_its_display_name(tmp_path: Path) -> None:
    rules_dir = _rules_dir(
        tmp_path, {"special.toml": SPECIALS_SOURCE, "tokens.toml": TOKENS_SOURCE}
    )

    body = parse_specials(rules_dir / "special.toml", RulesContext(rules_dir))

    acid, cunning = body.groups[0].rules
    assert acid.token == "Minor Acid"  # noqa: S105  a game Token's name, not a credential
    assert cunning.token is None
    assert cunning.example == "Hit four times and you add two tokens."
    assert cunning.description == "Any cunning way to take out armored units."


def test_specials_kind_drops_a_signature_that_only_repeats_the_name(
    tmp_path: Path,
) -> None:
    # `signature` is the Army Reference's compact override; when it is just
    # the name again, the Rulebook heading would read "Fumble Fumble".
    rules_dir = _rules_dir(
        tmp_path, {"special.toml": SPECIALS_SOURCE, "tokens.toml": TOKENS_SOURCE}
    )

    body = parse_specials(rules_dir / "special.toml", RulesContext(rules_dir))

    (fumble,) = body.groups[2].rules
    assert fumble.name == "Fumble"
    assert fumble.short is None


def test_specials_kind_carries_the_versions_map(tmp_path: Path) -> None:
    rules_dir = _rules_dir(
        tmp_path, {"special.toml": SPECIALS_SOURCE, "tokens.toml": TOKENS_SOURCE}
    )

    body = parse_specials(rules_dir / "special.toml", RulesContext(rules_dir))

    (resistance,) = body.groups[1].rules
    assert resistance.versions == [
        ("regular", "Regular damage is reduced by {N}."),
        ("psychic", "Psychic damage is reduced by {N}."),
    ]


def test_specials_kind_rejects_an_unresolvable_token(tmp_path: Path) -> None:
    rules_dir = _rules_dir(
        tmp_path,
        {
            "special.toml": SPECIALS_SOURCE.replace(
                '"token.minor_acid"', '"token.minor_acids"'
            ),
            "tokens.toml": TOKENS_SOURCE,
        },
    )

    with pytest.raises(ValueError, match=r"unknown token 'minor_acids'") as excinfo:
        parse_specials(rules_dir / "special.toml", RulesContext(rules_dir))

    message = str(excinfo.value)
    assert "special.toml" in message
    assert "'minor_acid'" in message  # the rule that carries the bad reference
    assert "known tokens:" in message


def test_specials_kind_parses_the_committed_file() -> None:
    # The real data: strict resolution means every committed `token =` has to
    # name a Token that actually exists.
    body = parse_specials(
        config.paths.rules / "special.toml", RulesContext(config.paths.rules)
    )

    tokens = {rule.token for group in body.groups for rule in group.rules if rule.token}
    assert tokens == {"Hidden", "Hypnotized", "Insane", "Shaken"}


# --- The to_hit kind's parser -----------------------------------------------

MODIFIER_NAMESPACES_SOURCE = """\
[namespaces.speed]
name = "Speeds"
label = "speed"
file = "modifiers.toml"
table = "speed"

[namespaces.terrain]
name = "Terrain"
label = "terrain"
file = "terrain.toml"
table = "terrain"

[namespaces.hex]
name = "Hexes"
label = "hex"
file = "hexes.toml"
table = "hexes"
group = "terrain"

[namespaces.token]
name = "Tokens"
label = "token"
file = "tokens.toml"
table = "tokens"

[damage_type]
"""

MODIFIERS_SOURCE = """\
[speed.still]
name = "Still"
to_hit = "+1"
to_be_hit = "+1"

[speed.flying]
name = "Flying"
to_hit = "-1"
to_be_hit = "-1"
effect = "Stacks with still, slow, and fast"

[speed.all]
name = "All"
todo = "Not a speed a unit can be in."

[distance]

[angle]

[size]

[ability]
"""

MODIFIER_TERRAIN_SOURCE = """\
[terrain.forest]
name = "Forest"
to_hit = "0"
to_be_hit = "-1"
todo = "Rule text not yet written."
"""

MODIFIER_HEXES_SOURCE = """\
explanation = "Hex effects trigger during movement."

[hexes]

[hexes.fog]
name = "Fog"
effect = "Blocks line of sight."
to_hit = "-1"
to_be_hit = "-1"
"""


def _modifier_rules_dir(tmp_path: Path) -> Path:
    """Write the registries the to-hit table is a view over, plus their index."""
    return _rules_dir(
        tmp_path,
        {
            "namespaces.toml": MODIFIER_NAMESPACES_SOURCE,
            "modifiers.toml": MODIFIERS_SOURCE,
            "terrain.toml": MODIFIER_TERRAIN_SOURCE,
            "hexes.toml": MODIFIER_HEXES_SOURCE,
            "tokens.toml": TOKENS_SOURCE,
        },
    )


def test_to_hit_kind_is_registered() -> None:
    assert KINDS["to_hit"] is TO_HIT
    assert TO_HIT.parse is parse_to_hit


def test_to_hit_kind_yields_one_titled_group_per_category(tmp_path: Path) -> None:
    rules_dir = _modifier_rules_dir(tmp_path)

    body = parse_to_hit(rules_dir / "modifiers.toml", RulesContext(rules_dir))

    # Empty categories are dropped: a heading with no rows says nothing. The
    # Tokens in this fixture carry no modifiers, so that group drops too.
    assert [group.title for group in body.groups] == ["Speeds", "Terrain"]


def test_to_hit_kind_carries_every_field_across(tmp_path: Path) -> None:
    rules_dir = _modifier_rules_dir(tmp_path)

    speeds, _ = parse_to_hit(
        rules_dir / "modifiers.toml", RulesContext(rules_dir)
    ).groups

    # A record with no numbers is not a row: membership is a query over the
    # registry, so the `all` stub never reaches the table.
    still, flying = speeds.rows
    assert (still.name, still.to_hit, still.to_be_hit) == ("Still", "+1", "+1")
    assert still.note is None  # an unwritten note is None, not the empty string
    assert flying.note == "Stacks with still, slow, and fast"
    assert speeds.has_notes


def test_to_hit_kind_reports_a_group_with_no_notes(tmp_path: Path) -> None:
    # Drives the column count in both families' partials.
    rules_dir = _modifier_rules_dir(tmp_path)

    _, terrain = parse_to_hit(
        rules_dir / "modifiers.toml", RulesContext(rules_dir)
    ).groups

    assert not terrain.has_notes


def test_to_hit_kind_renders_fog_among_the_terrains(tmp_path: Path) -> None:
    # Fog is a Hex Effect that behaves like Terrain for to-hit purposes, and
    # the numbers live on the record that owns the id, wherever that is.
    rules_dir = _modifier_rules_dir(tmp_path)

    _, terrain = parse_to_hit(
        rules_dir / "modifiers.toml", RulesContext(rules_dir)
    ).groups

    assert [row.name for row in terrain.rows] == ["Forest", "Fog"]


def test_to_hit_kind_parses_the_committed_file() -> None:
    body = parse_to_hit(
        config.paths.rules / "modifiers.toml", RulesContext(config.paths.rules)
    )

    titles = [group.title for group in body.groups]
    # Order is `namespaces.toml`'s declaration order and each title is the
    # namespace's own display name — neither is hand-listed here.
    assert titles[0] == "Speeds"
    assert "Abilities" in titles


# --- build_rulebook ---------------------------------------------------------


def _index(*sections: SectionConfig, title: str = "Test Rulebook") -> RulebookConfig:
    return RulebookConfig(title=title, sections=list(sections))


def _section(
    *, kind: str = "markdown", source: str = "round.md", title: str = "The Round"
) -> SectionConfig:
    return SectionConfig(kind=kind, source=source, title=title)


def _rules_dir(tmp_path: Path, files: dict[str, str]) -> Path:
    """Write `files` (real filenames -> content) into `tmp_path` and return it."""
    tmp_path.mkdir(parents=True, exist_ok=True)
    for name, text in files.items():
        (tmp_path / name).write_text(text, encoding="utf-8")
    return tmp_path


def test_build_rulebook_builds_a_section_per_index_entry(tmp_path: Path) -> None:
    rules_dir = _rules_dir(
        tmp_path, {"round.md": "# Dropped\n\nBody.\n", "setup.md": "Setup.\n"}
    )

    rulebook = build_rulebook(
        _index(_section(), _section(source="setup.md", title="Setting Up")),
        rules_dir=rules_dir,
    )

    assert isinstance(rulebook, Rulebook)
    assert rulebook.title == "Test Rulebook"
    first, second = rulebook.sections
    assert isinstance(first, Section)
    assert first.kind == "markdown"
    assert first.title == "The Round"
    assert "Dropped" not in str(first.body)
    assert "Body." in str(first.body)
    assert second.title == "Setting Up"


def test_build_rulebook_slugs_the_title_into_an_anchor(tmp_path: Path) -> None:
    rules_dir = _rules_dir(tmp_path, {"round.md": "Body.\n"})

    rulebook = build_rulebook(
        _index(_section(title="Fire & Movement, Part 2")), rules_dir=rules_dir
    )

    (section,) = rulebook.sections
    assert section.anchor == "fire-movement-part-2"


def test_build_rulebook_gives_duplicate_titles_distinct_anchors(tmp_path: Path) -> None:
    # Two same-named sections would otherwise both answer to `#the-round`, and
    # every link to the second would land on the first.
    rules_dir = _rules_dir(tmp_path, {"round.md": "Body.\n", "setup.md": "More.\n"})

    rulebook = build_rulebook(
        _index(_section(), _section(source="setup.md")), rules_dir=rules_dir
    )

    first, second = rulebook.sections
    assert first.anchor != second.anchor


def test_build_rulebook_rejects_an_unknown_kind_by_position(tmp_path: Path) -> None:
    rules_dir = _rules_dir(tmp_path, {"round.md": "Body.\n"})

    with pytest.raises(
        ValueError, match=r"section 2: Unknown kind 'orders'"
    ) as excinfo:
        build_rulebook(
            _index(_section(), _section(kind="orders", source="round.md")),
            rules_dir=rules_dir,
        )

    assert "known kinds:" in str(excinfo.value)


def test_build_rulebook_rejects_a_missing_source_by_position(tmp_path: Path) -> None:
    rules_dir = _rules_dir(tmp_path, {})

    with pytest.raises(FileNotFoundError) as excinfo:
        build_rulebook(_index(_section(source="absent.md")), rules_dir=rules_dir)

    message = str(excinfo.value)
    assert "section 1" in message
    assert "absent.md" in message


def test_build_rulebook_gives_every_parser_a_shared_context(tmp_path: Path) -> None:
    # One context per build, so a file read for section 1 is not read again for
    # section 4 — and rooted where the sources are.
    rules_dir = _rules_dir(tmp_path, {"round.md": "Body.\n", "setup.md": "More.\n"})
    seen: list[RulesContext] = []
    kind = SectionKind(name="_probe", parse=lambda _path, context: seen.append(context))
    register_kind(kind)
    try:
        build_rulebook(
            _index(_section(kind="_probe"), _section(kind="_probe", source="setup.md")),
            rules_dir=rules_dir,
        )
    finally:
        KINDS.pop("_probe", None)

    first, second = seen
    assert first is second
    assert first.rules_dir == rules_dir


def test_build_rulebook_accepts_an_empty_index(tmp_path: Path) -> None:
    rulebook = build_rulebook(_index(), rules_dir=tmp_path)

    assert rulebook.sections == []


# --- End-to-end rendering against the real templates ------------------------

_SOURCE = """\
# Dropped by the parser

Intro prose with **bold**.

## A Subheading

- one
- two
"""


@pytest.fixture
def rulebook(tmp_path: Path) -> Rulebook:
    rules_dir = _rules_dir(tmp_path / "rules", {"round.md": _SOURCE})
    return build_rulebook(_index(_section()), rules_dir=rules_dir)


def test_render_markdown_links_the_contents_to_an_anchor(
    tmp_path: Path, rulebook: Rulebook
) -> None:
    out = render(
        GENERAL_RULES,
        rulebook,
        fmt=get_format("markdown"),
        name="rulebook",
        output_root=tmp_path,
    )

    text = out.read_text(encoding="utf-8")
    assert out == tmp_path / "general-rules" / "rulebook.md"
    assert "# Test Rulebook" in text
    assert "- [The Round](#the-round)" in text
    # `md_to_html` emits no heading ids, so the anchor has to be explicit.
    assert '<a id="the-round"></a>' in text
    assert "## The Round" in text


def test_render_markdown_shifts_source_headings_below_the_section(
    tmp_path: Path, rulebook: Rulebook
) -> None:
    out = render(
        GENERAL_RULES,
        rulebook,
        fmt=get_format("markdown"),
        name="rulebook",
        output_root=tmp_path,
    )

    text = out.read_text(encoding="utf-8")
    assert "### A Subheading" in text
    assert "\n## A Subheading" not in text
    assert "Dropped by the parser" not in text


def test_render_html_resolves_the_contents_link(
    tmp_path: Path, rulebook: Rulebook
) -> None:
    out = render(
        GENERAL_RULES,
        rulebook,
        fmt=get_format("html"),
        name="rulebook",
        output_root=tmp_path,
    )

    html = out.read_text(encoding="utf-8")
    assert 'href="#the-round"' in html
    assert 'id="the-round"' in html


def test_render_latex_has_furniture_and_converted_body(
    tmp_path: Path, rulebook: Rulebook
) -> None:
    out = render(
        GENERAL_RULES,
        rulebook,
        fmt=get_format("latex"),
        name="rulebook",
        output_root=tmp_path,
    )

    text = out.read_text(encoding="utf-8")
    assert r"\title{Test Rulebook}" in text
    assert r"\tableofcontents" in text
    assert r"\section{The Round}" in text
    assert r"\subsection{A Subheading}" in text
    assert r"\textbf{bold}" in text
    assert r"\begin{itemize}" in text
    assert "Dropped by the parser" not in text


# --- The structured Kinds' partials, over the real rules files --------------


@pytest.fixture
def real_rulebook() -> Rulebook:
    """Build the committed Index over the committed sources."""
    return build_rulebook(get_rulebook(), rules_dir=config.paths.rules)


@pytest.fixture
def real_markdown(tmp_path: Path, real_rulebook: Rulebook) -> str:
    out = render(
        GENERAL_RULES,
        real_rulebook,
        fmt=get_format("markdown"),
        name="rulebook",
        output_root=tmp_path,
    )
    return out.read_text(encoding="utf-8")


@pytest.fixture
def real_latex(tmp_path: Path, real_rulebook: Rulebook) -> str:
    out = render(
        GENERAL_RULES,
        real_rulebook,
        fmt=get_format("latex"),
        name="rulebook",
        output_root=tmp_path,
    )
    return out.read_text(encoding="utf-8")


def test_markdown_partials_nest_specials_below_their_group(real_markdown: str) -> None:
    assert "### Assault\n" in real_markdown
    assert "### Unit\n" in real_markdown
    assert "### Range\n" in real_markdown
    assert "#### Cunning Assault [{N}]" in real_markdown
    # Tokens have no groups, so a token rule keeps the shallower level.
    assert "### Minor Acid\n" in real_markdown


def test_markdown_partials_keep_a_prose_bullet_list_a_list(real_markdown: str) -> None:
    # `unit.heal`'s explanation is Markdown; its bullets must stay bullets.
    assert "\n- Extinguish one fire. Cost 3." in real_markdown


def test_latex_partials_nest_specials_below_their_group(real_latex: str) -> None:
    assert r"\section{Special Rules}" in real_latex
    assert r"\subsection{Assault}" in real_latex
    assert r"\subsubsection{Cunning Assault [\{N\}]}" in real_latex
    # Tokens have no groups, so a token rule is a subsection, not a deeper one.
    assert r"\subsection{Minor Acid}" in real_latex


def test_latex_partials_render_the_structured_details(real_latex: str) -> None:
    assert r"\textbf{Places:} Shaken" in real_latex
    assert r"\textbf{M:} integer, 1-4" in real_latex
    assert r"\textbf{Phases:} Agony 1" in real_latex
    assert r"\textbf{Example:} If you hit" in real_latex
    assert r"\textbf{Versions}" in real_latex
    assert r"\textbf{psychic:}" in real_latex


def test_latex_partials_convert_a_prose_bullet_list(real_latex: str) -> None:
    assert r"\item Extinguish one fire. Cost 3." in real_latex


def test_markdown_partials_tabulate_the_to_hit_modifiers(real_markdown: str) -> None:
    assert "### Speeds\n" in real_markdown
    assert "| Flying | -1 | -1 | Stacks with still, slow, and fast |" in real_markdown
    # A group with no notes spends no column on them.
    assert "| On Edge | -1 | 0 |\n" in real_markdown


def test_latex_partials_tabulate_the_to_hit_modifiers(real_latex: str) -> None:
    assert r"\section{To-Hit Modifiers}" in real_latex
    # `md_to_latex` has no table rule, so the rows are built by the partial.
    assert (
        r"Camouflage & 0 & -1 & Applies when the unit is in the given terrain \\"
        in (real_latex)
    )


# --- The CLI ----------------------------------------------------------------


def test_cli_writes_the_rulebook(tmp_path: Path) -> None:
    out = tmp_path / "rulebook.md"

    render_general_rules(opts=RenderOpts(format="markdown", out=out))

    assert "SteamPunkFantasy Rulebook" in out.read_text(encoding="utf-8")


def test_cli_honors_an_alternate_index(tmp_path: Path) -> None:
    _rules_dir(tmp_path, {"round.md": _SOURCE})
    index = tmp_path / "alternate.toml"
    index.write_text(VALID_INDEX, encoding="utf-8")
    out = tmp_path / "rulebook.md"

    render_general_rules(index=index, opts=RenderOpts(format="markdown", out=out))

    assert "# Test Rulebook" in out.read_text(encoding="utf-8")


def test_cli_reports_a_missing_index_on_stderr(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    with pytest.raises(SystemExit) as excinfo:
        render_general_rules(index=tmp_path / "absent.toml")

    assert excinfo.value.code == 1
    assert "Error:" in unwrapped(capsys.readouterr().err)


def test_cli_reports_an_unknown_kind_on_stderr(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    index = tmp_path / "bad.toml"
    index.write_text(
        'title = "Bad"\n\n[[sections]]\nkind = "orders"\n'
        'source = "round.md"\ntitle = "Orders"\n',
        encoding="utf-8",
    )

    with pytest.raises(SystemExit) as excinfo:
        render_general_rules(index=index)

    assert excinfo.value.code == 1
    assert "Unknown kind 'orders'" in unwrapped(capsys.readouterr().err)


def test_general_rules_product_is_registered() -> None:
    assert PRODUCTS["general-rules"] is GENERAL_RULES
