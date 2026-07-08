r"""Jinja2 environments, one per template family.

The Markdown environment uses stock delimiters; the LaTeX environment uses
``\\VAR{}`` / ``\\BLOCK{}`` so template markup does not clash with LaTeX's own
braces. Neither environment HTML-escapes: Markdown templates emit Markdown (any
escaping happens later in :func:`spf.render.derivations.md_to_html`) and LaTeX
templates emit LaTeX. The factory takes an injectable ``templates_root`` so tests
can point it at fixture templates.
"""

from pathlib import Path

from jinja2 import Environment, FileSystemLoader

from spf.config import config
from spf.render.formats import Family

# Characters that must be escaped to survive a pdflatex run. Order cells carry
# ``°`` (rendered via ``textcomp``'s ``\textdegree``) alongside the usual TeX
# specials; ``+``, ``[`` and ``]`` are safe in text mode and pass through.
_LATEX_SPECIAL = {
    "\\": r"\textbackslash{}",
    "&": r"\&",
    "%": r"\%",
    "$": r"\$",
    "#": r"\#",
    "_": r"\_",
    "{": r"\{",
    "}": r"\}",
    "~": r"\textasciitilde{}",
    "^": r"\textasciicircum{}",
    "°": r"\textdegree{}",
}


def latex_escape(value: object) -> str:
    """Escape LaTeX-special characters in ``value`` for safe text-mode output."""
    return "".join(_LATEX_SPECIAL.get(char, char) for char in str(value))


def make_environments(templates_root: Path | None = None) -> dict[Family, Environment]:
    """Build the per-family Jinja2 environments.

    ``templates_root`` defaults to ``config.paths.templates`` but may be
    overridden. Each family loads from ``templates_root/<family>/``.
    """
    root = templates_root if templates_root is not None else config.paths.templates
    latex = Environment(
        loader=FileSystemLoader(root / "latex"),
        variable_start_string=r"\VAR{",
        variable_end_string="}",
        block_start_string=r"\BLOCK{",
        block_end_string="}",
        autoescape=False,  # noqa: S701  templates emit Markdown/LaTeX, not HTML (ADR 0005)
        trim_blocks=True,
        lstrip_blocks=True,
        keep_trailing_newline=True,
    )
    latex.filters["latex_escape"] = latex_escape
    return {
        "markdown": Environment(
            loader=FileSystemLoader(root / "markdown"),
            autoescape=False,  # noqa: S701  templates emit Markdown/LaTeX, not HTML (ADR 0005)
            keep_trailing_newline=True,
        ),
        "latex": latex,
    }
