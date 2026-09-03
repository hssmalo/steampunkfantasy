"""Tests for `spf lint`, the one linting namespace.

Every corpus here is synthetic and under `tmp_path`. No test runs these
commands over the committed data: an invalid TOML edit must be caught by the
linter, never by a test (`docs/agents/testing.md`).
"""

from pathlib import Path

import pytest
from cyclopts.exceptions import UnknownOptionError

from spf.config import config
from spf.frontends.cli import app
from tests.conftest import (
    BROKEN_RACE_TOML,
    InstallRegistry,
    army_json,
    synthetic_equipment,
    synthetic_race,
    write_army_json,
    write_race_toml,
)


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
    (races_dir / "ork.toml").write_text(BROKEN_RACE_TOML)

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
    (races_dir / "ork.toml").write_text(BROKEN_RACE_TOML)

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
    (races_dir / "ork.toml").write_text(BROKEN_RACE_TOML)

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
    data = army_json(race)
    data["units"][0]["models"][0]["upgrades"] = ["knife"]
    write_army_json(armies_dir, "illegal", data)

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
    write_army_json(armies_dir, "orkish", army_json(race, race="ork"))
    (races_dir / "ork.toml").write_text(BROKEN_RACE_TOML)

    _lint("armies")

    assert capsys.readouterr().out == ""


@pytest.mark.usefixtures("clean_corpus")
def test_lint_all_reports_a_broken_race_exactly_once(
    armies_dir: Path,
    races_dir: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """One process, one report: the Race fails, its Armies stay quiet."""
    write_army_json(armies_dir, "orkish", army_json(synthetic_race(), race="ork"))
    (races_dir / "ork.toml").write_text(BROKEN_RACE_TOML)

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
    data = army_json(synthetic_race())
    data["units"][0]["models"][0]["upgrades"] = ["knife"]
    write_army_json(armies_dir, "illegal", data)

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
# A rules file that will not read
# ---------------------------------------------------------------------------


def test_lint_all_reports_an_unreadable_rules_file_exactly_once(
    registry_reading_corpus: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """The file with the typo is the whole report, not one line per Race.

    Every Race resolves its refs through the registry, so a rules file that
    will not parse fails all of them -- but a Race that was never the problem
    is not worth a line, and naming it first buries the file that is.
    """
    (registry_reading_corpus / "namespaces.toml").write_text(
        '[namespaces]\nsee_also = ["token.acid", "token.minor_acid"\n'
    )

    with pytest.raises(SystemExit):
        _lint("all")

    [finding] = _findings(capsys)
    assert finding[0] == "rules/namespaces.toml"
    assert finding[-1].startswith("Unclosed array")


def test_lint_all_reports_a_rules_schema_failure_exactly_once(
    registry_reading_corpus: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """A schema failure keeps the located finding the rules corpus reports."""
    (registry_reading_corpus / "namespaces.toml").write_text(
        NAMESPACES_TOML + 'bogus_field = "nonsense"\n' + RESISTANCE_TYPES
    )

    with pytest.raises(SystemExit):
        _lint("all")

    assert _findings(capsys) == [
        [
            "rules/namespaces.toml",
            "damage_type.fire.bogus_field",
            "load",
            "Extra inputs are not permitted",
        ]
    ]


def test_lint_races_names_the_rules_file_rather_than_going_silent(
    registry_reading_corpus: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Suppressing the per-Race copies must not make the corpus look clean.

    `spf lint races` cannot load a Race while the registry is unreadable, so
    it reports what stopped it -- at the rules file, where the fix is.
    """
    (registry_reading_corpus / "namespaces.toml").write_text(
        '[namespaces]\nsee_also = ["token.acid", "token.minor_acid"\n'
    )

    with pytest.raises(SystemExit) as exit_info:
        _lint("races")

    assert exit_info.value.code == 1
    assert {finding[0] for finding in _findings(capsys)} == {"rules/namespaces.toml"}


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


NAMESPACES_TOML = (
    "[namespaces]\n"
    'damage_type = { name = "Damage Types", label = "damage type",'
    ' file = "namespaces.toml", table = "damage_type" }\n'
    '\n[damage_type.fire]\nname = "Fire"\ntodo = "Unwritten."\n'
)
"""The smallest namespace registry that reads: one namespace, whose records
live beside it."""

RESISTANCE_TYPES = "\n[resistance_type]\n"
"""The other record table the namespace registry has to carry, empty. Only a
test that needs `namespaces.toml` to satisfy its schema outright appends it."""

EMPTY_RACE_TOML = '[races.goblin]\nname = "Goblin"\n\n[units]\n[models]\n[equipment]\n'
"""A Race with an empty catalogue, for a test that loads it through the real
registries: the rules directory beside it declares one namespace, which no
catalogue entry could satisfy."""


def _write_corpus_around_races(
    tmp_path: Path, armies_dir: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Set up every corpus but the Races: rules, templates, Packs, workflows."""
    rules = tmp_path / "rules"
    rules.mkdir()
    (rules / "namespaces.toml").write_text(NAMESPACES_TOML)
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
    write_army_json(armies_dir, "clean", army_json(race))
    _write_corpus_around_races(tmp_path, armies_dir, monkeypatch)


@pytest.fixture
def registry_reading_corpus(
    tmp_path: Path,
    races_dir: Path,
    armies_dir: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> Path:
    """Set up a clean corpus whose Races load through the real registries.

    The sibling of `clean_corpus`, for a test about what an unreadable *rules
    file* does to a Race load: that question cannot be asked of a corpus whose
    registry lookups are answered from an installed Registry. Returns the rules
    directory, which holds the file the test is going to break.
    """
    (races_dir / "goblin.toml").write_text(EMPTY_RACE_TOML)
    _write_corpus_around_races(tmp_path, armies_dir, monkeypatch)
    return config.paths.rules
