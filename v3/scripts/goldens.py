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


def diff() -> int:
    """Re-render and report every file that differs from the snapshot."""
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
        differing = _report(GOLDENS, current)
    finally:
        shutil.rmtree(work, ignore_errors=True)

    if differing:
        _say(f"\n{differing} of {rendered} files differ from the snapshot")
        return 1
    _say(f"No differences: {rendered} files match the snapshot")
    return 0


def _report(baseline: Path, current: Path) -> int:
    """Print what moved between two rendered trees, and count the files."""
    differing = 0
    spent = 0
    withheld = 0
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
            if spent >= MAX_RUN_DIFF_LINES:
                withheld += 1
            else:
                spent += _print_diff(relative, before, after)
        else:
            continue
        differing += 1
    if withheld:
        _say(f"... {withheld} further files differ, not shown")
    return differing


def _paths(root: Path) -> set[Path]:
    """Every file under `root`, relative to it."""
    return {path.relative_to(root) for path in root.rglob("*") if path.is_file()}


def _print_diff(relative: Path, before: Path, after: Path) -> int:
    """Print a unified diff of one file, truncated to stay readable.

    Returns the lines printed, so the caller can spend down the run budget.
    """
    lines = _diff_lines(relative, before, after)
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
    args = parser.parse_args(argv)
    return snapshot() if args.command == "snapshot" else diff()


if __name__ == "__main__":
    sys.exit(main())
