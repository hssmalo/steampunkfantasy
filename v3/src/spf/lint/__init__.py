"""Style linting for Race data and for the rule registries.

Schema validation is a hard gate; this is a soft one that runs only on data
that already passes it (ADR 0016). The linter flags -- it never fixes.

The two sides are sibling commands rather than one: a broken `rules/*.toml`
should fail `just validate` and be skipped by its own linter, not silence the
Race linter with it.
"""

from spf.lint import latex, registries
from spf.lint.collect import Finding, lint_race
from spf.lint.registries import RegistryFinding, lint_registry

__all__ = [
    "Finding",
    "RegistryFinding",
    "latex",
    "lint_race",
    "lint_registry",
    "registries",
]
