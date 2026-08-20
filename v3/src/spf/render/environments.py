r"""Jinja2 environments, one per template family.

The Markdown environment uses stock delimiters; the LaTeX environment uses
`\\VAR{}` / `\\BLOCK{}` so template markup does not clash with LaTeX's own
braces. Neither environment HTML-escapes: Markdown templates emit Markdown (any
escaping happens later in `spf.render.derivations.md_to_html`) and LaTeX
templates emit LaTeX. The factory takes an injectable `templates_root` so tests
can point it at fixture templates.
"""

from pathlib import Path, PurePath

from jinja2 import Environment, FileSystemLoader

from spf.config import config
from spf.render.formats import Family
from spf.render.latex_text import latex_escape
from spf.render.md_latex import md_to_latex, shift_headings
from spf.version import spf_version


def posix_path(value: PurePath | str) -> str:
    r"""Return `value` with forward slashes, whatever the platform separator is.

    A native-Windows path is backslash-separated, and a backslash means
    something else in both output languages: it opens a control sequence in
    LaTeX (`C:\repo` compiles as `\r`) and escapes punctuation in CommonMark
    (`..\..` renders as `....`). Forward slashes are accepted by LaTeX engines
    and browsers on Windows too, so they are what both families emit.
    """
    return PurePath(value).as_posix()


def relative_to(value: PurePath, start: PurePath) -> str:
    """Return `value` as a path relative to the directory `start`.

    Markdown documents reference art relatively rather than absolutely, because
    a root-absolute path resolves against the *authority* of a `file://` URL:
    opened across a UNC boundary — `file://wsl.localhost/<distro>/…` — it drops
    the share name and the image 404s (ADR 0017). LaTeX keeps absolute paths,
    since it compiles in a temporary directory.

    `walk_up=True` because the two paths are siblings: the result has to be
    able to climb with `..`.
    """
    return posix_path(value.relative_to(start, walk_up=True))


def make_environments(templates_root: Path | None = None) -> dict[Family, Environment]:
    """Build the per-family Jinja2 environments.

    `templates_root` defaults to `config.paths.templates` but may be
    overridden. Each family loads from `templates_root/<family>/`.
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
    latex.filters["posix_path"] = posix_path
    # Markdown that arrives inside the *data* — free-text Rulebook Sections and
    # prose fields in the rules TOML — has no authored per-family form, so each
    # family converts it on the way out (ADR 0005 addendum).
    latex.filters["md_to_latex"] = md_to_latex
    markdown = Environment(
        loader=FileSystemLoader(root / "markdown"),
        autoescape=False,  # noqa: S701  templates emit Markdown/LaTeX, not HTML (ADR 0005)
        keep_trailing_newline=True,
    )
    markdown.filters["relative_to"] = relative_to
    # The Markdown family needs no conversion — its data is already Markdown —
    # only the source's headings pushed below the one it renders under.
    markdown.filters["shift_headings"] = shift_headings
    # A global rather than render context: every document stamps the version it
    # was rendered by, and no render call site should have to thread it through.
    version = spf_version()
    latex.globals["spf_version"] = version
    markdown.globals["spf_version"] = version
    return {"markdown": markdown, "latex": latex}
