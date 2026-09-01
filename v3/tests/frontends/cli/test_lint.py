"""Tests for `spf lint`, the one linting namespace.

Every corpus here is synthetic and under `tmp_path`. No test runs these
commands over the committed data: an invalid TOML edit must be caught by the
linter, never by a test (`docs/agents/testing.md`).
"""

import json
from pathlib import Path
from typing import Any

import pytest
from cyclopts.exceptions import UnknownOptionError

from spf.config import config
from spf.frontends.cli import app
from spf.schemas.race import RaceConfig
from tests.conftest import (
    InstallRegistry,
    synthetic_army,
    synthetic_equipment,
    synthetic_race,
    write_race_toml,
)

_BROKEN_RACE = "[races.ork]\nname = 123\n"


def _lint(*args: str) -> None:
    """Run `spf lint ...`, letting a SystemExit out to the test."""
    app(["lint", *args], exit_on_error=False, result_action="return_value")


def _findings(capsys: pytest.CaptureFixture[str]) -> list[list[str]]:
    """Read every printed finding back as its columns."""
    return [
        line.split("  ")
        for line in capsys.readouterr().out.splitlines()
        if line.strip()
    ]


def _army_data(race: RaceConfig) -> dict[str, Any]:
    """Build the JSON an Army file holds, for a `synthetic_race` Race."""
    army = synthetic_army(race)
    return {
        "race": army.race,
        "nick": army.nick,
        "units": [
            {
                "name": unit.name,
                "models": [
                    {"name": model.name, "upgrades": list(model.upgrades)}
                    for model in unit.models
                ],
            }
            for unit in army.units
        ],
    }


def _write_army(directory: Path, name: str, data: object) -> None:
    """Write an Army JSON file the linter will find."""
    (directory / f"{name}.json").write_text(json.dumps(data, indent=2))


# ---------------------------------------------------------------------------
# Exit codes
# ---------------------------------------------------------------------------


def test_lint_races_is_silent_and_exits_zero_on_a_clean_corpus(
    races_dir: Path,
    install_registry: InstallRegistry,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """No findings means no output and no failure."""
    install_registry()
    write_race_toml(races_dir, synthetic_race())

    _lint("races")

    assert capsys.readouterr().out == ""


def test_lint_races_exits_one_when_anything_is_wrong(
    races_dir: Path, install_registry: InstallRegistry
) -> None:
    """Lint speaks, the build fails: there is exactly one severity."""
    install_registry()
    (races_dir / "ork.toml").write_text(_BROKEN_RACE)

    with pytest.raises(SystemExit) as exit_info:
        _lint("races")

    assert exit_info.value.code == 1


# ---------------------------------------------------------------------------
# Both gates, in one command
# ---------------------------------------------------------------------------


def test_lint_races_reports_a_load_failure(
    races_dir: Path,
    install_registry: InstallRegistry,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """A schema failure is a finding of this command's, not another's."""
    install_registry()
    (races_dir / "ork.toml").write_text(_BROKEN_RACE)

    with pytest.raises(SystemExit):
        _lint("races")

    findings = _findings(capsys)
    assert findings
    assert all(finding[0] == "races/ork.toml" for finding in findings)
    assert all("load" in finding for finding in findings)


def test_lint_races_reports_style_for_a_race_that_loads(
    races_dir: Path,
    install_registry: InstallRegistry,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """A file that loads fine but is untidy gets Style findings."""
    install_registry()
    race = synthetic_race(
        equipment={
            "knife": synthetic_equipment(name="Knife", cost=None, upgrade_all=None),
            "sword": synthetic_equipment(name="Not A Sword At All"),
        }
    )
    write_race_toml(races_dir, race)

    with pytest.raises(SystemExit):
        _lint("races")

    findings = _findings(capsys)
    assert findings
    assert all("load" not in finding for finding in findings)


def test_lint_races_reports_no_style_for_a_race_that_will_not_load(
    races_dir: Path,
    install_registry: InstallRegistry,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """A file that fails the load gate yields no other kind of finding."""
    install_registry()
    (races_dir / "ork.toml").write_text(_BROKEN_RACE)

    with pytest.raises(SystemExit):
        _lint("races")

    assert {finding[-2] for finding in _findings(capsys)} == {"load"}


# ---------------------------------------------------------------------------
# Armies, and the cascade
# ---------------------------------------------------------------------------


def test_lint_armies_reports_an_illegal_build(
    armies_dir: Path,
    races_dir: Path,
    install_registry: InstallRegistry,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """An Army that loads but that its Race will not field is a Build finding."""
    install_registry()
    race = synthetic_race()
    write_race_toml(races_dir, race)
    data = _army_data(race)
    data["units"][0]["models"][0]["upgrades"] = ["knife"]
    _write_army(armies_dir, "illegal", data)

    with pytest.raises(SystemExit):
        _lint("armies")

    [finding] = _findings(capsys)
    assert finding[0] == "armies/illegal.json"
    assert finding[2] == "build"


def test_lint_armies_suppresses_the_armies_of_a_broken_race(
    armies_dir: Path,
    races_dir: Path,
    install_registry: InstallRegistry,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """A broken Race is reported at its cause, and not again per Army."""
    install_registry()
    race = synthetic_race()
    write_race_toml(races_dir, race)
    _write_army(armies_dir, "orkish", _army_data(race) | {"race": "ork"})
    (races_dir / "ork.toml").write_text(_BROKEN_RACE)

    _lint("armies")

    assert capsys.readouterr().out == ""


@pytest.mark.usefixtures("clean_corpus")
def test_lint_all_reports_a_broken_race_exactly_once(
    armies_dir: Path,
    races_dir: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """One process, one report: the Race fails, its Armies stay quiet."""
    _write_army(armies_dir, "orkish", _army_data(synthetic_race()) | {"race": "ork"})
    (races_dir / "ork.toml").write_text(_BROKEN_RACE)

    with pytest.raises(SystemExit):
        _lint("all")

    files = {finding[0] for finding in _findings(capsys)}
    assert files == {"races/ork.toml"}


# ---------------------------------------------------------------------------
# `spf lint all`
# ---------------------------------------------------------------------------


@pytest.mark.usefixtures("clean_corpus")
def test_lint_all_collects_across_corpora_rather_than_stopping(
    armies_dir: Path,
    races_dir: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Collect-all, never fail-fast: a broken Race does not hide a broken Army."""
    (races_dir / "elf.toml").write_text("[races.elf]\nname = 123\n")
    data = _army_data(synthetic_race())
    data["units"][0]["models"][0]["upgrades"] = ["knife"]
    _write_army(armies_dir, "illegal", data)

    with pytest.raises(SystemExit):
        _lint("all")

    files = {finding[0] for finding in _findings(capsys)}
    assert files == {"races/elf.toml", "armies/illegal.json"}


@pytest.mark.usefixtures("clean_corpus")
def test_lint_all_is_silent_and_exits_zero_on_a_clean_corpus(
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Output from a green build goes unread, so a clean run prints nothing."""
    _lint("all")

    assert capsys.readouterr().out == ""


# ---------------------------------------------------------------------------
# Render
# ---------------------------------------------------------------------------


@pytest.mark.usefixtures("clean_corpus")
def test_lint_render_reports_a_package_the_manifest_omits(
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Check one authored file against the other: the manifest, the templates."""
    latex_dir = config.paths.templates / "latex"
    (latex_dir / "main.tex.jinja").write_text("\\usepackage{tikz}\n")

    with pytest.raises(SystemExit):
        _lint("render")

    [finding] = _findings(capsys)
    assert finding == ["templates/latex/requirements.toml", "missing-package", "tikz"]


@pytest.mark.usefixtures("clean_corpus")
def test_lint_render_takes_no_arguments() -> None:
    """`--tlmgr` was never a lint; it lives at `spf render tlmgr`."""
    with pytest.raises(UnknownOptionError):
        app(["lint", "render", "--tlmgr"], exit_on_error=False)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def clean_corpus(
    tmp_path: Path,
    races_dir: Path,
    armies_dir: Path,
    install_registry: InstallRegistry,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Point every corpus at a synthetic one that lints clean."""
    install_registry()
    race = synthetic_race()
    write_race_toml(races_dir, race)
    _write_army(armies_dir, "clean", _army_data(race))

    rules = tmp_path / "rules"
    rules.mkdir()
    (rules / "namespaces.toml").write_text(
        "[namespaces]\n"
        'damage_type = { name = "Damage Types", label = "damage type",'
        ' file = "namespaces.toml", table = "damage_type" }\n'
        '\n[damage_type.fire]\nname = "Fire"\ntodo = "Unwritten."\n'
    )
    (rules / "rulebook.toml").write_text('title = "Rulebook"\nsections = []\n')
    monkeypatch.setattr(config.paths, "rules", rules)

    templates = tmp_path / "templates"
    (templates / "latex").mkdir(parents=True)
    (templates / "latex" / "requirements.toml").write_text("package = []\n")
    monkeypatch.setattr(config.paths, "templates", templates)

    (armies_dir / "site.toml").write_text(
        '[[packs]]\npack = "2026"\nheading = "2026"\n'
    )
    (armies_dir / "2026").mkdir()
    (armies_dir / "2026" / "pack.toml").write_text('title = "Pack"\narmies = []\n')

    workflows = tmp_path / "workflows"
    comfyui = config.assets.image.comfyui
    for env in ("local", "cloud"):
        (workflows / env).mkdir(parents=True)
        (workflows / env / f"{comfyui.selected(env).profile}.json").write_text("{}")
    monkeypatch.setattr(config.paths, "workflows", workflows)
