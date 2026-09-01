"""Tests for `spf special list` and `spf special show`.

Both commands read the Registry, and `show` walks the Races on top of it, so
these install a Registry and a Race of their own rather than coupling to
`rules/special.toml` and `races/` (ADR 0033). `special_rows` and
`special_record` are pure functions over a Registry, and take one directly.
"""

import re
from collections.abc import Callable
from pathlib import Path

import pydantic
import pytest
from cyclopts.exceptions import CycloptsError

from spf import races
from spf.config import config
from spf.frontends.cli import app
from spf.frontends.cli.special import (
    SpecialRecord,
    _print_record,
    special_record,
    special_rows,
)
from spf.registry import Registry
from spf.schemas.race import EquipmentConfig, RaceConfig
from spf.schemas.rules import SpecialRuleConfig
from spf.schemas.special import SpecialInstance, Specials
from spf.schemas.type_aliases import RaceName
from tests.conftest import (
    InstallRegistry,
    synthetic_assault,
    synthetic_equipment,
    synthetic_model,
    synthetic_race,
    synthetic_registry,
    synthetic_special,
    unwrapped,
    write_race_toml,
)

_ROW = re.compile(r"^(?P<marks>[UMAR ]{4}) (?P<label>\S+)")
"""A printed row: the UMAR column, then the Identifier and its Signature."""

type InstallRaces = Callable[..., None]
"""The `install_races` fixture: the Races to put on disk in, nothing out."""


@pytest.fixture
def install_races(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> InstallRaces:
    """Answer `spf.races` from Races this test wrote, rather than from `races/`.

    `show` walks every Race there is, so the corpus on disk is one of its
    inputs; a test about which Races it names supplies its own.
    """

    def install(*written: RaceConfig) -> None:
        for race in written:
            write_race_toml(tmp_path, race)
        monkeypatch.setattr(config.paths, "races", tmp_path)

    return install


def _break_race(name: RaceName, *, monkeypatch: pytest.MonkeyPatch) -> None:
    """Make the named Race fail to validate, the way a broken file would."""
    broken = pydantic.ValidationError.from_exception_data("RaceConfig", [])
    real_get_race = races.get_race

    def get_race(race_name: RaceName) -> RaceConfig:
        if race_name == name:
            raise broken
        return real_get_race(race_name)

    monkeypatch.setattr(races, "get_race", get_race)


def _assault_rule() -> SpecialRuleConfig:
    """Build a Special that only an Assault slot may hold."""
    return synthetic_special(slots=["assault"])


def _list(*args: str) -> None:
    app(["special", "list", *args], exit_on_error=False, result_action="return_value")


def _lines(
    command: Callable[[str], None],
    argument: str,
    *,
    capsys: pytest.CaptureFixture[str],
) -> list[str]:
    """Run a command and read its output back as stripped, non-empty lines."""
    command(argument)
    return [
        line.strip() for line in capsys.readouterr().out.splitlines() if line.strip()
    ]


def _registry(**specials: SpecialRuleConfig) -> Registry:
    return Registry(records={"special": dict(specials)})


def _rule(**kwargs: object) -> SpecialRuleConfig:
    kwargs.setdefault("name", "Rule")
    kwargs.setdefault("slots", ["unit"])
    return SpecialRuleConfig.model_validate(kwargs)


def test_rows_come_back_sorted_by_identifier() -> None:
    registry = _registry(
        zeal=_rule(effect="Zealous."),
        aim=_rule(effect="Aimed."),
        march=_rule(effect="Marching."),
    )

    rows = special_rows(registry)

    assert [row.label for row in rows] == ["aim", "march", "zeal"]


def test_a_multi_slot_special_is_one_row_with_combined_marks() -> None:
    # The list is a view of the Registry, where a multi-Slot Special is one
    # record, so it stays one row with both positions marked.
    registry = _registry(to_hit=_rule(slots=["unit", "range"], effect="Hits."))

    (row,) = special_rows(registry)

    assert row.marks == "U  R"


def test_a_single_slot_specials_marks_match_the_show_column() -> None:
    registry = _registry(
        aim=_rule(slots=["unit"], effect="."),
        fend=_rule(slots=["model"], effect="."),
        hack=_rule(slots=["assault"], effect="."),
        snipe=_rule(slots=["range"], effect="."),
    )

    marks = {row.label: row.marks for row in special_rows(registry)}

    assert marks == {"aim": "U   ", "fend": " M  ", "hack": "  A ", "snipe": "   R"}


def test_the_signature_is_appended_uninterpolated() -> None:
    # Uninterpolated: the list is a view of the record, and the placeholder is
    # what tells a reader the Special takes an argument at all.
    registry = _registry(
        ork_reroll=_rule(
            signature="[{N}]",
            variables={"N": {"type": "int", "min": 1}},
            effect="Reroll.",
        )
    )

    (row,) = special_rows(registry)

    assert row.label == "ork_reroll[{N}]"


def test_a_written_rules_text_is_its_effect() -> None:
    registry = _registry(aim=_rule(effect="Aim carefully."))

    (row,) = special_rows(registry)

    assert row.text == "Aim carefully."
    assert row.is_stub is False


def test_a_slot_keeps_every_special_declaring_it() -> None:
    # A multi-Slot Special belongs to each Slot it declares, and keeps its
    # combined marks there — the filter chooses rows, it does not rewrite them.
    registry = _registry(
        to_hit=_rule(slots=["unit", "range"], effect="."),
        snipe=_rule(slots=["range"], effect="."),
        fend=_rule(slots=["model"], effect="."),
    )

    rows = special_rows(registry, slot="range")

    assert [(row.label, row.marks) for row in rows] == [
        ("snipe", "   R"),
        ("to_hit", "U  R"),
    ]


def test_no_slot_returns_every_record_once() -> None:
    registry = _registry(
        to_hit=_rule(slots=["unit", "range"], effect="."),
        fend=_rule(slots=["model"], effect="."),
    )

    rows = special_rows(registry)

    assert sorted(row.label for row in rows) == ["fend", "to_hit"]


def test_a_stubs_text_is_the_first_line_of_its_todo() -> None:
    # A `todo` can run to a paragraph, and the row is one line.
    registry = _registry(aim=_rule(todo="Rule text not yet written.\nAsk Hans."))

    (row,) = special_rows(registry)

    assert row.text == "Rule text not yet written."
    assert row.is_stub is True


def test_a_multi_line_effect_is_collapsed_onto_one_line() -> None:
    # An effect may be a list of options; the row is one logical line, so it is
    # folded rather than cut — a piped list stays one line per Special.
    registry = _registry(heal=_rule(effect="Spend points:\n\n- Cure. Cost 1.\n"))

    (row,) = special_rows(registry)

    assert row.text == "Spend points: - Cure. Cost 1."


def test_every_registered_special_is_exactly_one_printed_line(
    capsys: pytest.CaptureFixture[str], install_registry: InstallRegistry
) -> None:
    # Including the record whose effect runs to several lines: the list is one
    # greppable line per Special, whatever the prose does.
    registry = install_registry(
        synthetic_registry(
            specials={
                "aim": synthetic_special(effect="Aim carefully."),
                "heal": synthetic_special(effect="Spend points:\n\n- Cure.\n"),
                "zeal": synthetic_special(effect="Zealous."),
            }
        )
    )

    _list()
    lines = [line for line in capsys.readouterr().out.splitlines() if line.strip()]

    assert len(lines) == len(registry.specials)


def test_every_record_gets_a_row_with_text() -> None:
    registry = _registry(
        aim=_rule(effect="Aim carefully."), fend=_rule(todo="Not written yet.")
    )

    rows = special_rows(registry)

    assert len(rows) == len(registry.specials)
    assert all(row.text for row in rows)


def test_the_printed_list_marks_a_stub_as_a_todo(
    capsys: pytest.CaptureFixture[str], install_registry: InstallRegistry
) -> None:
    install_registry(
        synthetic_registry(
            specials={"aim": synthetic_special(effect=None, todo="Not written yet.")}
        )
    )

    _list()

    assert "todo: Not written yet." in capsys.readouterr().out


def test_the_printed_list_keeps_a_signatures_brackets(
    capsys: pytest.CaptureFixture[str], install_registry: InstallRegistry
) -> None:
    # A Signature is full of square brackets, which are Rich's own markup:
    # printed raw, `[{N}]` would vanish as a tag.
    install_registry(
        synthetic_registry(
            specials={
                "reroll": synthetic_special(
                    signature="[{N}]", variables={"N": {"type": "int", "min": 1}}
                )
            }
        )
    )

    _list()

    assert "reroll[{N}]" in capsys.readouterr().out


def test_the_printed_list_narrows_to_one_slot(
    capsys: pytest.CaptureFixture[str], install_registry: InstallRegistry
) -> None:
    install_registry(
        synthetic_registry(
            specials={
                "snipe": synthetic_special(slots=["range"]),
                "hack": synthetic_special(slots=["assault"]),
            }
        )
    )

    _list("--slot", "range")
    # A row is the UMAR column, then the label: read the label back off it
    # rather than counting columns.
    rows = (_ROW.match(line) for line in capsys.readouterr().out.splitlines())
    labels = {row["label"] for row in rows if row is not None}

    assert labels == {"snipe"}, (
        "an assault-only Special has no place under --slot range"
    )


def test_a_written_rule_carrying_a_todo_still_shows_its_effect() -> None:
    # A written rule may keep an open question; the rule text is what it has.
    registry = _registry(aim=_rule(effect="Aim carefully.", todo="Duplicate of fend?"))

    (row,) = special_rows(registry)

    assert row.text == "Aim carefully."
    assert row.is_stub is False


#
# The record block `spf special show` prints above its Instances
#
def _record(key: str, registry: Registry) -> SpecialRecord:
    return special_record(key, registry.specials[key], registry=registry)


def test_a_written_records_effect_lands_in_the_record() -> None:
    registry = _registry(aim=_rule(effect="Aim carefully."))

    record = _record("aim", registry)

    assert record.effect == "Aim carefully."
    assert record.todo is None


def test_a_records_todo_survives_whole() -> None:
    # Unlike a list row, `show` has room for the whole note: the rescued design
    # prose is the only thing a Stub has to say.
    todo = "Rule text not yet written.\nThis wants an Order, and none exist."
    registry = _registry(aim=_rule(todo=todo))

    record = _record("aim", registry)

    assert record.todo == todo
    assert record.effect is None


def test_a_written_record_carrying_a_todo_keeps_both() -> None:
    # The schema deliberately admits both, and `show` is where the reader is
    # already looking at the rule the open question is about.
    registry = _registry(aim=_rule(effect="Aim carefully.", todo="Duplicate of fend?"))

    record = _record("aim", registry)

    assert record.effect == "Aim carefully."
    assert record.todo == "Duplicate of fend?"


def test_a_records_absent_fields_are_not_invented() -> None:
    registry = _registry(aim=_rule(effect="Aim carefully."))

    record = _record("aim", registry)

    assert (record.flavor, record.example) == (None, None)
    assert record.variables == []
    assert record.places == []
    assert record.see_also == []
    assert record.versions == []


def test_the_record_label_is_the_identifier_and_its_signature() -> None:
    # Uninterpolated: there are no Args at record level, and the placeholder is
    # what tells a reader the Special takes an argument at all.
    registry = _registry(
        ork_reroll=_rule(
            name="Ork Reroll",
            signature="[{N}]",
            variables={"N": {"type": "int", "min": 1}},
            effect="Reroll.",
        )
    )

    record = _record("ork_reroll", registry)

    assert record.label == "ork_reroll[{N}]"
    assert record.name == "Ork Reroll"


def test_refs_render_as_the_display_name_and_the_id() -> None:
    # The Display Name is what the reader knows the thing as; the Ref is what
    # they type into the next command and grep the TOML for.
    registry = Registry(
        records={
            "special": {
                "aim": _rule(
                    effect="Aim.",
                    places=["token.shaken"],
                    see_also=["special.fend"],
                ),
                "fend": _rule(name="Fend", effect="Fend."),
            },
            "token": {"shaken": _rule(name="Shaken", effect="Shaky.")},
        }
    )

    record = _record("aim", registry)

    assert record.places == ["Shaken (token.shaken)"]
    assert record.see_also == ["Fend (special.fend)"]


def test_a_ref_pointing_nowhere_falls_back_to_its_bare_id() -> None:
    # The load-time gate is what rejects a dangling Ref; printing one is not
    # the place to raise.
    registry = _registry(aim=_rule(effect="Aim.", see_also=["token.nowhere"]))

    record = _record("aim", registry)

    assert record.see_also == ["nowhere (token.nowhere)"]


def test_variables_are_name_and_phrase_pairs_in_declaration_order() -> None:
    registry = _registry(
        aim=_rule(
            signature="[{N}, {kind}]",
            variables={
                "N": {"type": "int", "min": 1, "max": 4},
                "kind": {"type": "str"},
            },
            effect="Aim.",
        )
    )

    record = _record("aim", registry)

    assert record.variables == [("N", "integer, 1-4"), ("kind", "text")]


def test_versions_come_back_as_rendered_ref_and_effect_pairs() -> None:
    # An overlay is a full alternative effect, not a fragment, so each keeps
    # its own text under the Ref it is keyed by.
    registry = Registry(
        records={
            "special": {
                "resistance": _rule(
                    effect="Resist.",
                    versions={"damage_type.fire": {"effect": "Fire is reduced."}},
                )
            },
            "damage_type": {"fire": _rule(name="Fire", effect="Burns.")},
        }
    )

    record = _record("resistance", registry)

    assert record.versions == [("Fire (damage_type.fire)", "Fire is reduced.")]


def test_variants_come_back_as_id_and_text_pairs() -> None:
    # A variant id is a bare name the rule owns, not a Ref, so it is printed as
    # written rather than resolved against a namespace.
    registry = _registry(
        ammo=_rule(
            effect="Carries shots.",
            variants={"always_loaded": "Always treated as loaded"},
        )
    )

    record = _record("ammo", registry)

    assert record.variants == [("always_loaded", "Always treated as loaded")]


def test_a_record_without_variants_invents_none() -> None:
    registry = _registry(aim=_rule(effect="Aim carefully."))

    assert _record("aim", registry).variants == []


def test_show_prints_the_variants_a_rule_defines(
    capsys: pytest.CaptureFixture[str],
) -> None:
    registry = _registry(
        ammo=_rule(
            effect="Carries shots.",
            variants={"always_loaded": "Always treated as loaded"},
        )
    )

    _print_record(_record("ammo", registry))
    out = capsys.readouterr().out

    assert "Variants" in out
    assert "always_loaded" in out
    assert "Always treated as loaded" in out


def test_the_records_marks_are_the_umar_column() -> None:
    registry = _registry(to_hit=_rule(slots=["unit", "range"], effect="Hits."))

    record = _record("to_hit", registry)

    assert record.marks == "U  R"


#
# `spf special show`
#
def show(key: str) -> None:
    app(["special", "show", key], exit_on_error=False, result_action="return_value")


def _assault_race(specials: Specials, *, race: RaceName = "goblin") -> RaceConfig:
    """Build a Race whose one Model carries the given Assault Instances."""
    return synthetic_race(
        race=race,
        models={
            "soldier": synthetic_model(
                race=race, assault=synthetic_assault(specials=specials)
            )
        },
    )


def _ranged(name: str, specials: Specials) -> EquipmentConfig:
    """Build an Equipment with a range profile, carrying Range Instances."""
    return synthetic_equipment(
        name=name,
        range={
            "range": 12,
            "angle": [True, False, False, False],
            "damage": "d6",
            "ap": 0,
            "specials": specials,
        },
    )


def _shelf(*equipment: EquipmentConfig) -> dict[str, EquipmentConfig]:
    """Stock a Race's shelf: the Default the Model carries, then the Upgrades."""
    default = synthetic_equipment(name="Knife", cost=None, upgrade_all=None)
    return {"knife": default} | {item.name.lower(): item for item in equipment}


def test_show_accepts_a_key_in_the_wrong_case(
    capsys: pytest.CaptureFixture[str],
    install_registry: InstallRegistry,
    install_races: InstallRaces,
) -> None:
    # The key is canonicalised, so the shouted spelling finds the same rows the
    # canonical one does rather than being rejected.
    install_registry(synthetic_registry(specials={"reroll": _assault_rule()}))
    install_races(_assault_race({"reroll": [SpecialInstance()]}))

    show("REROLL")
    canonical = capsys.readouterr().out
    show("reroll")

    assert "A  Model:     Soldier" in canonical
    assert capsys.readouterr().out == canonical


def test_show_reports_range_specials(
    capsys: pytest.CaptureFixture[str],
    install_registry: InstallRegistry,
    install_races: InstallRaces,
) -> None:
    install_registry(
        synthetic_registry(specials={"snipe": synthetic_special(slots=["range"])})
    )
    install_races(
        synthetic_race(
            equipment=_shelf(_ranged("Rifle", {"snipe": [SpecialInstance()]}))
        )
    )

    show("snipe")

    assert "R Equipment: Rifle" in capsys.readouterr().out


def test_show_reports_every_instance_a_holder_carries(
    capsys: pytest.CaptureFixture[str],
    install_registry: InstallRegistry,
    install_races: InstallRaces,
) -> None:
    # A slot holds N Instances of an id, so a holder with two Resistances is
    # two rows rather than the one a label dict could hold.
    install_registry(
        synthetic_registry(specials={"resist": synthetic_special(slots=["model"])})
    )
    install_races(
        synthetic_race(
            equipment=_shelf(
                synthetic_equipment(
                    name="Coat",
                    model_specials={
                        "resist": [
                            SpecialInstance(text="Against fire."),
                            SpecialInstance(text="Against acid."),
                        ]
                    },
                )
            )
        )
    )

    show("resist")
    rows = [
        line
        for line in capsys.readouterr().out.splitlines()
        if "Equipment: Coat" in line
    ]

    assert len(rows) == 2


def test_show_names_an_instance_that_renamed_itself(
    capsys: pytest.CaptureFixture[str],
    install_registry: InstallRegistry,
    install_races: InstallRaces,
) -> None:
    # An atmospheric name is what the reader could not have guessed from the id.
    install_registry(synthetic_registry(specials={"to_hit": _assault_rule()}))
    install_races(
        _assault_race(
            {"to_hit": [SpecialInstance(name="Excellent Shot", text="Ignores cover.")]}
        )
    )

    show("to_hit")

    assert "Excellent Shot: Ignores cover." in capsys.readouterr().out


def test_show_suggests_a_near_miss(install_registry: InstallRegistry) -> None:
    install_registry(synthetic_registry(specials={"reroll": None}))

    with pytest.raises(CycloptsError, match=r'Did you mean "reroll"\?'):
        show("rerol")


def test_show_points_at_the_listing_command_for_nonsense(
    install_registry: InstallRegistry,
) -> None:
    install_registry(synthetic_registry(specials={"reroll": None}))

    with pytest.raises(CycloptsError, match=r"spf rules specials"):
        show("zzz")


def test_show_prints_the_display_name_and_the_rule_text(
    capsys: pytest.CaptureFixture[str],
    install_registry: InstallRegistry,
    install_races: InstallRaces,
) -> None:
    # Short fragments, not whole paragraphs: this output wraps to the console
    # width, so a long phrase can straddle a break.
    install_registry(
        synthetic_registry(
            specials={
                "cunning": synthetic_special(
                    name="Cunning Assault",
                    effect="Halve the assault successes assigned to this Unit.",
                )
            }
        )
    )
    install_races(synthetic_race())

    show("cunning")
    out = unwrapped(capsys.readouterr().out)

    assert "Cunning Assault" in out
    assert "assault successes assigned" in out


def test_show_keeps_a_signatures_brackets(
    capsys: pytest.CaptureFixture[str],
    install_registry: InstallRegistry,
    install_races: InstallRaces,
) -> None:
    # A Signature is full of square brackets, which are Rich's own markup:
    # printed raw, `[{N}]` would vanish as a tag.
    install_registry(
        synthetic_registry(
            specials={
                "reroll": synthetic_special(
                    signature="[{N}]", variables={"N": {"type": "int", "min": 1}}
                )
            }
        )
    )
    install_races(synthetic_race())

    show("reroll")

    assert "reroll[{N}]" in capsys.readouterr().out


def test_show_heads_the_instances_with_their_own_word(
    capsys: pytest.CaptureFixture[str],
    install_registry: InstallRegistry,
    install_races: InstallRaces,
) -> None:
    install_registry(synthetic_registry(specials={"reroll": _assault_rule()}))
    install_races(_assault_race({"reroll": [SpecialInstance()]}))

    lines = _lines(show, "reroll", capsys=capsys)

    assert "Instances" in lines
    assert lines.index("Instances") < lines.index("Goblin (goblin)")


def test_show_skips_a_race_holding_no_instance(
    capsys: pytest.CaptureFixture[str],
    install_registry: InstallRegistry,
    install_races: InstallRaces,
) -> None:
    # A Race with nothing to contribute is silent: the heading is what says
    # "this Race holds one".
    install_registry(synthetic_registry(specials={"reroll": _assault_rule()}))
    install_races(
        _assault_race({"reroll": [SpecialInstance()]}, race="ork"),
        synthetic_race(race="goblin"),
    )

    show("reroll")
    out = capsys.readouterr().out

    assert "(ork)" in out
    assert "(goblin)" not in out


def test_show_says_so_when_no_race_uses_a_special(
    capsys: pytest.CaptureFixture[str],
    install_registry: InstallRegistry,
    install_races: InstallRaces,
) -> None:
    # Silence under a heading is indistinguishable from a bug, and
    # "defined but unused" is real information about this Registry.
    install_registry(synthetic_registry(specials={"unused": None}))
    install_races(synthetic_race())

    lines = _lines(show, "unused", capsys=capsys)

    assert lines[lines.index("Instances") + 1] == "(none)"


def test_show_states_that_it_skipped_a_race_that_does_not_validate(
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
    install_registry: InstallRegistry,
    install_races: InstallRaces,
) -> None:
    # Tolerant listing (ADR 0004) keeps going, but a skipped Race reads as a
    # Race with no Instances unless the skip is stated.
    install_registry(synthetic_registry(specials={"reroll": _assault_rule()}))
    install_races(_assault_race({"reroll": [SpecialInstance()]}))
    _break_race("goblin", monkeypatch=monkeypatch)

    show("reroll")

    assert "goblin: skipped (does not validate)" in capsys.readouterr().out


def test_show_heads_a_race_with_its_display_name_and_slug(
    capsys: pytest.CaptureFixture[str],
    install_registry: InstallRegistry,
    install_races: InstallRaces,
) -> None:
    # The name the reader knows, plus the id they can type into the next
    # command — one line, as a Ref is printed.
    install_registry(synthetic_registry(specials={"reroll": _assault_rule()}))
    install_races(_assault_race({"reroll": [SpecialInstance()]}))

    lines = _lines(show, "reroll", capsys=capsys)

    assert "Goblin (goblin)" in lines
    assert "goblin" not in lines


def test_show_survives_a_display_name_that_looks_like_markup(
    capsys: pytest.CaptureFixture[str],
    install_registry: InstallRegistry,
    install_races: InstallRaces,
) -> None:
    # A Display Name is author prose, and Rich reads a closing tag in it as an
    # error rather than as text.
    install_registry(
        synthetic_registry(specials={"aim": synthetic_special(name="Aim [/] Fire")})
    )
    install_races(synthetic_race())

    show("aim")

    assert "Aim [/] Fire" in capsys.readouterr().out


def test_show_qualifies_none_when_a_race_was_skipped(
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
    install_registry: InstallRegistry,
    install_races: InstallRaces,
) -> None:
    # "Unused" is only a claim about the Races that loaded; a skipped one may
    # hold the very Instances this line says there are none of.
    install_registry(synthetic_registry(specials={"unused": None}))
    install_races(synthetic_race())
    _break_race("goblin", monkeypatch=monkeypatch)

    lines = _lines(show, "unused", capsys=capsys)

    assert lines[-1] == "(none in the Races that validate)"
