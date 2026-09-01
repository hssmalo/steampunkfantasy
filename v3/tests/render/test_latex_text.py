"""Tests for `latex_escape`, the text-mode escaper both LaTeX seams share."""

from spf.render.latex_text import latex_escape


def test_tex_specials_are_escaped() -> None:
    assert latex_escape("50% of A & B uses snake_case #1") == (
        r"50\% of A \& B uses snake\_case \#1"
    )


def test_braces_and_backslash_become_commands() -> None:
    assert (
        latex_escape(r"{N}\~^")
        == r"\{N\}\textbackslash{}\textasciitilde{}\textasciicircum{}"
    )


def test_a_degree_glyph_becomes_textdegree() -> None:
    # Order cells carry `°`, which has no literal text-mode spelling.
    assert latex_escape("90°") == r"90\textdegree{}"


def test_infinity_goes_through_math_mode() -> None:
    # `∞` has no text-mode glyph at all, so an unescaped one is a fatal
    # pdflatex error rather than a bad-looking page.
    assert latex_escape("∞") == r"$\infty$"


def test_safe_characters_pass_through() -> None:
    assert latex_escape("+[1-2]") == "+[1-2]"


def test_a_non_string_is_stringified_first() -> None:
    assert latex_escape(42) == "42"
