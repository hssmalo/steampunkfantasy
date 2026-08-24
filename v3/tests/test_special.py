"""Tests for the `spf special show` command."""

import pytest
from cyclopts.exceptions import CycloptsError

from spf.frontends.cli import app


def show(key: str) -> None:
    app(["special", "show", key], exit_on_error=False, result_action="return_value")


def test_show_accepts_a_key_in_the_wrong_case(
    capsys: pytest.CaptureFixture[str],
) -> None:
    # The key is canonicalised, so the shouted spelling finds the same rows the
    # canonical one does rather than being rejected.
    show("ORK_REROLL")
    canonical = capsys.readouterr().out
    show("ork_reroll")
    assert "A  Model:     Grunt" in canonical
    assert capsys.readouterr().out == canonical


def test_show_reports_range_specials(capsys: pytest.CaptureFixture[str]) -> None:
    show("sniper")
    out = capsys.readouterr().out
    assert "R Equipment: Sniper Rifle" in out


def test_show_reports_every_instance_a_holder_carries(
    capsys: pytest.CaptureFixture[str],
) -> None:
    # A slot holds N instances of an id, so a holder with two Resistances is
    # two rows rather than the one a label dict could hold.
    show("resistance")
    rows = [
        line
        for line in capsys.readouterr().out.splitlines()
        if "Equipment: Trench Coat of Resistance" in line
    ]
    assert len(rows) == 2


def test_show_names_an_instance_that_renamed_itself(
    capsys: pytest.CaptureFixture[str],
) -> None:
    # An atmospheric name is what the reader could not have guessed from the id.
    show("to_hit")
    assert "Enhanced Arrow: Excellent Shot" in capsys.readouterr().out


def test_show_suggests_a_near_miss() -> None:
    with pytest.raises(CycloptsError, match=r'Did you mean "ork_reroll"\?'):
        show("ork_rerol")


def test_show_points_at_the_listing_command_for_nonsense() -> None:
    with pytest.raises(CycloptsError, match=r"spf rules specials"):
        show("zzz")
