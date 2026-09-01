"""Tests for the per-corpus load probes.

Every corpus is a synthetic one under `tmp_path`: these probes are about what
`spf lint` does with a file that will not load, not about the committed data
(`docs/agents/testing.md`).
"""

import json
from pathlib import Path
from typing import Any

import pytest
import tomlkit

from spf.config import config
from spf.lint import loading
from spf.schemas.race import RaceConfig
from tests.conftest import (
    InstallRegistry,
    synthetic_army,
    synthetic_race,
    write_race_toml,
)

_BROKEN_RACE = "[races.ork]\nname = 123\n"


def _write_army(directory: Path, name: str, army: object) -> Path:
    """Write an Army JSON file the probe will find."""
    path = directory / f"{name}.json"
    path.write_text(json.dumps(army, indent=2))
    return path


# ---------------------------------------------------------------------------
# Races
# ---------------------------------------------------------------------------


def test_probe_races_is_silent_when_every_race_loads(
    races_dir: Path, install_registry: InstallRegistry
) -> None:
    """A clean corpus yields no findings, and every Race counts as loaded."""
    install_registry()
    write_race_toml(races_dir, synthetic_race())

    probe = loading.probe_races()

    assert probe.findings == []
    assert probe.loaded == ["goblin"]


def test_probe_races_reports_one_finding_per_pydantic_error(
    races_dir: Path, install_registry: InstallRegistry
) -> None:
    """Two schema errors in one file are two lines, not one."""
    install_registry()
    write_race_toml(races_dir, synthetic_race())
    _corrupt(races_dir / "goblin.toml", ("races", "goblin", "name"), ("units",))

    probe = loading.probe_races()

    assert len(probe.findings) == 2
    assert {finding.file for finding in probe.findings} == {"races/goblin.toml"}
    assert {finding.rule for finding in probe.findings} == {"load"}
    assert {finding.location for finding in probe.findings} == {
        "races.goblin.name",
        "units",
    }


def test_probe_races_locates_the_failing_field(
    races_dir: Path, install_registry: InstallRegistry
) -> None:
    """A finding's location is the dotted path pydantic reports."""
    install_registry()
    (races_dir / "ork.toml").write_text(_BROKEN_RACE)

    locations = {finding.location for finding in loading.probe_races().findings}

    assert "races.ork.name" in locations


def test_probe_races_leaves_a_broken_race_out_of_loaded(
    races_dir: Path, install_registry: InstallRegistry
) -> None:
    """A Race that failed is named as broken, not as loaded."""
    install_registry()
    write_race_toml(races_dir, synthetic_race())
    (races_dir / "ork.toml").write_text(_BROKEN_RACE)

    probe = loading.probe_races()

    assert probe.loaded == ["goblin"]
    assert probe.broken == frozenset({"ork"})


def test_probe_races_reports_unreadable_toml_as_a_file_level_finding(
    races_dir: Path, install_registry: InstallRegistry
) -> None:
    """A file TOML itself cannot parse is a Load finding, not a traceback."""
    install_registry()
    (races_dir / "ork.toml").write_text("this is not = = toml\n")

    [finding] = loading.probe_races().findings

    assert finding.file == "races/ork.toml"
    assert finding.location == ""
    assert finding.rule == "load"


# ---------------------------------------------------------------------------
# Armies
# ---------------------------------------------------------------------------


def test_probe_armies_is_silent_when_every_army_loads(
    armies_dir: Path, races_dir: Path, install_registry: InstallRegistry
) -> None:
    """A clean corpus yields no findings and hands back what it loaded."""
    install_registry()
    race = synthetic_race()
    write_race_toml(races_dir, race)
    _write_army(armies_dir, "clean", _army_data(race))

    probe = loading.probe_armies()

    assert probe.findings == []
    assert [loaded.file for loaded in probe.loaded] == ["armies/clean.json"]


def test_probe_armies_reports_an_unknown_unit_name(
    armies_dir: Path, races_dir: Path, install_registry: InstallRegistry
) -> None:
    """A name that resolves to nothing is a Load finding: the file will not load."""
    install_registry()
    race = synthetic_race()
    write_race_toml(races_dir, race)
    data = _army_data(race)
    data["units"][0]["name"] = "nonesuch"
    _write_army(armies_dir, "broken", data)

    probe = loading.probe_armies()

    assert [finding.rule for finding in probe.findings] == ["load"]
    assert probe.findings[0].file == "armies/broken.json"
    assert probe.loaded == []


def test_probe_armies_reports_unreadable_json(
    armies_dir: Path, races_dir: Path, install_registry: InstallRegistry
) -> None:
    """A JSON file that will not parse is one file-level Load finding."""
    install_registry()
    write_race_toml(races_dir, synthetic_race())
    (armies_dir / "broken.json").write_text("{not json")

    [finding] = loading.probe_armies().findings

    assert finding.file == "armies/broken.json"
    assert finding.rule == "load"


def test_probe_armies_suppresses_armies_of_a_broken_race(
    armies_dir: Path, races_dir: Path, install_registry: InstallRegistry
) -> None:
    """A broken Race is reported once, at its cause -- not again per Army."""
    install_registry()
    race = synthetic_race()
    write_race_toml(races_dir, race)
    _write_army(armies_dir, "orkish", _army_data(race) | {"race": "ork"})
    (races_dir / "ork.toml").write_text(_BROKEN_RACE)

    probe = loading.probe_armies(broken_races=frozenset({"ork"}))

    assert probe.findings == []


def test_probe_armies_reports_an_army_of_an_unknown_race(
    armies_dir: Path, races_dir: Path, install_registry: InstallRegistry
) -> None:
    """A Race that is not broken but simply absent is the Army's own problem."""
    install_registry()
    race = synthetic_race()
    write_race_toml(races_dir, race)
    _write_army(armies_dir, "orkish", _army_data(race) | {"race": "ork"})

    [finding] = loading.probe_armies().findings

    assert finding.file == "armies/orkish.json"
    assert finding.rule == "load"


# ---------------------------------------------------------------------------
# Rules
# ---------------------------------------------------------------------------


@pytest.mark.usefixtures("rules_dir")
def test_probe_rules_is_silent_on_a_registry_that_loads() -> None:
    """A corpus whose namespaces, records and Index all resolve says nothing."""
    assert loading.probe_rules() == []


def test_probe_rules_locates_a_schema_failure_at_its_own_file(
    rules_dir: Path,
) -> None:
    """A record that fails its schema names the file it was authored in."""
    (rules_dir / "namespaces.toml").write_text(
        _NAMESPACES + "\n[damage_type.fire]\nname = 5\n"
    )

    findings = loading.probe_rules()

    assert [finding.file for finding in findings] == ["rules/namespaces.toml"]
    assert findings[0].rule == "load"


def test_probe_rules_reports_a_namespace_with_no_loader(rules_dir: Path) -> None:
    """A cross-file failure is a Load finding against the declaring file."""
    (rules_dir / "namespaces.toml").write_text(
        "[namespaces]\n"
        'damage_type = { name = "D", label = "d",'
        ' file = "nonesuch.toml", table = "damage_type" }\n'
        '[damage_type.fire]\nname = "Fire"\ntodo = "Unwritten."\n'
    )

    findings = loading.probe_rules()

    assert [finding.file for finding in findings] == ["rules/namespaces.toml"]


def test_probe_rules_reports_a_rulebook_source_that_is_missing(
    rules_dir: Path,
) -> None:
    """The Rulebook Index is resolved, so a source it names must exist."""
    (rules_dir / "rulebook.toml").write_text(
        'title = "Rulebook"\n'
        "[[sections]]\n"
        'kind = "markdown"\nsource = "nonesuch.md"\ntitle = "Gone"\n'
    )

    findings = loading.probe_rules()

    assert [finding.file for finding in findings] == ["rules/rulebook.toml"]
    assert findings[0].rule == "load"


# ---------------------------------------------------------------------------
# Render
# ---------------------------------------------------------------------------


@pytest.mark.usefixtures("render_corpus")
def test_probe_render_is_silent_on_a_clean_corpus() -> None:
    """A manifest, a Site Index and a Pack Index that all load say nothing."""
    assert loading.probe_render() == []


def test_probe_render_reports_a_missing_manifest(render_corpus: Path) -> None:
    """The LaTeX manifest is a file the render corpus cannot do without."""
    (render_corpus / "latex" / "requirements.toml").unlink()

    findings = loading.probe_render()

    assert [finding.file for finding in findings] == [
        "templates/latex/requirements.toml"
    ]
    assert findings[0].rule == "load"


@pytest.mark.usefixtures("render_corpus")
def test_probe_render_reports_a_broken_site_index(armies_dir: Path) -> None:
    """The Site Index is schema-checked like any other authored file."""
    (armies_dir / "site.toml").write_text("[[packs]]\npack = 1\n")

    findings = loading.probe_render()

    assert {finding.file for finding in findings} == {"armies/site.toml"}


@pytest.mark.usefixtures("render_corpus")
def test_probe_render_reports_a_pack_the_site_index_names_but_lacks(
    armies_dir: Path,
) -> None:
    """A missing file a manifest names is a Load finding."""
    (armies_dir / "2026" / "pack.toml").unlink()

    findings = loading.probe_render()

    assert [finding.file for finding in findings] == ["armies/2026/pack.toml"]


@pytest.mark.usefixtures("render_corpus")
def test_probe_render_reports_a_broken_pack_index(armies_dir: Path) -> None:
    """A Pack Index that fails its schema is located at its own file."""
    (armies_dir / "2026" / "pack.toml").write_text("title = 5\narmies = []\n")

    findings = loading.probe_render()

    assert [finding.file for finding in findings] == ["armies/2026/pack.toml"]
    assert findings[0].rule == "load"


# ---------------------------------------------------------------------------
# Assets
# ---------------------------------------------------------------------------


def test_probe_assets_is_silent_when_the_configured_profile_resolves(
    workflows_dir: Path,
) -> None:
    """An Environment whose configured Profile is on disk says nothing."""
    env = config.assets.image.comfyui.env
    (workflows_dir / env).mkdir()
    profile = config.assets.image.comfyui.selected(env).profile
    (workflows_dir / env / f"{profile}.json").write_text("{}")

    assert loading.probe_assets() == []


def test_probe_assets_reports_a_configured_profile_that_does_not_resolve(
    workflows_dir: Path,
) -> None:
    """An Environment that offers Profiles but not its own is misconfigured."""
    env = config.assets.image.comfyui.env
    (workflows_dir / env).mkdir()
    (workflows_dir / env / "something-else.json").write_text("{}")

    findings = loading.probe_assets()

    assert [finding.rule for finding in findings] == ["load"]


@pytest.mark.usefixtures("workflows_dir")
def test_probe_assets_does_not_report_an_environment_that_is_absent() -> None:
    """`workflows/local/` is gitignored, so a fresh clone legitimately lacks it."""
    assert loading.probe_assets() == []


# ---------------------------------------------------------------------------
# Helpers and fixtures
# ---------------------------------------------------------------------------


def _corrupt(path: Path, *keys: tuple[str, ...]) -> None:
    """Replace each named field of a Race file with a value of the wrong type."""
    data = tomlkit.parse(path.read_text())
    for key in keys:
        table = data
        for part in key[:-1]:
            table = table[part]  # pyright: ignore[reportIndexIssue, reportArgumentType]
        table[key[-1]] = 123  # pyright: ignore[reportIndexIssue, reportArgumentType]
    path.write_text(tomlkit.dumps(data))


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


@pytest.fixture
def render_corpus(
    tmp_path: Path, armies_dir: Path, monkeypatch: pytest.MonkeyPatch
) -> Path:
    """Set up a LaTeX manifest, plus a Site Index and one Pack Index."""
    templates = tmp_path / "templates"
    (templates / "latex").mkdir(parents=True)
    (templates / "latex" / "requirements.toml").write_text(
        '[[package]]\nname = "tikz"\n'
    )
    monkeypatch.setattr(config.paths, "templates", templates)

    (armies_dir / "site.toml").write_text(
        '[[packs]]\npack = "2026"\nheading = "2026"\n'
    )
    (armies_dir / "2026").mkdir()
    (armies_dir / "2026" / "pack.toml").write_text('title = "Pack"\narmies = []\n')
    return templates


_NAMESPACES = (
    "[namespaces]\n"
    'damage_type = { name = "Damage Types", label = "damage type",'
    ' file = "namespaces.toml", table = "damage_type" }\n'
)
"""A namespace registry declaring one namespace, whose records live beside it.

The smallest corpus `load_registry` accepts: every other namespace would pull
in a rules file this test has no reason to invent.
"""


@pytest.fixture
def rules_dir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Set up a rules directory: one namespace, and an empty Rulebook Index."""
    rules = tmp_path / "rules"
    rules.mkdir()
    (rules / "namespaces.toml").write_text(
        _NAMESPACES + '\n[damage_type.fire]\nname = "Fire"\ntodo = "Unwritten."\n'
    )
    (rules / "rulebook.toml").write_text('title = "Rulebook"\nsections = []\n')
    monkeypatch.setattr(config.paths, "rules", rules)
    return rules


@pytest.fixture
def workflows_dir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Point `config.paths.workflows` at a directory of this test's own."""
    workflows = tmp_path / "workflows"
    workflows.mkdir()
    monkeypatch.setattr(config.paths, "workflows", workflows)
    return workflows
