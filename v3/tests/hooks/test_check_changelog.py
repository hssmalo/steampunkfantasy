"""Tests for the changelog pre-commit hook's pure logic."""

from hooks.check_changelog import missing_changelogs


def test_modified_race_toml_without_changelog_is_flagged() -> None:
    result = missing_changelogs(
        modified={"races/elf.toml"},
        staged={"races/elf.toml"},
    )
    assert result == [("races/elf.toml", "races/changelog.md")]
