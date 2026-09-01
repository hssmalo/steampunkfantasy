"""Tests for the three rules countdowns.

The two `todo` queries are pure functions over an already-loaded `Registry`,
so they get registries built by hand. They are tested apart because keeping
them apart is the point: a stub and an open question about a finished rule are
different things to the designer working the list.

`used_special_ids` walks a Race instead. It gets one built here too: a
Registry installed behind the load-time gate is what lets a Race carry
invented ids, one per Holder, so the walk is checked against a Race that
holds nothing else.
"""

from spf import countdown
from spf.registry import Registry
from spf.schemas import rules as r
from tests.conftest import (
    InstallRegistry,
    synthetic_assault,
    synthetic_equipment,
    synthetic_model,
    synthetic_race,
    synthetic_registry,
    synthetic_unit,
)

WRITTEN = r.SpecialRuleConfig(name="Fear", slots=["assault"], effect="Enemies flee")
STUB = r.SpecialRuleConfig(name="Hide", slots=["unit"], todo="Rule text not written")
QUESTIONED = r.SpecialRuleConfig(
    name="Heal", slots=["unit"], effect="Remove a token", todo="Does it stack?"
)

REGISTRY = Registry(
    records={"special": {"fear": WRITTEN, "hide": STUB, "heal": QUESTIONED}},
    namespaces={
        "special": r.NamespaceConfig(
            name="Specials", label="special", file="special.toml", table="special"
        )
    },
)


def test_unwritten_lists_only_stubs() -> None:
    """A record with no meaning-bearing field is a stub, whatever else it has."""
    assert [entry.key for entry in countdown.unwritten(REGISTRY)] == ["hide"]


def test_open_questions_list_only_written_rules() -> None:
    """A `todo` on a written rule is a question, not an unwritten rule.

    Completeness is at-least-one-of, so a finished rule may carry an open
    design question; counting it as a stub is what the relaxation was made to
    avoid.
    """
    assert [entry.key for entry in countdown.open_questions(REGISTRY)] == ["heal"]


def test_the_two_todo_sections_do_not_overlap() -> None:
    """Every record carrying a `todo` lands in exactly one of the two."""
    stubs = {entry.key for entry in countdown.unwritten(REGISTRY)}
    questions = {entry.key for entry in countdown.open_questions(REGISTRY)}

    assert stubs & questions == set()
    assert stubs | questions == {"hide", "heal"}


def test_entry_carries_the_todo_text() -> None:
    """The countdown prints the question, so the entry has to carry it."""
    (entry,) = countdown.open_questions(REGISTRY)

    assert entry.namespace == "special"
    assert entry.name == "Heal"
    assert entry.todo == "Does it stack?"


def test_unreachable_lists_ids_no_instance_names() -> None:
    """A declared Special no Race writes an instance of is unreachable."""
    entries = countdown.unreachable(REGISTRY, used={"fear"})

    assert [entry.key for entry in entries] == ["heal", "hide"]


def test_unreachable_is_silent_when_every_id_is_used() -> None:
    """Unreachability is a property of the corpus, not of the registry alone."""
    assert countdown.unreachable(REGISTRY, used={"fear", "hide", "heal"}) == []


_HOLDERS = (
    "on_unit",
    "on_model_as_unit",
    "on_model",
    "on_model_assault",
    "on_equipment_as_unit",
    "on_equipment_as_model",
    "on_equipment_assault",
    "on_equipment_range",
)
"""One invented Special id per Holder a Race can write an Instance on."""


def _instance(key: str) -> dict[str, list[dict[str, str]]]:
    """One Instance of `key`, as a Holder's Specials table writes it."""
    return {key: [{"text": "Once per round."}]}


def test_used_special_ids_reaches_every_kind_of_holder(
    install_registry: InstallRegistry,
) -> None:
    """An id counts as used wherever in a Race it is written.

    One id per Holder, so a Holder dropped from the walk fails this rather
    than quietly enlarging the unreachable list.
    """
    install_registry(synthetic_registry(specials=dict.fromkeys(_HOLDERS)))
    unit, model_unit, model, model_assault, *equipment = _HOLDERS
    equip_unit, equip_model, equip_assault, equip_range = equipment
    race = synthetic_race(
        units={"squad": synthetic_unit(specials=_instance(unit))},
        models={
            "soldier": synthetic_model(
                unit_specials=_instance(model_unit),
                specials=_instance(model),
                assault=synthetic_assault(specials=_instance(model_assault)),
            )
        },
        equipment={
            "knife": synthetic_equipment(
                name="Knife",
                cost=None,
                upgrade_all=None,
                unit_specials=_instance(equip_unit),
                model_specials=_instance(equip_model),
                assault={"specials": _instance(equip_assault)},
                range={
                    "range": 12,
                    "angle": [True, False, False, False],
                    "damage": "d6",
                    "ap": 0,
                    "specials": _instance(equip_range),
                },
            )
        },
    )

    assert countdown.used_special_ids([race]) == set(_HOLDERS)
