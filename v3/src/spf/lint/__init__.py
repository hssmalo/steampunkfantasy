"""Every check `spf lint` makes over the committed corpus.

One command per corpus owns both gates: it loads the corpus and reports a Load
finding for anything that will not load, then reports Style findings only for
the files that did (ADR 0035). Build findings sit between them — an Army that
loads but asks its Race for something the Race does not offer. The linter flags
-- it never fixes.
"""

from spf.lint import latex, registries
from spf.lint.collect import Finding, lint_race
from spf.lint.findings import LintFinding, format_finding, print_findings
from spf.lint.registries import RegistryFinding, lint_registry

__all__ = [
    "Finding",
    "LintFinding",
    "RegistryFinding",
    "format_finding",
    "latex",
    "lint_race",
    "lint_registry",
    "print_findings",
    "registries",
]
