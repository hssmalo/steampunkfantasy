"""Tests for the Markdown-to-LaTeX converter and the heading-shift filter."""

from spf.render.md_latex import md_to_latex, shift_headings

# --- Headings ---------------------------------------------------------------


def test_h2_becomes_a_subsection() -> None:
    assert r"\subsection{Phases}" in md_to_latex("## Phases\n")


def test_h3_becomes_a_subsubsection() -> None:
    assert r"\subsubsection{Speed}" in md_to_latex("### Speed\n")


def test_h4_becomes_a_paragraph() -> None:
    assert r"\paragraph{Detail}" in md_to_latex("#### Detail\n")


def test_h1_degrades_to_a_subsection() -> None:
    # The `markdown` kind's parser drops H1s, so one should never arrive here;
    # map it defensively rather than raising.
    assert r"\subsection{Stray}" in md_to_latex("# Stray\n")


def test_heading_text_is_escaped() -> None:
    assert r"\subsection{Fire \& Movement}" in md_to_latex("## Fire & Movement\n")


# --- Paragraphs and inline markup -------------------------------------------


def test_paragraphs_are_separated_by_a_blank_line() -> None:
    latex = md_to_latex("First.\n\nSecond.\n")
    assert "First.\n\nSecond." in latex


def test_text_is_latex_escaped() -> None:
    latex = md_to_latex("50% of A & B uses snake_case #1\n")
    assert r"50\% of A \& B uses snake\_case \#1" in latex


def test_variable_placeholder_renders_literally() -> None:
    # The rules prose carries `{N}`-style placeholders. Escaping the braces is
    # what makes them *print* as `{N}` instead of vanishing into a TeX group.
    assert r"roll \{N\} or better" in md_to_latex("roll {N} or better\n")


def test_strong_becomes_textbf() -> None:
    assert r"\textbf{Gunnery}" in md_to_latex("A **Gunnery** phase\n")


def test_emphasis_becomes_textit() -> None:
    assert r"\textit{simultaneously}" in md_to_latex("resolve *simultaneously*\n")


def test_inline_code_becomes_escaped_texttt() -> None:
    assert r"\texttt{a\_b}" in md_to_latex("use `a_b` here\n")


def test_hardbreak_becomes_a_latex_line_break() -> None:
    # A trailing backslash in Markdown produces a `hardbreak` token.
    latex = md_to_latex("Gunnery 1 \\\nApply damage\n")
    assert "Gunnery 1 \\\\\nApply damage" in latex


def test_softbreak_becomes_a_newline() -> None:
    latex = md_to_latex("one\ntwo\n")
    assert "one\ntwo" in latex


def test_link_keeps_its_text_and_drops_the_url() -> None:
    latex = md_to_latex("see [the rules](https://example.com/rules)\n")
    assert "see the rules" in latex
    assert "example.com" not in latex


# --- Lists ------------------------------------------------------------------


def test_bullet_list_becomes_itemize() -> None:
    latex = md_to_latex("- one\n- two\n")
    assert r"\begin{itemize}" in latex
    assert r"\item one" in latex
    assert r"\item two" in latex
    assert r"\end{itemize}" in latex


def test_ordered_list_becomes_enumerate() -> None:
    latex = md_to_latex("1. first\n2. second\n")
    assert r"\begin{enumerate}" in latex
    assert r"\item first" in latex
    assert r"\end{enumerate}" in latex


def test_loose_list_item_keeps_its_text_on_the_item_line() -> None:
    # A loose list wraps each item's content in a paragraph; emitting the usual
    # blank line before it would leave `\item` dangling on its own.
    latex = md_to_latex("- one\n\n- two\n")
    assert r"\item one" in latex
    assert r"\item two" in latex
    assert "\\item\n\n" not in latex


def test_multi_paragraph_list_item_separates_its_later_paragraphs() -> None:
    latex = md_to_latex("- one\n\n  more\n\n- two\n")
    assert r"\item one" in latex
    assert "one\n\nmore" in latex


def test_bullet_list_nested_in_an_ordered_list() -> None:
    latex = md_to_latex("1. outer\n    - inner\n")
    assert latex.index(r"\begin{enumerate}") < latex.index(r"\begin{itemize}")
    assert latex.index(r"\end{itemize}") < latex.index(r"\end{enumerate}")
    assert r"\item inner" in latex


# --- Blocks -----------------------------------------------------------------


def test_thematic_break_becomes_an_hrule() -> None:
    assert r"\hrulefill" in md_to_latex("one\n\n---\n\ntwo\n")


def test_fenced_code_is_verbatim_and_unescaped() -> None:
    latex = md_to_latex("```\na_b & c\n```\n")
    assert r"\begin{verbatim}" in latex
    assert "a_b & c" in latex
    assert r"\end{verbatim}" in latex
    assert r"\_" not in latex


def test_indented_code_block_is_verbatim() -> None:
    latex = md_to_latex("    a_b & c\n")
    assert r"\begin{verbatim}" in latex
    assert "a_b & c" in latex


def test_blockquote_content_survives_as_text() -> None:
    # Unsupported constructs degrade to their escaped content, never raise.
    assert "quoted" in md_to_latex("> quoted\n")


def test_empty_source_converts_to_empty_text() -> None:
    assert md_to_latex("") == ""


# --- shift_headings ---------------------------------------------------------


def test_shift_headings_deepens_atx_headings() -> None:
    assert shift_headings("## Phases\n", 1) == "### Phases\n"


def test_shift_headings_leaves_body_text_alone() -> None:
    assert shift_headings("a # b\nplain\n", 1) == "a # b\nplain\n"


def test_shift_headings_skips_fenced_code() -> None:
    text = "## Real\n\n```\n## Not a heading\n```\n"
    assert shift_headings(text, 1) == "### Real\n\n```\n## Not a heading\n```\n"


def test_shift_headings_by_zero_is_the_identity() -> None:
    assert shift_headings("## Phases\n", 0) == "## Phases\n"
