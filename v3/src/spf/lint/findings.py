"""The one finding type every corpus reports, and the one way it is printed.

A Load finding, a Build finding and a Style finding differ only in their `rule`
column (ADR 0036), so one shape carries all three and one renderer prints them.
"""

from collections.abc import Iterable
from dataclasses import dataclass

from spf.console import stdout


@dataclass(frozen=True)
class LintFinding:
    """One finding, located precisely enough to go and fix it."""

    file: str
    """Repo-relative path, e.g. `races/ork.toml`."""

    location: str
    """Dotted path within the file, e.g. `units.archer.cost.mp`; empty when
    the finding is about the file as a whole."""

    rule: str
    """`load`, `build`, or the name of a style rule."""

    message: str


def format_finding(finding: LintFinding) -> str:
    """Render one finding as its columns, two spaces apart.

    An empty column is dropped rather than padded, so a file-level finding
    stays three columns wide instead of carrying a hole where a location would
    have been.
    """
    columns = (finding.file, finding.location, finding.rule, finding.message)
    return "  ".join(column for column in columns if column)


def print_findings(findings: Iterable[LintFinding]) -> None:
    """Print one line per finding.

    Soft-wrapped so a finding is always exactly one line: these are meant to be
    grepped, and Rich would otherwise fold the long ones at the terminal width,
    splitting a key away from its rule.

    Markup is off because a finding quotes the data, and the data has square
    brackets in it -- an order cell `A[f, fly]` would otherwise print as `A`,
    with Rich having read the argument list as a style tag.
    """
    for finding in findings:
        stdout.print(
            format_finding(finding), highlight=False, markup=False, soft_wrap=True
        )
