"""Tests for the changelog pre-commit hook's pure logic."""

from hooks.check_changelog import missing_changelogs


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
