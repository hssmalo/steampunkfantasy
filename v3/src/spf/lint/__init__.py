"""Style linting for Race data.

Schema validation is a hard gate; this is a soft one that runs only on Races
that already pass it (ADR 0016). The linter flags -- it never fixes.
"""

from spf.lint.collect import Finding, lint_race

__all__ = ["Finding", "lint_race"]
