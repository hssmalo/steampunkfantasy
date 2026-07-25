"""Tests for the Rulebook product: index, kind registry, view-model, CLI."""

from pathlib import Path

import pytest
from pydantic import ValidationError

from spf.rules import get_rulebook
from spf.schemas.rulebook import RulebookConfig, SectionConfig

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
