"""Tests for the changelog pre-commit hook's pure logic."""

import subprocess
from pathlib import Path

import pytest

from hooks.check_changelog import format_message, main, missing_changelogs


def _git(repo: Path, *args: str) -> None:
    subprocess.run(["git", *args], cwd=repo, check=True, capture_output=True)  # noqa: S603, S607


@pytest.fixture
def committed_race_repo(tmp_path: Path) -> Path:
    """Build a git repo with a committed race TOML and its changelog."""
    _git(tmp_path, "init", "-q")
    _git(tmp_path, "config", "user.email", "t@example.com")
    _git(tmp_path, "config", "user.name", "Test")
    (tmp_path / "races").mkdir()
    (tmp_path / "races" / "elf.toml").write_text("name = 'Elf'\n")
    (tmp_path / "races" / "changelog.md").write_text("# Changelog\n")
    _git(tmp_path, "add", "-A")
    _git(tmp_path, "commit", "-qm", "init")
    return tmp_path


def test_modified_race_toml_without_changelog_is_flagged() -> None:
    result = missing_changelogs(
        modified={"races/elf.toml"},
        staged={"races/elf.toml"},
    )
    assert result == [("races/elf.toml", "races/changelog.md")]


def test_modified_race_toml_with_changelog_staged_is_not_flagged() -> None:
    result = missing_changelogs(
        modified={"races/elf.toml"},
        staged={"races/elf.toml", "races/changelog.md"},
    )
    assert result == []


def test_first_time_added_changelog_satisfies() -> None:
    # The changelog is brand new: it is staged (ACM) but was never "modified".
    result = missing_changelogs(
        modified={"races/elf.toml"},
        staged={"races/elf.toml", "races/changelog.md"},
    )
    assert result == []


def test_tooling_toml_is_never_flagged() -> None:
    # Tooling TOML lives outside races/ and rules/, so it is ignored.
    result = missing_changelogs(
        modified={"pyproject.toml", "typos.toml", "configs/spf.toml"},
        staged={"pyproject.toml", "typos.toml", "configs/spf.toml"},
    )
    assert result == []


def test_message_lists_offenders_changelog_and_escape_hatch() -> None:
    message = format_message(
        [
            ("races/elf.toml", "races/changelog.md"),
            ("rules/special.toml", "rules/changelog.md"),
        ]
    )
    # Every offending TOML is named.
    assert "races/elf.toml" in message
    assert "rules/special.toml" in message
    # Each required changelog is named.
    assert "races/changelog.md" in message
    assert "rules/changelog.md" in message
    # The escape hatch is mentioned.
    assert "--no-verify" in message


def test_main_blocks_when_changelog_missing(
    committed_race_repo: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repo = committed_race_repo
    (repo / "races" / "elf.toml").write_text("name = 'Elf'  # buffed\n")
    _git(repo, "add", "races/elf.toml")
    monkeypatch.chdir(repo)

    assert main() == 1


def test_main_passes_when_changelog_staged(
    committed_race_repo: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repo = committed_race_repo
    (repo / "races" / "elf.toml").write_text("name = 'Elf'  # buffed\n")
    (repo / "races" / "changelog.md").write_text("# Changelog\n\nwhy\n")
    _git(repo, "add", "races/elf.toml", "races/changelog.md")
    monkeypatch.chdir(repo)

    assert main() == 0


def test_added_game_toml_is_not_flagged() -> None:
    # A newly added race is staged but not in the modified-only set; adds pass.
    result = missing_changelogs(
        modified=set(),
        staged={"races/troll.toml"},
    )
    assert result == []


def test_rules_flagged_independently_of_satisfied_races() -> None:
    # races changelog is staged (satisfied); rules changelog is not.
    result = missing_changelogs(
        modified={"races/elf.toml", "rules/special.toml"},
        staged={"races/elf.toml", "races/changelog.md", "rules/special.toml"},
    )
    assert result == [("rules/special.toml", "rules/changelog.md")]


def test_races_flagged_independently_of_satisfied_rules() -> None:
    # rules changelog is staged (satisfied); races changelog is not.
    result = missing_changelogs(
        modified={"races/elf.toml", "rules/special.toml"},
        staged={"races/elf.toml", "rules/special.toml", "rules/changelog.md"},
    )
    assert result == [("races/elf.toml", "races/changelog.md")]
