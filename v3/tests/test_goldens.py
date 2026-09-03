"""Tests for the comparison behind `just golden-diff`.

Two rendered trees in, a count of what moved out: these never render a
document and never touch `goldens/`.
"""

from pathlib import Path

import pytest

import goldens


def _tree(root: Path, files: dict[str, str]) -> Path:
    """Write a rendered tree of `path: content` and return its root."""
    for name, content in files.items():
        path = root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
    return root


def _both_formats(tmp_path: Path) -> tuple[Path, Path]:
    """Build two trees where one document moved in both Formats."""
    before = {"race-overview/demo.md": "old\n", "race-overview/demo.tex": "old\n"}
    after = {"race-overview/demo.md": "new\n", "race-overview/demo.tex": "new\n"}
    return _tree(tmp_path / "before", before), _tree(tmp_path / "after", after)


def test_an_unchanged_tree_reports_nothing(tmp_path: Path) -> None:
    files = {"army-rules/demo.md": "# Demo\n", "cards/demo.md": "# Cards\n"}
    baseline = _tree(tmp_path / "before", files)
    current = _tree(tmp_path / "after", files)

    assert goldens._report(baseline, current) == 0


def test_a_changed_line_is_reported_with_its_diff(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    baseline = _tree(
        tmp_path / "before", {"army-rules/demo.md": "# Demo — 12 points\n"}
    )
    current = _tree(tmp_path / "after", {"army-rules/demo.md": "# Demo — 12 pts\n"})

    assert goldens._report(baseline, current) == 1

    printed = capsys.readouterr().out
    assert "-# Demo — 12 points" in printed
    assert "+# Demo — 12 pts" in printed


def test_a_long_diff_is_truncated(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    # A refactor that moved everything would otherwise bury the summary line
    # under every document in the corpus.
    lines = goldens.MAX_DIFF_LINES * 2
    baseline = _tree(tmp_path / "before", {"cards/demo.md": "old\n" * lines})
    current = _tree(tmp_path / "after", {"cards/demo.md": "new\n" * lines})

    goldens._report(baseline, current)

    printed = capsys.readouterr().out
    assert "more diff lines" in printed
    assert len(printed.splitlines()) < lines


def test_a_diff_carries_no_context_lines(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    # The hunk header locates the change; the surrounding prose only spends the
    # line budget that the changed lines want.
    before = "Kept above\nFire two shots per fire order\nKept below\n"
    after = "Kept above\nFires 2 shots per fire order\nKept below\n"
    baseline = _tree(tmp_path / "before", {"race-overview/demo.md": before})
    current = _tree(tmp_path / "after", {"race-overview/demo.md": after})

    goldens._report(baseline, current)

    printed = capsys.readouterr().out
    assert "-Fire two shots per fire order" in printed
    assert "+Fires 2 shots per fire order" in printed
    assert "Kept above" not in printed
    assert "Kept below" not in printed


def test_the_run_budget_bounds_a_broad_change(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    # A template edit moves every document at once; a per-file cap alone would
    # still let the run print the whole corpus.
    files = {f"race-overview/demo{index}.md": "old\n" * 20 for index in range(40)}
    moved = {name: content.replace("old", "new") for name, content in files.items()}
    baseline = _tree(tmp_path / "before", files)
    current = _tree(tmp_path / "after", moved)

    assert goldens._report(baseline, current) == len(files)

    printed = capsys.readouterr().out
    assert "further files differ" in printed
    assert len(printed.splitlines()) < goldens.MAX_RUN_DIFF_LINES * 2


def test_latex_diffs_are_counted_but_not_shown_by_default(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    # Both Formats render the same view model, so for a prose edit the LaTeX
    # diff is the same change in a noisier notation.
    baseline, current = _both_formats(tmp_path)

    assert goldens._report(baseline, current) == 2

    printed = capsys.readouterr().out
    assert "demo.md" in printed
    assert "-old" in printed
    assert "demo.tex" not in printed
    assert "1 LaTeX file elided" in printed


def test_a_named_format_is_shown(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    baseline, current = _both_formats(tmp_path)

    goldens._report(baseline, current, shown=("latex",))

    printed = capsys.readouterr().out
    assert "demo.tex" in printed
    assert "demo.md" not in printed
    assert "1 Markdown file elided" in printed


def test_every_format_can_be_shown_at_once(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    baseline, current = _both_formats(tmp_path)

    goldens._report(baseline, current, shown=goldens.FORMATS)

    printed = capsys.readouterr().out
    assert "demo.md" in printed
    assert "demo.tex" in printed
    assert "elided" not in printed


def test_the_summary_counts_hunks_and_changed_lines(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    # The counts line fronts a diff pasted into an issue, so it has to be right
    # about how much of the document moved.
    body = [f"line {index}" for index in range(10)]
    moved = list(body)
    moved[0] = "first moved"
    moved[9] = "last moved"
    baseline = _tree(tmp_path / "before", {"cards/demo.md": "\n".join(body) + "\n"})
    current = _tree(tmp_path / "after", {"cards/demo.md": "\n".join(moved) + "\n"})

    goldens._report(baseline, current)

    assert "**1 Markdown file, 2 hunks, 4 changed lines**" in capsys.readouterr().out


def test_a_document_that_stopped_rendering_is_reported(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    baseline = _tree(tmp_path / "before", {"cards/demo.md": "# Cards\n"})
    current = _tree(tmp_path / "after", {})

    assert goldens._report(baseline, current) == 1
    assert "no longer rendered" in capsys.readouterr().out


def test_a_vanished_document_is_reported_whatever_its_format(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    # A Format filter hides prose that moved, never a document that vanished.
    baseline = _tree(tmp_path / "before", {"cards/demo.tex": "# Cards\n"})
    current = _tree(tmp_path / "after", {})

    assert goldens._report(baseline, current) == 1
    assert "no longer rendered" in capsys.readouterr().out


def test_a_newly_rendered_document_is_reported(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    baseline = _tree(tmp_path / "before", {})
    current = _tree(tmp_path / "after", {"cards/demo.md": "# Cards\n"})

    assert goldens._report(baseline, current) == 1
    assert "newly rendered" in capsys.readouterr().out


def test_the_baseline_stamp_is_not_compared_as_a_document(tmp_path: Path) -> None:
    # The stamp lives in the snapshot so that discarding one discards both.
    baseline = _tree(tmp_path / "before", {"cards/demo.md": "# Cards\n"})
    current = _tree(tmp_path / "after", {"cards/demo.md": "# Cards\n"})
    (baseline / goldens.BASELINE).write_text('{"commit": "abc"}', encoding="utf-8")

    assert goldens._report(baseline, current) == 0


def test_a_matching_stamp_says_nothing() -> None:
    stamp = {"commit": "a" * 40, "dirty": False}

    assert goldens._baseline_warnings(stamp, "a" * 40) == []


def test_a_snapshot_taken_at_another_commit_warns() -> None:
    # Committing a reviewed cluster moves HEAD by design, so this is a warning
    # and never a refusal.
    stamp = {"commit": "a" * 40, "dirty": False}

    warnings = goldens._baseline_warnings(stamp, "b" * 40)

    assert len(warnings) == 1
    assert "aaaaaaa" in warnings[0]
    assert "bbbbbbb" in warnings[0]


def test_a_snapshot_taken_over_uncommitted_changes_warns() -> None:
    # Its baseline is a tree that exists in no commit.
    stamp = {"commit": "a" * 40, "dirty": True}

    warnings = goldens._baseline_warnings(stamp, "a" * 40)

    assert len(warnings) == 1
    assert "uncommitted" in warnings[0]


def test_a_snapshot_with_no_stamp_warns() -> None:
    warnings = goldens._baseline_warnings(None, "a" * 40)

    assert len(warnings) == 1
    assert "no baseline stamp" in warnings[0]


def test_a_written_stamp_reads_back(tmp_path: Path) -> None:
    goldens._write_baseline(tmp_path)

    stamp = goldens._read_baseline(tmp_path)

    assert stamp is not None
    assert set(stamp) == {"commit", "dirty"}


def test_an_unreadable_stamp_is_no_stamp(tmp_path: Path) -> None:
    (tmp_path / goldens.BASELINE).write_text("not json", encoding="utf-8")

    assert goldens._read_baseline(tmp_path) is None


def test_accept_retakes_the_snapshot(monkeypatch: pytest.MonkeyPatch) -> None:
    # `accept` is `snapshot` under the name an agent mid-issue will reach for.
    taken = []

    def _snapshot() -> int:
        taken.append("taken")
        return 0

    monkeypatch.setattr(goldens, "snapshot", _snapshot)

    assert goldens.main(["accept"]) == 0
    assert taken == ["taken"]
