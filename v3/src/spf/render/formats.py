"""The Format registry.

A :class:`Format` is a target output shape: a file extension, the template
*family* it renders from, and an optional post-step (a derivation) that turns the
rendered text into the final content. Formats are plain records registered in a
module-level dict at import time and looked up by name.
"""

from collections.abc import Callable
from dataclasses import dataclass
from typing import Literal

from spf.render.derivations import latex_to_pdf, md_to_html

type Family = Literal["markdown", "latex"]
type PostStep = Callable[[str], str | bytes]

# The authored-template extension for each family. A Format renders from its
# family's source template (`main.<ext>.jinja`); its own `extension` names only
# the output file. So `html` and `pdf` render from `main.md.jinja` /
# `main.tex.jinja` respectively.
FAMILY_TEMPLATE_EXT: dict[Family, str] = {"markdown": "md", "latex": "tex"}


@dataclass(frozen=True)
class Format:
    """A registered output format."""

    name: str
    extension: str
    family: Family
    post_step: PostStep | None = None


FORMATS: dict[str, Format] = {}


def register_format(fmt: Format) -> Format:
    """Register a Format under its name and return it."""
    FORMATS[fmt.name] = fmt
    return fmt


def get_format(name: str) -> Format:
    """Look up a registered Format by name."""
    try:
        return FORMATS[name]
    except KeyError:
        known = ", ".join(FORMATS) or "(none registered)"
        msg = f"Unknown format {name!r}; known formats: {known}"
        raise ValueError(msg) from None


register_format(Format(name="markdown", extension="md", family="markdown"))
register_format(
    Format(name="html", extension="html", family="markdown", post_step=md_to_html)
)
register_format(Format(name="latex", extension="tex", family="latex"))
register_format(
    Format(name="pdf", extension="pdf", family="latex", post_step=latex_to_pdf)
)
