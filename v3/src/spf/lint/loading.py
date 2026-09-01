"""Load each corpus, and report what will not load or will not build.

`spf lint <corpus>` owns both gates over its corpus (ADR 0035): these probes
are the first one. A probe never raises — a corpus that cannot be read is the
answer, not an interruption — and it hands back what *did* load, so the style
pass that follows runs over exactly the files that yielded no Load finding.
"""

import json
import tomllib
from collections.abc import Callable, Iterable
from dataclasses import dataclass
from functools import partial
from pathlib import Path

import pydantic

from spf import races, registry, rules
from spf.armies import io
from spf.armies.build import ArmyList, army_violations
from spf.assets.profiles import check as check_profile
from spf.config import config
from spf.lint import latex
from spf.lint.findings import LintFinding
from spf.render.rulebook import build_rulebook
from spf.schemas import type_aliases as t
from spf.schemas.config import COMFYUI_ENV_NAMES
from spf.schemas.race import RaceConfig

LOAD = "load"
"""The rule column of a finding about a file that will not load."""

BUILD = "build"
"""The rule column of a finding about an Army its Race will not field."""

LATEX_MANIFEST = "templates/latex/requirements.toml"
"""Where the LaTeX package manifest lives, repo-relative."""

SITE_INDEX = "armies/site.toml"
"""Where the Site Index lives, repo-relative (ADR 0028)."""

# What a corpus cannot be read past. `tomllib` and `json` raise their own for a
# file that will not parse; a manifest naming a file that is not there, or a
# key that is not, raises the rest.
_UNREADABLE = (OSError, ValueError, KeyError, tomllib.TOMLDecodeError)


def _finding(file: str, message: str, *, location: str = "") -> LintFinding:
    """Build one Load finding."""
    return LintFinding(file=file, location=location, rule=LOAD, message=message)


def _pydantic_findings(file: str, error: pydantic.ValidationError) -> list[LintFinding]:
    """Report one Load finding per pydantic error, located at its own field.

    One line per error rather than one per file: a finding is meant to be
    grepped, and `str(err)` folds several problems into a paragraph.
    """
    return [
        _finding(
            file,
            str(detail["msg"]),
            location=".".join(str(part) for part in detail["loc"]),
        )
        for detail in error.errors()
    ]


def _findings_from(file: str, load: Callable[[], object]) -> list[LintFinding]:
    """Run a loader, turning whatever it raises into Load findings for `file`."""
    try:
        load()
    except pydantic.ValidationError as err:
        return _pydantic_findings(file, err)
    except _UNREADABLE as err:
        return [_finding(file, str(err))]
    return []


# ---------------------------------------------------------------------------
# Races
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class RaceProbe:
    """Which Races loaded, and why the rest did not."""

    findings: list[LintFinding]
    loaded: list[t.RaceName]
    broken: frozenset[str]


def probe_races() -> RaceProbe:
    """Load every `races/*.toml`, reporting one finding per schema error."""
    findings: list[LintFinding] = []
    loaded: list[t.RaceName] = []
    broken: set[str] = set()
    for race in races.list_races():
        file = f"races/{race}.toml"
        try:
            error = races.race_load_error(race)
        except _UNREADABLE as err:
            findings.append(_finding(file, str(err)))
            broken.add(race)
            continue
        if error is None:
            loaded.append(race)
        else:
            findings += _pydantic_findings(file, error)
            broken.add(race)
    return RaceProbe(findings=findings, loaded=loaded, broken=frozenset(broken))


# ---------------------------------------------------------------------------
# Rules
# ---------------------------------------------------------------------------


def probe_rules() -> list[LintFinding]:
    """Load every rule registry and the Rulebook Index.

    Each registry file is read on its own first, so a schema failure names the
    file it was authored in; only then is the whole registry assembled, which
    is what checks the declarations spanning files.
    """
    findings = [
        finding
        for file_name, load in registry.LOADERS.items()
        if (path := config.paths.rules / file_name).is_file()
        for finding in _findings_from(f"rules/{file_name}", partial(load, path))
    ]
    if findings:
        return findings

    # A cross-file failure is authored in the namespace registry: it is the
    # file that says which registries exist and where their records live.
    return [
        *_findings_from("rules/namespaces.toml", registry.load_registry),
        *_findings_from(f"rules/{rules.RULEBOOK_INDEX}", _build_rulebook),
    ]


def _build_rulebook() -> object:
    """Resolve the committed Rulebook Index, which is what validates it."""
    return build_rulebook(rules.get_rulebook(), rules_dir=config.paths.rules)


# ---------------------------------------------------------------------------
# Armies
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class LoadedArmy:
    """One Army that read cleanly, ready for the referential checks."""

    file: str
    army: ArmyList
    race_config: RaceConfig


@dataclass(frozen=True)
class ArmyProbe:
    """Which Armies loaded, and why the rest did not."""

    findings: list[LintFinding]
    loaded: list[LoadedArmy]


def probe_armies(*, broken_races: frozenset[str] = frozenset()) -> ArmyProbe:
    """Read every `armies/**/*.json` against its Race.

    An Army of a Race in `broken_races` is skipped in silence: the Race already
    reported the failure, and reporting it once, at its cause, is the rule
    (ADR 0016).
    """
    findings: list[LintFinding] = []
    loaded: list[LoadedArmy] = []
    for path in io.list_armies():
        file = f"armies/{path.relative_to(config.paths.armies).as_posix()}"
        try:
            data = json.loads(path.read_text())
            if data["race"] in broken_races:
                continue
            race_config = races.get_race(data["race"])
            errors = io.army_data_errors(data, cfg=race_config)
            army = None if errors else io.build_army_list(data, cfg=race_config)
        except _UNREADABLE as err:
            findings.append(_finding(file, str(err)))
            continue
        if army is None:
            findings += [_finding(file, error) for error in errors]
        else:
            loaded.append(LoadedArmy(file=file, army=army, race_config=race_config))
    return ArmyProbe(findings=findings, loaded=loaded)


def build_findings(loaded: Iterable[LoadedArmy]) -> list[LintFinding]:
    """Report every Army that loads but that its Race will not field.

    A third kind of finding, between Load and Style: the file read fine, and
    the Army is illegal rather than untidy (ADR 0035).
    """
    return [
        LintFinding(
            file=army.file,
            location=violation.location,
            rule=BUILD,
            message=violation.message,
        )
        for army in loaded
        for violation in army_violations(army.army, race_config=army.race_config)
    ]


# ---------------------------------------------------------------------------
# Render
# ---------------------------------------------------------------------------


def latex_manifest_path() -> Path:
    """Locate the LaTeX manifest, beside the templates it is a manifest for."""
    return config.paths.templates / "latex" / "requirements.toml"


def probe_render() -> list[LintFinding]:
    """Read the render inputs: the LaTeX manifest, the Site Index, the Packs.

    `pack.toml` and `site.toml` live under `armies/` but are render inputs, not
    Army data (ADR 0028, ADR 0035), so they are checked here.
    """
    return [
        *_findings_from(
            LATEX_MANIFEST, partial(latex.read_manifest, latex_manifest_path())
        ),
        *_probe_site_index(),
        *(
            finding
            for path in sorted(config.paths.armies.glob("*/pack.toml"))
            for finding in _probe_pack(path)
        ),
    ]


def _probe_site_index() -> list[LintFinding]:
    """Read the Site Index, and check that every Pack it names has an Index."""
    path = config.paths.armies / "site.toml"
    try:
        index = io.get_site_index(path)
    except pydantic.ValidationError as err:
        return _pydantic_findings(SITE_INDEX, err)
    except _UNREADABLE as err:
        return [_finding(SITE_INDEX, str(err))]
    return [
        _finding(f"armies/{entry.pack}/pack.toml", "no Army Pack Index at this path")
        for entry in index.packs
        if not (config.paths.armies / entry.pack / "pack.toml").is_file()
    ]


def _probe_pack(path: Path) -> list[LintFinding]:
    """Read one Army Pack Index."""
    file = f"armies/{path.relative_to(config.paths.armies).as_posix()}"
    return _findings_from(file, partial(io.get_army_pack, path))


# ---------------------------------------------------------------------------
# Assets
# ---------------------------------------------------------------------------


def probe_assets() -> list[LintFinding]:
    """Check each ComfyUI Environment's configured Profile against the disk.

    An Environment whose directory is absent is passed over rather than
    reported: `workflows/local/` is per-machine and gitignored, so a fresh
    clone legitimately has only the committed ones.
    """
    comfyui = config.assets.image.comfyui
    statuses = [
        check_profile(
            config.paths.workflows,
            env,
            comfyui.selected(env).profile,
            project_root=config.paths.project,
        )
        for env in COMFYUI_ENV_NAMES
    ]
    return [
        _finding(f"workflows/{status.env}", status.detail, location=status.profile)
        for status in statuses
        if status.state == "broken"
    ]
