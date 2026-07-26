r"""Escaping text for LaTeX's text mode.

Its own module because both consumers need it and they sit on opposite sides of
an import edge: `spf.render.environments` registers it as the `latex_escape`
filter, and `spf.render.md_latex` — which `environments` imports, to register
`md_to_latex` — escapes every text token it emits.
"""

# Characters that must be escaped to survive a pdflatex run. Order cells carry
# `°` (rendered via `textcomp`'s `\textdegree`) alongside the usual TeX
# specials; `+`, `[` and `]` are safe in text mode and pass through.
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
    """Escape LaTeX-special characters in `value` for safe text-mode output."""
    return "".join(_LATEX_SPECIAL.get(char, char) for char in str(value))
