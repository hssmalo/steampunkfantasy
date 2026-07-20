"""Tests for the walk that applies the rules to a Race's entries.

`lint_entries` takes any mapping of key to something with a `.name`, so these
build stubs rather than real `UnitConfig`s -- constructing one would need
`shaken`, `orders`, `damage_tables`, `size` and `models`, none of which the
linter looks at.
"""

from dataclasses import dataclass

from spf.lint import collect
from spf.schemas.config import LintConfig

CONVENTIONS = LintConfig(
    aliases={"darkelf": "dark_elf"},
    optional_key_prefixes=["greater_"],
    optional_key_suffixes=["_free"],
    function_words=["of", "with", "in"],
)


@dataclass(frozen=True)
class Entry:
    """A stand-in for a Unit, Model or Equipment entry."""

    name: str


def test_clean_entries_produce_no_findings() -> None:
    """Entries that satisfy every rule are silent."""
    entries = {"elf_bow": Entry("Elf Bow"), "seeker_arrows": Entry("Seeker Arrows")}

    assert collect.lint_entries("elf", "equipment", entries, CONVENTIONS) == []


def test_finding_locates_the_violation() -> None:
    """A finding carries race, section, key and rule so it can be acted on."""
    entries = {"sauropod_riders": Entry("Sauropod Rider")}

    (finding,) = collect.lint_entries("elf", "units", entries, CONVENTIONS)

    assert finding.race == "elf"
    assert finding.section == "units"
    assert finding.key == "sauropod_riders"
    assert finding.rule == "key-name"


def test_one_entry_can_break_several_rules() -> None:
    """Every rule runs against every entry; they are not short-circuited."""
    entries = {"gasmask": Entry("Gas mask assault training")}

    findings = collect.lint_entries("darkelf", "equipment", entries, CONVENTIONS)

    assert {finding.rule for finding in findings} == {"key-name", "title-case"}


def test_entries_are_reported_in_declaration_order() -> None:
    """Findings follow the order of the source file, for a stable report."""
    entries = {"beta": Entry("Beta Two"), "alpha": Entry("Alpha One")}

    findings = collect.lint_entries("elf", "models", entries, CONVENTIONS)

    assert [finding.key for finding in findings] == ["beta", "alpha"]


def test_title_case_cannot_see_past_an_underscore() -> None:
    """An underscore hides the casing defect behind it, so fix it first.

    `Pegasus_rider` is a single whitespace-delimited word starting uppercase,
    so `title-case` has nothing to say until `no-underscore` is resolved --
    only then does `Pegasus rider` surface as a second finding. This is why
    the data fixes go underscores first, then casing, then the key.
    """
    underscored = {"pegasus_rider": Entry("Pegasus_rider")}
    despaced = {"pegasus_rider": Entry("Pegasus rider")}

    first_pass = collect.lint_entries("elf", "models", underscored, CONVENTIONS)
    second_pass = collect.lint_entries("elf", "models", despaced, CONVENTIONS)

    assert [finding.rule for finding in first_pass] == ["no-underscore"]
    assert [finding.rule for finding in second_pass] == ["title-case"]
