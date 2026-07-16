"""Block a commit when game-data TOML changes without its changelog.

Each game-data directory owns a changelog: ``races/`` is paired with
``races/changelog.md`` and ``rules/`` with ``rules/changelog.md``. Modifying a
TOML in one of those directories requires its changelog to be staged in the
same commit.
"""

import subprocess
import sys
from pathlib import Path

GAME_DATA_DIRS = ("races", "rules")


def missing_changelogs(
    modified: set[str],
    staged: set[str],
) -> list[tuple[str, str]]:
    """Find game-data TOMLs modified without their changelog staged.

    ``modified`` is the set of paths modified in the commit; ``staged`` is the
    set of paths added or modified (so a first-time changelog counts). Returns
    ``(offending_toml, required_changelog)`` pairs, empty when nothing is amiss.
    """
    offending: list[tuple[str, str]] = []
    for directory in GAME_DATA_DIRS:
        changelog = f"{directory}/changelog.md"
        flagged = sorted(
            path for path in modified if _is_game_toml(path, directory)
        )
        if flagged and changelog not in staged:
            offending.extend((path, changelog) for path in flagged)
    return offending


def format_message(offending: list[tuple[str, str]]) -> str:
    """Render the block message for ``(toml, changelog)`` offender pairs."""
    lines = ["Game data changed without a changelog update:", ""]
    lines.extend(
        f"  {toml} -> update {changelog}" for toml, changelog in offending
    )
    lines += [
        "",
        "Record *why* the balance changed in the changelog, then stage it.",
        "To bypass this check, commit with `git commit --no-verify`.",
    ]
    return "\n".join(lines)


def _is_game_toml(path: str, directory: str) -> bool:
    """Return whether ``path`` is a TOML directly inside ``directory``."""
    candidate = Path(path)
    return candidate.parent == Path(directory) and candidate.suffix == ".toml"


def _staged_paths(diff_filter: str) -> set[str]:
    """Return staged paths matching a ``git diff --cached`` diff filter."""
    result = subprocess.run(  # noqa: S603
        ["git", "diff", "--cached", "--name-only", f"--diff-filter={diff_filter}"],  # noqa: S607
        capture_output=True,
        text=True,
        check=True,
    )
    return {line for line in result.stdout.splitlines() if line}


def main() -> int:
    """Block the commit when game data changed without its changelog."""
    modified = _staged_paths("M")  # modify-only trigger
    staged = _staged_paths("ACM")  # add-or-modify satisfies the changelog
    offending = missing_changelogs(modified, staged)
    if offending:
        print(format_message(offending), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
