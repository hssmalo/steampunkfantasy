"""Tests for the Rulebook product: index, kind registry, view-model, CLI."""

import shutil
from pathlib import Path

import pytest
from pydantic import ValidationError

from spf.config import config
from spf.frontends.cli.render import GENERAL_RULES, RenderOpts, render_general_rules
from spf.frontends.cli.rules import list_rulebook
from spf.render import render
from spf.render.formats import get_format
from spf.render.products import PRODUCTS
from spf.render.rulebook import (
    KINDS,
    MARKDOWN,
    Rulebook,
    Section,
    SectionKind,
    build_rulebook,
    get_kind,
    parse_markdown,
    register_kind,
)
from spf.rules import get_rulebook
from spf.schemas.rulebook import RulebookConfig, SectionConfig
from tests.conftest import unwrapped

ENGINE = config.render.latex.engine

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
    kind = SectionKind(name="_probe", parse=lambda path: path.read_text())
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


# --- The markdown kind's parser ---------------------------------------------


def test_markdown_kind_drops_h1_lines(tmp_path: Path) -> None:
    source = tmp_path / "round.md"
    source.write_text("# The Round\n\nBody text.\n\n## Phases\n", encoding="utf-8")

    body = parse_markdown(source)

    assert "# The Round" not in body
    assert "Body text." in body
    assert "## Phases" in body


def test_markdown_kind_keeps_a_hash_that_is_not_a_heading(tmp_path: Path) -> None:
    source = tmp_path / "round.md"
    source.write_text("Roll #1 on the table.\n", encoding="utf-8")

    assert parse_markdown(source) == "Roll #1 on the table.\n"


# --- build_rulebook ---------------------------------------------------------


def _index(*sections: SectionConfig, title: str = "Test Rulebook") -> RulebookConfig:
    return RulebookConfig(title=title, sections=list(sections))


def _section(
    *, kind: str = "markdown", source: str = "round.md", title: str = "The Round"
) -> SectionConfig:
    return SectionConfig(kind=kind, source=source, title=title)


def _rules_dir(tmp_path: Path, **files: str) -> Path:
    tmp_path.mkdir(parents=True, exist_ok=True)
    for name, text in files.items():
        (tmp_path / name.replace("_", ".")).write_text(text, encoding="utf-8")
    return tmp_path


def test_build_rulebook_builds_a_section_per_index_entry(tmp_path: Path) -> None:
    rules_dir = _rules_dir(
        tmp_path, round_md="# Dropped\n\nBody.\n", setup_md="Setup.\n"
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
    rules_dir = _rules_dir(tmp_path, round_md="Body.\n")

    rulebook = build_rulebook(
        _index(_section(title="Fire & Movement, Part 2")), rules_dir=rules_dir
    )

    (section,) = rulebook.sections
    assert section.anchor == "fire-movement-part-2"


def test_build_rulebook_gives_duplicate_titles_distinct_anchors(tmp_path: Path) -> None:
    # Two same-named sections would otherwise both answer to `#the-round`, and
    # every link to the second would land on the first.
    rules_dir = _rules_dir(tmp_path, round_md="Body.\n", setup_md="More.\n")

    rulebook = build_rulebook(
        _index(_section(), _section(source="setup.md")), rules_dir=rules_dir
    )

    first, second = rulebook.sections
    assert first.anchor != second.anchor


def test_build_rulebook_rejects_an_unknown_kind_by_position(tmp_path: Path) -> None:
    rules_dir = _rules_dir(tmp_path, round_md="Body.\n")

    with pytest.raises(
        ValueError, match=r"section 2: Unknown kind 'orders'"
    ) as excinfo:
        build_rulebook(
            _index(_section(), _section(kind="orders", source="round.md")),
            rules_dir=rules_dir,
        )

    assert "known kinds:" in str(excinfo.value)


def test_build_rulebook_rejects_a_missing_source_by_position(tmp_path: Path) -> None:
    rules_dir = _rules_dir(tmp_path)

    with pytest.raises(FileNotFoundError) as excinfo:
        build_rulebook(_index(_section(source="absent.md")), rules_dir=rules_dir)

    message = str(excinfo.value)
    assert "section 1" in message
    assert "absent.md" in message


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
    rules_dir = _rules_dir(tmp_path / "rules", round_md=_SOURCE)
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


@pytest.mark.skipif(shutil.which(ENGINE) is None, reason=f"{ENGINE} not installed")
def test_render_the_committed_rulebook_compiles_to_pdf(tmp_path: Path) -> None:
    # The real index over the real sources: the check that authored rules prose
    # actually survives the converter and the engine.
    real = build_rulebook(get_rulebook(), rules_dir=config.paths.rules)

    out = render(
        GENERAL_RULES,
        real,
        fmt=get_format("pdf"),
        name="rulebook",
        output_root=tmp_path,
    )

    assert out.stat().st_size > 0


# --- The CLI ----------------------------------------------------------------


def test_cli_writes_the_rulebook(tmp_path: Path) -> None:
    out = tmp_path / "rulebook.md"

    render_general_rules(opts=RenderOpts(format="markdown", out=out))

    assert "SteamPunkFantasy Rulebook" in out.read_text(encoding="utf-8")


def test_cli_honours_an_alternate_index(tmp_path: Path) -> None:
    _rules_dir(tmp_path, round_md=_SOURCE)
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


def test_rules_rulebook_lists_the_committed_sections(
    capsys: pytest.CaptureFixture[str],
) -> None:
    # What `just validate` runs: resolving the Index is what validates it.
    list_rulebook()

    out = unwrapped(capsys.readouterr().out)
    assert "SteamPunkFantasy Rulebook" in out
    assert "1. The Round (markdown)" in out
