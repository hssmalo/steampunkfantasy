"""Render every document on demand, and diff a re-render against that snapshot.

A golden is a refactoring tool, not a fixture (`docs/agents/testing.md`,
ADR 0033): it is worth exactly one thing, proving a change altered no output.
So none are committed. `snapshot` writes the current working tree's output into
the gitignored `goldens/`, and `diff` re-renders and reports what moved.

Every Product goes through the same entry points `spf render` does, in the two
text Formats — Markdown and LaTeX. The binary Formats derive from those, and a
PDF stamps a build time that would differ on every run.
"""

import argparse
import contextlib
import difflib
import io
import shutil
import sys
import tempfile
from collections.abc import Callable, Iterator
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, cast

from spf.config import config
from spf.frontends.cli.render import (
    RULEBOOK_STEM,
    RenderOpts,
    render_army_pack,
    render_army_rules,
    render_cards,
    render_general_rules,
    render_race_overview,
    safe_stem,
)
from spf.render.formats import get_format

if TYPE_CHECKING:
    from spf.schemas import type_aliases as t

V3 = Path(__file__).resolve().parent.parent
GOLDENS = V3 / "goldens"

FORMATS = ("markdown", "latex")

FORMAT_LABELS = {"markdown": "Markdown", "latex": "LaTeX"}
"""How each Format is spelled in a report a human reads."""

WORK_PREFIX = ".goldens-"
"""Names the throwaway tree `diff` renders into; gitignored alongside them."""

MAX_DIFF_LINES = 25
"""Lines of any one file's diff to print before saying how many were left."""

MAX_RUN_DIFF_LINES = 100
"""Diff lines to print across a whole run before naming the files left out.

A per-file cap alone still lets a template edit, which moves every document,
print the entire corpus.
"""

DIFF_CONTEXT = 0
"""Unchanged lines to keep around each hunk.

None: the hunk header gives the line number and a rendered line names its own
Special, so context only spends the budget the changed lines want.
"""


@dataclass
class Tally:
    """What one report accumulated as it walked the two rendered trees.

    Counts only what the run had something to say about: files whose diff was
    printed, and those it declined to print.
    """

    files: int = 0
    hunks: int = 0
    changed: int = 0
    elided: int = 0
    """Files that moved in a Format whose diffs were not asked for."""
    withheld: int = 0
    """Files that moved after the run's line budget was spent."""


@dataclass(frozen=True)
class Document:
    """One document to render: which Product, under which stem."""

    product: str
    stem: str
    render: Callable[[RenderOpts], None]
    """The `spf render` function, already bound to its subject."""


def documents() -> Iterator[Document]:
    """Every document the committed corpus renders to, in a stable order.

    The Rulebook, one Race Overview per Race file, an Army Reference and an
    Order Card deck per Army, and one Army Pack per authored Pack Index.
    """
    yield Document(
        "general-rules",
        RULEBOOK_STEM,
        lambda opts: render_general_rules(opts=opts),
    )
    for race_file in sorted(config.paths.races.glob("*.toml")):
        race = race_file.stem
        yield Document(
            "race-overview",
            race,
            lambda opts, race=race: render_race_overview(
                # A `RaceName` is a closed set of strings; a Race file is named
                # for the Race it holds, so its stem is one of them.
                cast("t.RaceName", race),
                opts=opts,
            ),
        )
    for name in _army_names():
        stem = safe_stem(name)
        yield Document(
            "army-rules",
            stem,
            lambda opts, name=name: render_army_rules(name, opts=opts),
        )
        yield Document(
            "cards", stem, lambda opts, name=name: render_cards(name, opts=opts)
        )
    for index in _pack_indexes():
        yield Document(
            "army-pack",
            safe_stem(index.parent.name),
            lambda opts, index=index: render_army_pack(index=index, opts=opts),
        )


def _army_names() -> list[str]:
    """Name every committed Army the way its load name spells it."""
    armies = config.paths.armies
    return sorted(
        str(path.relative_to(armies).with_suffix("")) for path in armies.rglob("*.json")
    )


def _pack_indexes() -> list[Path]:
    """Find every Army Pack Index, whether or not the Site Index names it."""
    return sorted(config.paths.armies.rglob("pack.toml"))


def render_all(into: Path) -> int:
    """Render every document into `into`, and return how many files were written.

    Output lands at `into/<product>/<stem>.<extension>`, the layout
    `spf render` writes under `output/`.
    """
    written = 0
    for document in documents():
        for format_name in FORMATS:
            fmt = get_format(format_name)
            out = into / document.product / f"{document.stem}.{fmt.extension}"
            opts = RenderOpts(format=format_name, out=out)
            # `spf render` reports every file it writes; here the count is the
            # only interesting part of that.
            with contextlib.redirect_stdout(io.StringIO()):
                document.render(opts)
            written += 1
    return written


def snapshot() -> int:
    """Replace `goldens/` with a fresh render of the working tree."""
    if GOLDENS.exists():
        shutil.rmtree(GOLDENS)
    written = render_all(GOLDENS)
    _say(f"Snapshotted {written} files into {GOLDENS.relative_to(V3)}/")
    return 0


def diff(shown: tuple[str, ...] = (FORMATS[0],)) -> int:
    """Re-render and report every file that differs from the snapshot.

    Every Format is always compared, so the verdict is honest; `shown` only
    selects whose diffs are worth reading.
    """
    if not GOLDENS.is_dir():
        _say(f"No snapshot at {GOLDENS}: run `just golden-snapshot` first")
        return 1

    # Beside `goldens/`, not in the system temp directory: a document links its
    # Images by a path relative to where it was written, so a re-render only
    # compares equal from the same depth in the tree.
    work = tempfile.mkdtemp(prefix=WORK_PREFIX, dir=V3)
    try:
        current = Path(work)
        rendered = render_all(current)
        differing = _report(GOLDENS, current, shown=shown)
    finally:
        shutil.rmtree(work, ignore_errors=True)

    if differing:
        _say(f"\n{differing} of {rendered} files differ from the snapshot")
        return 1
    _say(f"No differences: {rendered} files match the snapshot")
    return 0


def _report(
    baseline: Path, current: Path, shown: tuple[str, ...] = (FORMATS[0],)
) -> int:
    """Print what moved between two rendered trees, and count the files.

    Only the `shown` Formats have their diffs printed; the rest are counted and
    named. A document that vanished or appeared is structural news, so it is
    reported whatever its Format.
    """
    extensions = {get_format(name).extension for name in shown}
    tally = Tally()
    differing = 0
    spent = 0
    for relative in sorted(_paths(baseline) | _paths(current)):
        before = baseline / relative
        after = current / relative
        if not after.exists():
            _say(f"--- {relative}: no longer rendered")
            spent += 1
        elif not before.exists():
            _say(f"+++ {relative}: newly rendered")
            spent += 1
        elif before.read_bytes() != after.read_bytes():
            if relative.suffix.lstrip(".") not in extensions:
                tally.elided += 1
            elif spent >= MAX_RUN_DIFF_LINES:
                tally.withheld += 1
            else:
                lines = _diff_lines(relative, before, after)
                tally.files += 1
                tally.hunks += sum(1 for line in lines if line.startswith("@@"))
                tally.changed += sum(1 for line in lines[2:] if line[:1] in "+-")
                spent += _print_diff(lines)
        else:
            continue
        differing += 1
    if differing:
        _print_summary(tally, shown)
    return differing


def _print_summary(tally: "Tally", shown: tuple[str, ...]) -> None:
    """Print the counts line that fronts a diff pasted into an issue."""
    # Naming the Format only reads right when there is one of them to name.
    label = f"{FORMAT_LABELS[shown[0]]} " if len(shown) == 1 else ""
    summary = (
        f"\n**{_count(tally.files, f'{label}file')}, {_count(tally.hunks, 'hunk')}, "
        f"{_count(tally.changed, 'changed line')}**"
    )
    if tally.elided:
        others = ", ".join(FORMAT_LABELS[name] for name in FORMATS if name not in shown)
        summary += f" ({_count(tally.elided, f'{others} file')} elided)"
    _say(summary)
    if tally.withheld:
        _say(f"... {tally.withheld} further files differ, not shown")


def _count(number: int, noun: str) -> str:
    """Say how many of `noun` there are, pluralising the noun to match."""
    return f"{number} {noun}" if number == 1 else f"{number} {noun}s"


def _paths(root: Path) -> set[Path]:
    """Every file under `root`, relative to it."""
    return {path.relative_to(root) for path in root.rglob("*") if path.is_file()}


def _print_diff(lines: list[str]) -> int:
    """Print one file's diff, truncated to stay readable.

    Returns the lines printed, so the caller can spend down the run budget.
    """
    shown = lines[:MAX_DIFF_LINES]
    _say("\n".join(shown))
    if len(lines) > MAX_DIFF_LINES:
        _say(f"... {len(lines) - MAX_DIFF_LINES} more diff lines")
    _say("")
    return len(shown)


def _diff_lines(relative: Path, before: Path, after: Path) -> list[str]:
    """Diff one file, dropping the unchanged context lines around each hunk."""
    return list(
        difflib.unified_diff(
            before.read_text(encoding="utf-8").splitlines(),
            after.read_text(encoding="utf-8").splitlines(),
            fromfile=f"snapshot/{relative}",
            tofile=f"current/{relative}",
            n=DIFF_CONTEXT,
            lineterm="",
        )
    )


def _say(message: str) -> None:
    """Write one line, flushed so a long run reads as it goes."""
    sys.stdout.write(f"{message}\n")
    sys.stdout.flush()


def main(argv: list[str] | None = None) -> int:
    """Run the requested command."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "command",
        choices=("snapshot", "diff"),
        help="snapshot: render into goldens/. diff: re-render and compare.",
    )
    parser.add_argument(
        "--format",
        choices=(*FORMATS, "all"),
        default=FORMATS[0],
        help="Whose diffs to print. Every Format is compared either way.",
    )
    args = parser.parse_args(argv)
    if args.command == "snapshot":
        return snapshot()
    shown = FORMATS if args.format == "all" else (args.format,)
    return diff(shown)


if __name__ == "__main__":
    sys.exit(main())
