"""Tests for the LaTeX-template package scanner.

`packages_in_text` takes a plain string, so these exercise it directly rather
than writing template fixtures to disk.
"""

from pathlib import Path

from spf.lint import latex


def test_finds_usepackage_names() -> None:
    r"""A plain \usepackage line yields its package name."""
    text = r"\usepackage{graphicx}"

    assert latex.packages_in_text(text) == {"graphicx"}


def test_finds_usepackage_with_options() -> None:
    """Bracketed options before the package name are ignored."""
    text = r"\usepackage[margin=2cm]{geometry}"

    assert latex.packages_in_text(text) == {"geometry"}


def test_splits_comma_separated_package_list() -> None:
    r"""A single \usepackage line naming several packages yields all of them."""
    text = r"\usepackage{textcomp,graphicx}"

    assert latex.packages_in_text(text) == {"textcomp", "graphicx"}


def test_finds_documentclass_name() -> None:
    r"""\documentclass is scanned the same way as \usepackage."""
    text = r"\documentclass[frontgrid,backgrid,a4paper,12pt]{flacards}"

    assert latex.packages_in_text(text) == {"flacards"}


def test_ignores_article_documentclass() -> None:
    """The base `article` class is not a manifest dependency."""
    text = r"\documentclass[a4paper,12pt]{article}"

    assert latex.packages_in_text(text) == set()


def test_ignores_commented_lines() -> None:
    r"""A \usepackage line inside a comment is not a real dependency."""
    text = "% \\usepackage{graphicx}\n\\usepackage{parskip}"

    assert latex.packages_in_text(text) == {"parskip"}


def test_packages_in_templates_scans_every_tex_jinja_file(tmp_path: Path) -> None:
    """The directory walk unions packages across every `*.tex.jinja` file."""
    (tmp_path / "a").mkdir()
    (tmp_path / "a" / "main.tex.jinja").write_text(r"\usepackage{fancyhdr}")
    (tmp_path / "b").mkdir()
    (tmp_path / "b" / "main.tex.jinja").write_text(r"\usepackage{graphicx}")
    (tmp_path / "b" / "notes.md").write_text(r"\usepackage{ignored}")

    assert latex.packages_in_templates(tmp_path) == {"fancyhdr", "graphicx"}


def test_read_manifest_strips_comments_and_blank_lines(tmp_path: Path) -> None:
    """A manifest entry may carry a trailing `#` comment; blanks are skipped."""
    manifest = tmp_path / "requirements.txt"
    manifest.write_text("graphicx  # for images\n\nfancyhdr\n")

    assert latex.read_manifest(manifest) == {"graphicx", "fancyhdr"}


def test_unlisted_packages_reports_only_missing_ones(tmp_path: Path) -> None:
    """A package used by a template but absent from the manifest is reported."""
    templates_dir = tmp_path / "latex"
    templates_dir.mkdir()
    (templates_dir / "main.tex.jinja").write_text(
        "\\usepackage{graphicx}\n\\usepackage{unlisted}\n"
    )
    manifest_path = templates_dir / "requirements.txt"
    manifest_path.write_text("graphicx\n")

    assert latex.unlisted_packages(templates_dir, manifest_path) == ["unlisted"]


def test_unlisted_packages_empty_when_manifest_covers_everything(
    tmp_path: Path,
) -> None:
    """A fully-covered set of templates reports no findings."""
    templates_dir = tmp_path / "latex"
    templates_dir.mkdir()
    (templates_dir / "main.tex.jinja").write_text(r"\usepackage{graphicx}")
    manifest_path = templates_dir / "requirements.txt"
    manifest_path.write_text("graphicx\n")

    assert latex.unlisted_packages(templates_dir, manifest_path) == []
