"""Tests for the `spf special show` command."""

import pytest
from cyclopts.exceptions import CycloptsError

from spf.frontends.cli import app


def show(key: str) -> None:
    app(["special", "show", key], exit_on_error=False, result_action="return_value")


# `spf special show` reads the label dicts the Race files no longer carry, so
# these two find nothing until the command reads instances instead.
UNREAD = pytest.mark.xfail(reason="the command still reads label dicts", strict=True)


@UNREAD
def test_show_accepts_a_key_in_the_wrong_case(
    capsys: pytest.CaptureFixture[str],
) -> None:
    # The key is canonicalised, so the lowercase spelling finds the same rows
    # the canonical one does rather than being rejected.
    show("Ork Reroll")
    canonical = capsys.readouterr().out
    show("ork reroll")
    assert "A  Model:     Grunt" in canonical
    assert capsys.readouterr().out == canonical


@UNREAD
def test_show_reports_range_specials(capsys: pytest.CaptureFixture[str]) -> None:
    show("Sniper")
    out = capsys.readouterr().out
    assert "R Equipment: Sniper Rifle" in out


def test_show_suggests_a_near_miss() -> None:
    with pytest.raises(CycloptsError, match=r'Did you mean "Ork Reroll"\?'):
        show("Reroll")


def test_show_points_at_the_listing_command_for_nonsense() -> None:
    with pytest.raises(CycloptsError, match=r"spf rules specials"):
        show("zzz")
