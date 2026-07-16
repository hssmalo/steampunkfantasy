"""Format derivations: post-render steps that transform rendered text.

A derivation takes the text produced by a template and turns it into the final
content for its Format: Markdown into a standalone HTML document, or LaTeX into a
compiled PDF. Each formatting rule lives here in exactly one place.
"""

import shutil
import subprocess
import tempfile
from pathlib import Path

from markdown_it import MarkdownIt

from spf.config import config

_LOG_TAIL_LINES = 30

_HTML_DOCUMENT = """\
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>SteamPunkFantasy</title>
<style>
body {{ font-family: system-ui, sans-serif; margin: 2rem auto; max-width: 48rem; }}
table {{ border-collapse: collapse; }}
th, td {{ border: 1px solid #ccc; padding: 0.25rem 0.5rem; }}
</style>
</head>
<body>
{body}</body>
</html>
"""


class RenderError(Exception):
    """Raised when a derivation cannot produce its output."""


def md_to_html(text: str) -> str:
    """Convert Markdown text into a standalone HTML5 document.

    Tables are enabled and the rendered fragment is wrapped in a minimal
    document (doctype, charset, title, embedded stylesheet) so the `.html` is
    double-clickable.
    """
    markdown = MarkdownIt("commonmark").enable("table")
    body = markdown.render(text)
    return _HTML_DOCUMENT.format(body=body)


def latex_to_pdf(text: str) -> bytes:
    """Compile LaTeX text to PDF and return the PDF bytes.

    Compilation runs the configured engine twice in a temporary directory with
    `-interaction=nonstopmode -halt-on-error` so cross-references and page
    numbers stabilize. Only the resulting `.pdf` is read back out; every
    transient file stays inside the temporary directory.
    """
    engine = config.render.latex.engine
    if shutil.which(engine) is None:
        msg = (
            f"LaTeX engine {engine!r} was not found on PATH. "
            "Only the 'pdf' format requires it; install a LaTeX distribution "
            "or configure another engine under [render.latex]."
        )
        raise RenderError(msg)

    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        (tmp_path / "main.tex").write_text(text, encoding="utf-8")
        for _ in range(2):
            result = subprocess.run(  # noqa: S603
                [
                    engine,
                    "-interaction=nonstopmode",
                    "-halt-on-error",
                    "main.tex",
                ],
                cwd=tmp_path,
                capture_output=True,
                text=True,
                check=False,
            )
            if result.returncode != 0:
                raise RenderError(_compile_error(engine, tmp_path, result.stdout))
        return (tmp_path / "main.pdf").read_bytes()


def _compile_error(engine: str, tmp_path: Path, stdout: str) -> str:
    """Build a compile-failure message ending with the tail of the engine log."""
    log_path = tmp_path / "main.log"
    log = (
        log_path.read_text(encoding="utf-8", errors="replace")
        if log_path.exists()
        else stdout
    )
    tail = "\n".join(log.splitlines()[-_LOG_TAIL_LINES:])
    return f"{engine} failed to compile the document:\n{tail}"
