"""Tests for the three rules countdowns.

The two `todo` queries are pure functions over an already-loaded `Registry`,
so they get registries built by hand. They are tested apart because keeping
them apart is the point: a stub and an open question about a finished rule are
different things to the designer working the list.

`used_special_ids` walks a Race instead, and a Race cannot be built by hand
with invented ids -- the hard gate rejects them -- so it is exercised against
real Race data.
"""

from spf import countdown, races
from spf.registry import Registry
from spf.schemas import rules as r

WRITTEN = r.SpecialRuleConfig(name="Fear", slots=["assault"], effect="Enemies flee")
STUB = r.SpecialRuleConfig(name="Hide", slots=["unit"], todo="Rule text not written")
QUESTIONED = r.SpecialRuleConfig(
    name="Heal", slots=["unit"], effect="Remove a token", todo="Does it stack?"
)

REGISTRY = Registry(
    records={"special": {"fear": WRITTEN, "hide": STUB, "heal": QUESTIONED}},
    namespaces={
        "special": r.NamespaceConfig(
            name="Specials", file="special.toml", table="special"
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


def test_used_special_ids_reaches_every_kind_of_holder() -> None:
    """An id counts as used wherever in a Race it is written.

    One id per holder kind, so a holder dropped from the walk fails this
    rather than quietly enlarging the unreachable list.
    """
    used = countdown.used_special_ids([races.get_race("ork")])

    assert {
        "forward_position",  # Unit
        "pre_assault_retreat",  # Model, unit slot
        "not_yet_dead",  # Model
        "stench",  # Model, assault slot
        "terror",  # Equipment, unit slot
        "to_hit",  # Equipment, model slot
        "damage_on_deflect",  # Equipment, assault slot
        "limited_ammo",  # Equipment, range slot
    } <= used
