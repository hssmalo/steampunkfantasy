"""Walk a Race's entries and apply the name rules to each.

The walk is split from disk access on purpose: `lint_entries` takes any
mapping of key to something with a `.name`, so it is exercised with plain
stubs. `lint_race` is the thin layer that loads real config and Race data.
"""

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Protocol

from spf import races
from spf.config import config
from spf.lint import rules
from spf.schemas import type_aliases as t
from spf.schemas.config import LintConfig
from spf.schemas.race import RaceConfig


class Named(Protocol):
    """Anything carrying a display name -- a Unit, Model or Equipment entry."""

    name: str


@dataclass(frozen=True)
class Finding:
    """One rule violation, located precisely enough to go and fix it."""

    race: str
    section: str
    key: str
    rule: str
    message: str


def lint_entries(
    race: str, section: str, entries: Mapping[str, Named], conventions: LintConfig
) -> list[Finding]:
    """Apply every entry-level rule to each key/name pair in `entries`."""
    checks = {
        "key-name": lambda key, name: rules.check_key_name(key, name, conventions),
        "no-underscore": lambda _key, name: rules.check_no_underscore(name),
        "title-case": lambda _key, name: rules.check_title_case(
            name, conventions.function_words
        ),
        "key-lowercase": lambda key, _name: rules.check_key_lowercase(key),
    }
    return [
        Finding(race=race, section=section, key=key, rule=rule, message=message)
        for key, entry in entries.items()
        for rule, check in checks.items()
        if (message := check(key, entry.name)) is not None
    ]


def lint_race_config(
    race: t.RaceName, race_config: RaceConfig, conventions: LintConfig
) -> list[Finding]:
    """Return every finding for an already-loaded, schema-valid Race."""
    findings: list[Finding] = []
    if (message := rules.check_capitalized(race_config.races[race].name)) is not None:
        findings.append(
            Finding(
                race=race,
                section="races",
                key=race,
                rule="race-capitalized",
                message=message,
            )
        )
    sections: dict[str, Mapping[str, Named]] = {
        "units": race_config.units,
        "models": race_config.models,
        "equipment": race_config.equipment,
    }
    for section, entries in sections.items():
        findings.extend(lint_entries(race, section, entries, conventions))
    return findings


def lint_race(race: t.RaceName) -> list[Finding]:
    """Load `race` and return its findings, using the configured conventions."""
    return lint_race_config(race, races.get_race(race), config.lint)
