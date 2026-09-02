"""Every check `spf lint` makes over the committed corpus.

One command per corpus owns both gates: it loads the corpus and reports a Load
finding for anything that will not load, then reports Style findings only for
the files that did (ADR 0036). Build findings sit between them — an Army that
loads but asks its Race for something the Race does not offer. The linter flags
-- it never fixes.
"""

from spf.lint import latex, loading, registries
from spf.lint.collect import Finding, lint_race
from spf.lint.findings import LintFinding, format_finding, print_findings
from spf.lint.loading import (
    build_findings,
    probe_armies,
    probe_assets,
    probe_races,
    probe_render,
    probe_rules,
)
from spf.lint.registries import RegistryFinding, lint_registry

__all__ = [
    "Finding",
    "LintFinding",
    "RegistryFinding",
    "build_findings",
    "format_finding",
    "latex",
    "lint_race",
    "lint_registry",
    "loading",
    "print_findings",
    "probe_armies",
    "probe_assets",
    "probe_races",
    "probe_render",
    "probe_rules",
    "registries",
]
