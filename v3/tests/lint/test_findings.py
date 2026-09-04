"""Tests for the one finding type and the one renderer every lint shares."""

import pytest

from spf.lint import LintFinding, findings


def test_format_joins_columns_with_two_spaces() -> None:
    """A finding is one line, its four columns two spaces apart."""
    finding = LintFinding(
        file="races/ork.toml",
        location="units.archer.cost.mp",
        rule="load",
        message="Input should be a valid integer",
    )
    assert findings.format_finding(finding) == (
        "races/ork.toml  units.archer.cost.mp  load  Input should be a valid integer"
    )


def test_format_omits_an_empty_location() -> None:
    """A file-level finding leaves out the column rather than padding it."""
    finding = LintFinding(
        file="templates/latex/requirements.toml",
        location="",
        rule="missing-package",
        message="tikz",
    )
    assert findings.format_finding(finding) == (
        "templates/latex/requirements.toml  missing-package  tikz"
    )


def test_format_omits_an_empty_message() -> None:
    """A rule that says everything in its name needs no message column."""
    finding = LintFinding(file="races/ork.toml", location="", rule="load", message="")
    assert findings.format_finding(finding) == "races/ork.toml  load"


def test_print_findings_writes_one_line_each(
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Every finding lands on its own line."""
    findings.print_findings(
        [
            LintFinding(file="a.toml", location="x", rule="load", message="first"),
            LintFinding(file="b.toml", location="y", rule="load", message="second"),
        ]
    )
    assert capsys.readouterr().out.splitlines() == [
        "a.toml  x  load  first",
        "b.toml  y  load  second",
    ]


def test_print_findings_soft_wraps_without_highlighting(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Findings are grepped, so Rich must neither fold nor color them."""
    calls: list[dict[str, object]] = []
    monkeypatch.setattr(
        findings.stdout, "print", lambda *_, **kwargs: calls.append(kwargs)
    )
    findings.print_findings(
        [LintFinding(file="a.toml", location="", rule="load", message="boom")]
    )
    assert calls == [{"highlight": False, "markup": False, "soft_wrap": True}]


def test_print_findings_of_nothing_prints_nothing(
    capsys: pytest.CaptureFixture[str],
) -> None:
    """A clean corpus is silent."""
    findings.print_findings([])
    assert capsys.readouterr().out == ""


def test_print_findings_does_not_read_a_message_as_markup(
    capsys: pytest.CaptureFixture[str],
) -> None:
    """An order cell holds square brackets, and Rich would swallow them."""
    finding = LintFinding(file="f", location="l", rule="r", message="A[f, fly]")

    findings.print_findings([finding])

    assert "A[f, fly]" in capsys.readouterr().out
