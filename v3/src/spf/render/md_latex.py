r"""Convert Markdown that arrives inside the data into LaTeX.

The Rulebook's free-text Sections and the prose fields inside the rules TOML are
authored as Markdown. They have no per-family authored form — and never will,
which is what keeps this from being the single-source/Pandoc approach ADR 0005
rejected (see that ADR's addendum). Templates stay authored per family; only the
Markdown that arrives *inside the data* is converted here.

Both functions are registered as Jinja filters in `spf.render.environments`:
`md_to_latex` on the LaTeX environment, `shift_headings` on the Markdown one.
A Markdown template needs no conversion — its data is already Markdown — but it
does need the source's headings pushed below the heading the section renders
under.

Headings map one level down from where the source wrote them, because the
section's own title is already a `\section`: H2 becomes `\subsection`, H3
`\subsubsection`, H4 `\paragraph`. An H1 should never arrive (the `markdown`
Section Kind's parser drops them) and degrades to `\subsection` rather than
raising.

**Known limitations**, all deliberate for this first cut:

- Tables are not converted. The parser runs stock `commonmark`, which has no
  table rule at all (unlike `md_to_html`, which enables one), so a pipe table
  arrives as ordinary paragraph text and prints with its pipes and dashes
  intact.
- Images are dropped entirely.
- A link renders its text; the URL is discarded, so no `hyperref` dependency.
- Block quotes lose their quoting and flow as ordinary paragraphs.
- **Raw LaTeX in a Markdown source is escaped, not passed through** —
  markdown-it reads `\pagebreak` as text and `latex_escape` turns the backslash
  into `\textbackslash{}`. Do not put raw LaTeX in a rules Markdown file. A
  passthrough escape hatch is future work.

Anything else unsupported degrades to escaped text; nothing here raises.
"""

import re

from markdown_it import MarkdownIt
from markdown_it.token import Token

from spf.render.latex_text import latex_escape

# Heading level -> LaTeX sectioning command, one step below the `\section` the
# Rulebook template emits for the Section's own title.
_HEADINGS = {
    1: r"\subsection",
    2: r"\subsection",
    3: r"\subsubsection",
    4: r"\paragraph",
    5: r"\subparagraph",
    6: r"\subparagraph",
}

_LISTS = {"bullet_list": "itemize", "ordered_list": "enumerate"}

# Inline tokens that wrap their children in a single LaTeX command.
_WRAPPERS = {"strong": r"\textbf", "em": r"\textit"}

_ATX_HEADING = re.compile(r"^(#{1,6})(\s|$)")
_FENCE = re.compile(r"^\s*(```|~~~)")

_MAX_HEADING = 6


def md_to_latex(text: str) -> str:
    """Convert Markdown `text` to LaTeX body content."""
    tokens = MarkdownIt("commonmark").parse(text)
    return _Converter().convert(tokens)


def shift_headings(text: str, by: int) -> str:
    """Deepen every ATX heading in Markdown `text` by `by` levels.

    Line-based on purpose: the result has to stay Markdown, so re-rendering the
    document through markdown-it would be a lossy round trip. Lines inside a
    fenced code block are left alone, and a heading is never pushed past H6.
    """
    if by == 0:
        return text

    lines = text.split("\n")
    in_fence = False
    shifted: list[str] = []
    for line in lines:
        if _FENCE.match(line):
            in_fence = not in_fence
        match = None if in_fence else _ATX_HEADING.match(line)
        if match is None:
            shifted.append(line)
        else:
            level = min(len(match.group(1)) + by, _MAX_HEADING)
            shifted.append("#" * level + line[match.end(1) :])
    return "\n".join(shifted)


class _Converter:
    r"""A single Markdown-token walk. One instance per conversion.

    The state is what makes list items work: `_fresh_item` records that an
    `\\item` has just been emitted, so the block that follows joins it on the
    same line instead of opening with the usual blank-line separation. Without
    it a *loose* list — whose items wrap their content in real, non-hidden
    paragraph tokens — would leave every `\\item` dangling alone on its line.
    """

    def __init__(self) -> None:
        self.out: list[str] = []
        self._fresh_item = False

    def convert(self, tokens: list[Token]) -> str:
        for token in tokens:
            self._block(token)
        body = "".join(self.out)
        return f"{body}\n" if body else ""

    def _start_block(self, separator: str = "\n\n") -> None:
        """Separate the block about to be emitted from the one before it."""
        if self._fresh_item:
            self._fresh_item = False
        elif self.out:
            self.out.append(separator)

    def _block(self, token: Token) -> None:  # noqa: C901  one branch per token type; a dispatch table would only move the cases
        match token.type:
            case "heading_open":
                self._start_block()
                level = int(token.tag.removeprefix("h"))
                self.out.append(f"{_HEADINGS[level]}{{")
            case "heading_close":
                self.out.append("}")
            case "paragraph_open":
                self._start_block()
            case "bullet_list_open" | "ordered_list_open":
                self._start_block("\n")
                self.out.append(
                    rf"\begin{{{_LISTS[token.type.removesuffix('_open')]}}}"
                )
            case "bullet_list_close" | "ordered_list_close":
                self._start_block("\n")
                self.out.append(rf"\end{{{_LISTS[token.type.removesuffix('_close')]}}}")
            case "list_item_open":
                self._start_block("\n")
                self.out.append(r"\item ")
                self._fresh_item = True
            case "hr":
                self._start_block()
                self.out.append(r"\hrulefill")
            case "fence" | "code_block":
                self._start_block()
                content = token.content
                if not content.endswith("\n"):
                    content += "\n"
                self.out.append(
                    f"\\begin{{verbatim}}\n{content}\\end{{verbatim}}",
                )
            case "inline":
                for child in token.children or []:
                    self._inline(child)
            case _:
                # Block quotes, tables, raw HTML, and anything else markdown-it
                # grows later: their inline children still flow through, so the
                # text survives even when the construct does not.
                pass

    def _inline(self, token: Token) -> None:
        match token.type:
            case "text":
                self.out.append(latex_escape(token.content))
            case "code_inline":
                self.out.append(rf"\texttt{{{latex_escape(token.content)}}}")
            case "strong_open" | "em_open":
                self.out.append(f"{_WRAPPERS[token.type.removesuffix('_open')]}{{")
            case "strong_close" | "em_close":
                self.out.append("}")
            case "softbreak":
                self.out.append("\n")
            case "hardbreak":
                self.out.append("\\\\\n")
            case _:
                # Links keep their text and lose their URL; images and raw
                # inline HTML vanish entirely. See the module docstring.
                pass
