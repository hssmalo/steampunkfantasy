"""The `spf lint` commands: one per corpus, plus `all`.

Each command owns both gates over its corpus (ADR 0035). It loads the corpus
itself, reports a failure to load as a Load finding, and reports Style findings
only for the files that loaded — so a defect is reported once, at its cause,
and never twice. Findings are collected across the whole corpus and printed
before the single exit: there is exactly one severity, and lint speaking means
the build fails.
"""

import cyclopts

from spf import lint
from spf.config import config
from spf.lint import latex, loading
from spf.lint.findings import LintFinding

MISSING_PACKAGE = "missing-package"
"""The style rule a LaTeX template using an unlisted package breaks."""


def add_commands(app: cyclopts.App) -> None:
    """Add the lint commands to the CLI."""
    app.command(lint_races, name="races")
    app.command(lint_rules, name="rules")
    app.command(lint_armies, name="armies")
    app.command(lint_render, name="render")
    app.command(lint_assets, name="assets")
    app.command(lint_all, name="all")


def _report(findings: list[LintFinding]) -> None:
    """Print every finding, then fail if there was one."""
    lint.print_findings(findings)
    if findings:
        raise SystemExit(1)


# ---------------------------------------------------------------------------
# The five corpora
# ---------------------------------------------------------------------------


def races_findings(probe: loading.RaceProbe | None = None) -> list[LintFinding]:
    """Return every finding over `races/*.toml`.

    Takes an already-run probe when the caller has one, so `spf lint all` loads
    each Race once rather than once per corpus that depends on it.
    """
    probe = probe if probe is not None else loading.probe_races()
    return [
        *probe.findings,
        *(
            LintFinding(
                file=f"races/{finding.race}.toml",
                location=f"{finding.section}.{finding.key}",
                rule=finding.rule,
                message=finding.message,
            )
            for race in probe.loaded
            for finding in lint.lint_race(race)
        ),
    ]


def rules_findings() -> list[LintFinding]:
    """Return every finding over the rule registries and the Rulebook Index.

    The style pass walks whatever the probe could assemble, which holds the
    namespaces whose files read and no others -- so a broken `hexes.toml`
    costs the corpus its hex records without silencing the rest.
    """
    probe = loading.probe_rules()
    if probe.registry is None:
        return probe.findings
    return [
        *probe.findings,
        *(
            LintFinding(
                file=f"rules/{finding.file}",
                location=f"{finding.namespace}.{finding.key}",
                rule=finding.rule,
                message=finding.message,
            )
            for finding in lint.lint_registry(probe.registry, config.lint)
        ),
    ]


def armies_findings(*, broken_races: frozenset[str]) -> list[LintFinding]:
    """Return every finding over `armies/**/*.json`.

    Armies have no style rules of their own: their names are the Race's, and
    the Race is where a name is linted.
    """
    probe = loading.probe_armies(broken_races=broken_races)
    return [*probe.findings, *loading.build_findings(probe.loaded)]


def render_findings() -> list[LintFinding]:
    """Return every finding over the render inputs.

    The LaTeX manifest's style pass is a check of one authored file against
    another, so it runs only once the manifest itself has read.
    """
    findings = loading.probe_render()
    if any(finding.file == loading.LATEX_MANIFEST for finding in findings):
        return findings
    return [
        *findings,
        *(
            LintFinding(
                file=loading.LATEX_MANIFEST,
                location="",
                rule=MISSING_PACKAGE,
                message=name,
            )
            for name in latex.unlisted_packages(
                loading.latex_templates_dir(), loading.latex_manifest_path()
            )
        ),
    ]


def assets_findings() -> list[LintFinding]:
    """Return every finding over the ComfyUI Profiles."""
    return loading.probe_assets()


# ---------------------------------------------------------------------------
# The commands
# ---------------------------------------------------------------------------


def lint_races() -> None:
    """Load every Race, and check what loads for name and key consistency."""
    _report(races_findings())


def lint_rules() -> None:
    """Load the rule registries and the Rulebook Index, and check what loads."""
    _report(rules_findings())


def lint_armies() -> None:
    """Load every Army, and check it against the catalogue its Race offers."""
    _report(armies_findings(broken_races=loading.probe_races().broken))


def lint_render() -> None:
    """Load the render inputs: the LaTeX manifest, the Site and Pack Indexes."""
    _report(render_findings())


def lint_assets() -> None:
    """Check each ComfyUI Environment's configured Profile against the disk."""
    _report(assets_findings())


def lint_all() -> None:
    """Lint every corpus in one process, and fail once at the end.

    Dependency order: the Races are loaded first, and the probe is shared, so
    `armies` can suppress the Armies of a Race that already failed rather than
    loading every Race a second time (ADR 0034).
    """
    races = loading.probe_races()
    _report(
        [
            *races_findings(races),
            *rules_findings(),
            *armies_findings(broken_races=races.broken),
            *render_findings(),
            *assets_findings(),
        ]
    )
