"""Tests for the walk that applies the rules to a Race's entries.

`lint_entries` takes any mapping of key to something with a `.name`, so these
build stubs rather than real `UnitConfig`s -- constructing one would need
`shaken`, `orders`, `damage_tables`, `size` and `models`, none of which the
linter looks at.
"""

from dataclasses import dataclass

from spf.lint import collect, holders
from spf.schemas.config import LintConfig
from spf.schemas.race import (
    AssaultConfig,
    EquipmentConfig,
    ModelConfig,
    RaceConfig,
    RaceMetadata,
)
from spf.schemas.special import SpecialInstance

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


# ---------------------------------------------------------------------------
# Default equipment must fit the model's holder limits
# ---------------------------------------------------------------------------

_ASSAULT = AssaultConfig(
    strength=[1, 0, 0, 0],
    strength_die="4+",
    deflection=[1, 0, 0, 0],
    deflection_die="4+",
    damage="d4",
    ap=0,
)


def _equipment(name: str, *, requires: list[list[str]]) -> EquipmentConfig:
    """Build an equipment entry carrying only a name and its holder claims."""
    return EquipmentConfig(
        race="ogre",
        name=name,  # pyright: ignore[reportArgumentType]
        requires=requires,  # pyright: ignore[reportArgumentType]
    )


def _model(*, limits: list[str], defaults: list[str]) -> ModelConfig:
    """Build a model config carrying only its holder limits and default keys."""
    return ModelConfig(
        race="ogre",
        name="Scout Engineer",  # pyright: ignore[reportArgumentType]
        equipment_limit=limits,  # pyright: ignore[reportArgumentType]
        equipment=defaults,
        type=["Infantry"],
        assault=_ASSAULT,
    )


def test_defaults_within_the_limits_are_silent() -> None:
    """A model whose defaults fit has nothing to report."""
    model = _model(limits=["Hands:2"], defaults=["rifle"])
    catalogue = {"rifle": _equipment("Rifle", requires=[["Hands:2"]])}

    assert holders.check_default_equipment_fits(model, catalogue) is None


def test_defaults_claiming_an_undeclared_holder_are_reported() -> None:
    """The ogre scout engineer case: a Reserve Melee sword on a Hands-only model."""
    model = _model(limits=["Independent:∞", "Hands:2"], defaults=["ogre_sword_free"])
    catalogue = {
        "ogre_sword_free": _equipment("Ogre Sword", requires=[["Reserve Melee:1"]])
    }

    message = holders.check_default_equipment_fits(model, catalogue)

    assert message == "defaults claim Reserve Melee:1 but the limit is 0"


def test_defaults_are_measured_together_not_one_at_a_time() -> None:
    """Two defaults that each fit alone can still over-commit the holder."""
    model = _model(limits=["Hands:2"], defaults=["rifle", "pistol"])
    catalogue = {
        "rifle": _equipment("Rifle", requires=[["Hands:2"]]),
        "pistol": _equipment("Pistol", requires=[["Hands:1"]]),
    }

    message = holders.check_default_equipment_fits(model, catalogue)

    assert message == "defaults claim Hands:3 but the limit is 2"


def test_every_over_committed_holder_is_named() -> None:
    """One message covers all the holders that need fixing."""
    model = _model(limits=["Hands:1"], defaults=["rig"])
    catalogue = {"rig": _equipment("Rig", requires=[["Hands:2"], ["Grenades:1"]])}

    message = holders.check_default_equipment_fits(model, catalogue)

    assert message is not None
    assert "Hands:2 but the limit is 1" in message
    assert "Grenades:1 but the limit is 0" in message


def test_type_requirements_never_over_commit_a_holder() -> None:
    """`type:` says who may take the equipment, not where it sits."""
    model = _model(limits=["Hands:2"], defaults=["rifle"])
    catalogue = {
        "rifle": _equipment("Rifle", requires=[["Hands:2"], ["type:Infantry"]])
    }

    assert holders.check_default_equipment_fits(model, catalogue) is None


def test_over_committed_defaults_surface_as_a_finding() -> None:
    """The rule reaches `lint_race_config` and locates the model it fired on."""
    race_config = RaceConfig(
        races={"ogre": RaceMetadata(name="Ogre")},
        units={},
        models={
            "ogre_scout_engineer": _model(
                limits=["Hands:2"], defaults=["ogre_sword_free"]
            )
        },
        equipment={
            "ogre_sword_free": _equipment("Ogre Sword", requires=[["Reserve Melee:1"]])
        },
    )

    findings = collect.lint_race_config("ogre", race_config, CONVENTIONS, pools={})

    (finding,) = [f for f in findings if f.rule == "default-equipment-limit"]
    assert finding.section == "models"
    assert finding.key == "ogre_scout_engineer"
    assert "Reserve Melee:1" in finding.message


_POOLS = {"fog": {"ignores_weather": "Ignores the weather"}}
"""One rule's variants, the way the registry holds them."""


def _race_carrying(instance: dict[str, object]) -> RaceConfig:
    """Build a Race whose only Special is one instance of `fog`, on equipment."""
    equipment = _equipment("Ogre Sword", requires=[["Hands:1"]])
    return RaceConfig(
        races={"ogre": RaceMetadata(name="Ogre")},
        units={},
        models={},
        equipment={
            "ogre_sword_free": equipment.model_copy(
                update={"unit_specials": {"fog": [SpecialInstance(**instance)]}}  # pyright: ignore[reportArgumentType]
            )
        },
    )


def test_longhand_prose_surfaces_as_a_finding() -> None:
    """The variant rule reaches `lint_race_config` and locates its holder."""
    race_config = _race_carrying({"text": "Ignores the weather"})

    findings = collect.lint_race_config("ogre", race_config, CONVENTIONS, pools=_POOLS)

    (finding,) = [f for f in findings if f.rule == "variant-longhand"]
    assert finding.section == "equipment"
    assert finding.key == "ogre_sword_free"
    assert "ignores_weather" in finding.message


def test_a_race_the_pools_say_nothing_about_is_clean() -> None:
    race_config = _race_carrying({"text": "Ignores the weather"})

    findings = collect.lint_race_config("ogre", race_config, CONVENTIONS, pools={})

    assert [f for f in findings if f.rule == "variant-longhand"] == []
