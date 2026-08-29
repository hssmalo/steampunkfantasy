"""Tests for the `spf army list` and `spf army show` commands.

Both commands read `config.paths.armies`, so every test here points that at
`tmp_path` and writes the Army JSON it needs: the committed armies are a
separate subject, covered by `tests/armies/test_io.py`.
"""

import json
from pathlib import Path

import pytest

from spf.config import config
from spf.frontends.cli.army import list_armies, show_army
from tests.conftest import unwrapped


@pytest.fixture
def armies_dir(tmp_path: Path, *, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Redirect config.paths.armies to a temporary directory."""
    monkeypatch.setattr(config.paths, "armies", tmp_path)
    return tmp_path


def _army_data(
    *, nick: str = "Da Boyz", upgrades: list[str] | None = None
) -> dict[str, object]:
    """Build a valid Goblin army: one Unit of one Model."""
    return {
        "race": "goblin",
        "nick": nick,
        "units": [
            {
                "name": "goblin_infantry",
                "models": [
                    {"name": "goblin_infantry", "upgrades": upgrades or []},
                ],
            }
        ],
    }


def _write_army(armies_dir: Path, army_id: str, data: dict[str, object]) -> None:
    """Save raw Army JSON at `army_id`, which may name a tournament directory."""
    path = armies_dir / f"{army_id}.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data))


# ---------------------------------------------------------------------------
# show_army
# ---------------------------------------------------------------------------


def test_show_army_prints_the_nick(
    armies_dir: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    _write_army(armies_dir, "warband", _army_data(nick="Snaggle's Lads"))

    show_army("warband")

    assert "Snaggle's Lads" in unwrapped(capsys.readouterr().out)


def test_show_army_prints_its_units(
    armies_dir: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    _write_army(armies_dir, "warband", _army_data())

    show_army("warband")

    assert "Total cost" in unwrapped(capsys.readouterr().out)


def test_show_army_missing_file_exits_nonzero(armies_dir: Path) -> None:  # noqa: ARG001
    with pytest.raises(SystemExit) as exc_info:
        show_army("no-such-army")

    assert exc_info.value.code != 0


def test_show_army_missing_file_names_the_army_on_stderr(
    armies_dir: Path,  # noqa: ARG001
    capsys: pytest.CaptureFixture[str],
) -> None:
    with pytest.raises(SystemExit):
        show_army("no-such-army")

    captured = capsys.readouterr()
    assert "no-such-army" in unwrapped(captured.err)
    assert captured.out == ""


@pytest.mark.parametrize(
    ("army_id", "data", "expected"),
    [
        (
            "bad-race",
            {"race": "nonexistent_race_xyz", "nick": "Nope", "units": []},
            "nonexistent_race_xyz",
        ),
        (
            "bad-unit",
            {"race": "goblin", "nick": "Nope", "units": [{"name": "", "models": []}]},
            "unknown unit name",
        ),
        (
            "bad-upgrade",
            _army_data(upgrades=["no_such_upgrade"]),
            "unknown equipment 'no_such_upgrade'",
        ),
    ],
)
def test_show_army_invalid_file_reports_the_value_error(
    armies_dir: Path,
    capsys: pytest.CaptureFixture[str],
    army_id: str,
    data: dict[str, object],
    expected: str,
) -> None:
    """A present-but-invalid Army is a message and an exit code, not a traceback."""
    _write_army(armies_dir, army_id, data)

    with pytest.raises(SystemExit) as exc_info:
        show_army(army_id)

    assert exc_info.value.code == 1
    assert expected in unwrapped(capsys.readouterr().err)


def test_show_army_invalid_file_prints_nothing_to_stdout(
    armies_dir: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    # The Army is never resolved, so nothing of it reaches the user's report.
    _write_army(armies_dir, "bad-upgrade", _army_data(upgrades=["no_such_upgrade"]))

    with pytest.raises(SystemExit):
        show_army("bad-upgrade")

    assert capsys.readouterr().out == ""


# ---------------------------------------------------------------------------
# list_armies
# ---------------------------------------------------------------------------


def test_list_armies_lists_every_saved_army(
    armies_dir: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    _write_army(armies_dir, "alpha", _army_data(nick="Alpha"))
    _write_army(armies_dir, "beta", _army_data(nick="Beta"))

    list_armies()

    output = capsys.readouterr().out
    assert "alpha" in output
    assert "beta" in output


def test_list_armies_includes_a_tournament_army_by_its_path(
    armies_dir: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    # A tournament Army lives in a subdirectory, and the listed id keeps it.
    _write_army(armies_dir, "2025/gorak", _army_data(nick="Gorak"))

    list_armies()

    assert "2025/gorak" in capsys.readouterr().out


def test_list_armies_shows_the_race_and_the_nick(
    armies_dir: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    _write_army(armies_dir, "alpha", _army_data(nick="Alpha Warband"))

    list_armies()

    row = unwrapped(capsys.readouterr().out)
    assert "Goblin" in row
    assert "Alpha Warband" in row


def test_list_armies_prints_nothing_when_the_directory_is_empty(
    armies_dir: Path,  # noqa: ARG001
    capsys: pytest.CaptureFixture[str],
) -> None:
    list_armies()

    captured = capsys.readouterr()
    assert captured.out == ""
    assert captured.err == ""
