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
from spf.lint import holders, names, orders, prose, variants
from spf.registry import Registry, load_registry
from spf.schemas import type_aliases as t
from spf.schemas.config import LintConfig
from spf.schemas.race import RaceConfig, special_slots


class Named(Protocol):
    """Anything carrying a display name -- a Unit, Model or Equipment entry.

    A read-only property rather than an attribute, so frozen entries satisfy
    it: the linter only ever reads a name.
    """

    @property
    def name(self) -> str:
        """The display name shown to players."""
        ...


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
    return [
        Finding(race=race, section=section, key=key, rule=rule, message=message)
        for key, entry in entries.items()
        for rule, message in names.check_name(key, entry.name, conventions)
    ]


def lint_race_config(
    race: t.RaceName,
    race_config: RaceConfig,
    conventions: LintConfig,
    *,
    pools: Mapping[str, Mapping[str, str]],
    registry: Registry,
) -> list[Finding]:
    """Return every finding for an already-loaded, schema-valid Race.

    `pools` is each rule's variants. Required rather than defaulted: a caller
    that has no pools says so with `{}`, which is not the same claim as having
    forgotten to pass them. The registry travels beside them because a pool is
    filled with an instance's args before it is compared (ADR 0037).
    """
    findings: list[Finding] = []
    for section, key, specials in special_slots(race_config):
        findings += [
            Finding(
                race=race,
                section=section,
                key=key,
                rule="variant-longhand",
                message=f"'{identifier}': {message}",
            )
            for identifier, message in variants.check_specials(
                specials, pools, registry=registry
            )
        ]
    if (message := names.check_capitalized(race_config.races[race].name)) is not None:
        findings.append(
            Finding(
                race=race,
                section="races",
                key=race,
                rule="race-capitalized",
                message=message,
            )
        )
    for model_key, model in race_config.models.items():
        message = holders.check_default_equipment_fits(model, race_config.equipment)
        if message is not None:
            findings.append(
                Finding(
                    race=race,
                    section="models",
                    key=model_key,
                    rule="default-equipment-limit",
                    message=message,
                )
            )
    for equipment_key, equipment in race_config.equipment.items():
        message = holders.check_requires_one_holder(equipment)
        if message is not None:
            findings.append(
                Finding(
                    race=race,
                    section="equipment",
                    key=equipment_key,
                    rule="or-group-one-holder",
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
    findings += lint_prose(race, race_config)
    findings += lint_order_cells(race, race_config, conventions)
    return findings


def lint_order_cells(
    race: t.RaceName, race_config: RaceConfig, conventions: LintConfig
) -> list[Finding]:
    """Apply the order rules to every cell of every Order Card the Race prints."""
    vocabulary = frozenset(conventions.order_names)
    return [
        Finding(
            race=race,
            section=location.split(".", 1)[0],
            key=location.split(".", 1)[-1],
            rule=rule,
            message=message,
        )
        for location, cell in orders.walk_cells(race_config.model_dump())
        for rule, message in orders.check_cell(cell, vocabulary)
    ]


def lint_prose(race: t.RaceName, race_config: RaceConfig) -> list[Finding]:
    """Apply the prose rules to every sentence field the Race declares.

    The walk is over the dumped model, so it reaches prose wherever the schema
    puts it -- a Unit's `tip`, a Special instance's `text`, a damage table's
    `notes` -- without this function having to name each place.
    """
    return [
        Finding(
            race=race,
            section=location.split(".", 1)[0],
            key=location.split(".", 1)[-1],
            rule=rule,
            message=message,
        )
        for location, value in prose.walk_prose(race_config.model_dump())
        for rule, message in prose.check_prose(value)
    ]


def lint_race(race: t.RaceName) -> list[Finding]:
    """Load `race` and return its findings, using the configured conventions."""
    registry = load_registry()
    pools = {
        identifier: rule.variants for identifier, rule in registry.specials.items()
    }
    return lint_race_config(
        race, races.get_race(race), config.lint, pools=pools, registry=registry
    )
