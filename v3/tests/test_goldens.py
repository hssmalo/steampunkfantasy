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


def test_a_document_that_stopped_rendering_is_reported(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    baseline = _tree(tmp_path / "before", {"cards/demo.md": "# Cards\n"})
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
