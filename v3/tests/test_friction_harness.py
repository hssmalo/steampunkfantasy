"""Tests for the mutation logic behind `just test-friction`.

Pure string-in, string-out: these never run pytest and never touch the
committed corpus.
"""

from pathlib import Path
from typing import Any, cast

import pytest
import tomlkit

import test_friction as friction

RACE_TOML = """\
[races]

[races.dwarf]
name = "Dwarf"
description = "Sturdy."

[units]

[units.dwarf_infantry]
race = "dwarf"
name = "Dwarf Infantry"
models = ["dwarf_infantry", "dwarf_infantry"]
armor = [8, 6, 5, 4]
cost.mp = 16
description = "Wields a musket"

[[units.dwarf_infantry.specials.resistance]]
args.version = "damage_type.poison"
args.N = 2
text = "Shrugs off poison."

[models]

[models.dwarf_infantry]
name = "Dwarf Infantry"
assault.strength = [2, 1, 1, 1]
assault.ap = "N/A"
"""


def _keys(text: str) -> set[tuple[str, ...]]:
    """Every key path in a document, values discarded."""

    def walk(node: object, prefix: tuple[str, ...]) -> set[tuple[str, ...]]:
        found: set[tuple[str, ...]] = set()
        if isinstance(node, dict):
            for key, value in node.items():
                found.add((*prefix, str(key)))
                found |= walk(value, (*prefix, str(key)))
        elif isinstance(node, list):
            for index, value in enumerate(node):
                found |= walk(value, (*prefix, str(index)))
        return found

    return walk(tomlkit.parse(text), ())


def _target(field: str, targets: list[friction.Target]) -> friction.Target:
    return next(target for target in targets if target.field == field)


def _value_at(text: str, keys: tuple[str | int, ...]) -> object:
    node: object = tomlkit.parse(text)
    for key in keys:
        node = cast("dict[Any, Any]", node)[key]
    return node


#
# Scalar mutation
#


def test_mutate_string_appends_a_title_case_marker() -> None:
    """The marker must survive `spf race lint`'s title-case rule."""
    assert friction.mutate_value("Sturdy.") == "Sturdy. Zz"


def test_mutate_integer_steps_by_one() -> None:
    assert friction.mutate_value(3) == 4


def test_mutate_integer_list_steps_its_first_entry() -> None:
    """Arity is structure, so the list keeps its length."""
    assert friction.mutate_value([8, 6, 5, 4]) == [9, 6, 5, 4]


@pytest.mark.parametrize("value", [True, 1.5, [], ["a", "b"], {}])
def test_unmutable_values_yield_none(value: object) -> None:
    """Anything that is not prose or a number is left to the linters."""
    assert friction.mutate_value(value) is None


#
# Finding targets
#


def test_targets_cover_prose_and_numbers() -> None:
    fields = {target.field for target in friction.find_targets(RACE_TOML)}

    assert {"name", "description", "armor", "mp", "N", "text"} <= fields


def test_targets_reach_into_arrays_of_tables() -> None:
    target = _target("text", friction.find_targets(RACE_TOML))

    assert target.keys == (
        "units",
        "dwarf_infantry",
        "specials",
        "resistance",
        0,
        "text",
    )


def test_reference_valued_fields_are_not_targets() -> None:
    """A Model list or a `race` key names other records; editing one is a rename."""
    fields = {target.field for target in friction.find_targets(RACE_TOML)}

    assert "models" not in fields
    assert "race" not in fields
    assert "version" not in fields


def test_unmutable_values_are_not_targets() -> None:
    """`assault.ap = "N/A"` is in the allowlist but carries no number to step."""
    keys = {target.keys for target in friction.find_targets(RACE_TOML)}

    assert ("models", "dwarf_infantry", "assault", "ap") not in keys


#
# Applying a mutation
#


def test_applied_mutation_changes_exactly_one_value() -> None:
    target = _target("description", friction.find_targets(RACE_TOML))

    mutated = friction.apply_mutation(RACE_TOML, target)

    assert _value_at(mutated, target.keys) == "Sturdy. Zz"
    assert _value_at(mutated, ("races", "dwarf", "name")) == "Dwarf"


def test_no_mutation_alters_the_key_structure() -> None:
    """Renames and deletions are allowed to break tests, so never produce one."""
    for target in friction.find_targets(RACE_TOML):
        mutated = friction.apply_mutation(RACE_TOML, target)

        assert _keys(mutated) == _keys(RACE_TOML), target.keys


def test_applied_mutation_reaches_a_dotted_key() -> None:
    target = _target("mp", friction.find_targets(RACE_TOML))

    mutated = friction.apply_mutation(RACE_TOML, target)

    assert _value_at(mutated, ("units", "dwarf_infantry", "cost", "mp")) == 17


def test_applied_mutation_reaches_a_nested_list() -> None:
    target = _target("strength", friction.find_targets(RACE_TOML))

    mutated = friction.apply_mutation(RACE_TOML, target)

    assert _value_at(mutated, target.keys) == [3, 1, 1, 1]


def test_untouched_lines_keep_their_formatting() -> None:
    target = _target("mp", friction.find_targets(RACE_TOML))

    mutated = friction.apply_mutation(RACE_TOML, target)

    assert 'models = ["dwarf_infantry", "dwarf_infantry"]' in mutated


#
# Sampling
#


def _targets(count: int, field: str, name: str) -> list[friction.Target]:
    return [
        friction.Target(path=Path(f"{name}{index}.toml"), keys=(field,), field=field)
        for index in range(count)
    ]


def test_sample_covers_every_field_once() -> None:
    targets = _targets(5, "description", "a") + _targets(5, "mp", "b")

    sampled = friction.sample_targets(targets, per_field=1, seed=0)

    assert {target.field for target in sampled} == {"description", "mp"}
    assert len(sampled) == 2


def test_sample_is_deterministic_for_a_seed() -> None:
    targets = _targets(20, "description", "a")

    assert friction.sample_targets(targets, per_field=3, seed=7) == (
        friction.sample_targets(targets, per_field=3, seed=7)
    )


def test_sample_spreads_a_field_across_files() -> None:
    """One file's every `description` would be a much weaker sample."""
    targets = [
        friction.Target(
            path=Path(f"{name}.toml"), keys=("description", index), field="description"
        )
        for name in "abc"
        for index in range(5)
    ]

    sampled = friction.sample_targets(targets, per_field=3, seed=1)

    assert len({target.path for target in sampled}) == 3


def test_sample_keeps_everything_when_asked_for_the_full_sweep() -> None:
    targets = _targets(5, "description", "a")

    assert friction.sample_targets(targets, per_field=None, seed=0) == targets


#
# Reading a pytest run
#

PYTEST_OUTPUT = """\
.....F...E...
=================================== FAILURES ===================================
FAILED is a word that also opens this traceback line
=========================== short test summary info ============================
FAILED tests/render/test_army.py::test_rules - AssertionError: assert 'a' in 'b'
FAILED tests/render/test_army.py::test_rules - AssertionError: assert 'a' in 'b'
ERROR tests/lint/test_latex.py::test_manifest
1 failed, 1 error, 11 passed in 3.14s
"""


def test_failures_are_read_as_test_ids() -> None:
    """The id, not the `FAILED` marker in front of it, and each one once."""
    assert friction.parse_failures(PYTEST_OUTPUT) == [
        "tests/lint/test_latex.py::test_manifest",
        "tests/render/test_army.py::test_rules",
    ]


def test_a_clean_run_reports_nothing() -> None:
    assert friction.parse_failures("....\n12 passed in 1.00s\n") == []
