"""Tests for the placeholder grammar's linked form: spans carrying their Refs."""

from spf.prose import (
    LinkedText,
    Span,
    fill,
    fill_linked,
    interpolate_linked,
    link_refs,
    linked_prose,
    malformed_links,
    plain,
)
from spf.schemas import rules as r
from spf.schemas.race import spawn_reference
from spf.schemas.special import SpecialInstance
from tests.conftest import synthetic_registry, synthetic_special

REGISTRY = synthetic_registry(
    specials={
        "to_hit": synthetic_special(
            name="To Hit",
            signature="{version}[{N}]",
            variables={
                "version": {"type": "ref", "namespaces": ["ability"]},
                "N": {"type": "int"},
            },
        ),
        "optional": synthetic_special(
            name="Optional",
            signature="Base[{N}]",
            variables={"N": {"type": "int"}},
        ),
    },
    records={
        "ability": {
            "take_cover": r.ModifierRuleConfig.model_validate(
                {
                    "name": "Take Cover",
                    "to_hit": "-1",
                    "signature": "[{speed}]",
                    "variables": {"speed": {"type": "ref", "namespaces": ["speed"]}},
                }
            ),
            "loop": r.ModifierRuleConfig.model_validate(
                {
                    "name": "Loop",
                    "to_hit": "-1",
                    "signature": "<{version}>",
                    "variables": {
                        "version": {"type": "ref", "namespaces": ["ability"]}
                    },
                }
            ),
        },
    },
)


def test_a_ref_arg_links_the_targets_name() -> None:
    text = fill_linked("Resist {version}", {"version": "damage_type.poison"}, REGISTRY)

    assert text.spans == (
        Span("Resist "),
        Span("Poison", ref="damage_type.poison"),
    )


def test_a_ref_nested_in_a_targets_signature_links_too() -> None:
    args = {"version": "ability.take_cover", "speed": "speed.slow", "N": -2}

    text = interpolate_linked(REGISTRY.specials["to_hit"], args, REGISTRY)

    assert text.spans == (
        Span("Take Cover", ref="ability.take_cover"),
        Span("["),
        Span("Slow", ref="speed.slow"),
        Span("][-2]"),
    )


def test_a_raw_id_placeholder_stays_plain() -> None:
    text = fill_linked("{version.id}", {"version": "damage_type.poison"}, REGISTRY)

    assert text.spans == (Span("poison"),)


def test_a_cycle_still_prints_a_linked_name() -> None:
    text = fill_linked("{version}", {"version": "ability.loop"}, REGISTRY)

    assert text.spans == (
        Span("Loop", ref="ability.loop"),
        Span("<"),
        Span("Loop", ref="ability.loop"),
        Span(">"),
    )


def test_an_elided_group_leaves_no_span() -> None:
    text = interpolate_linked(REGISTRY.specials["optional"], {}, REGISTRY)

    assert text.spans == (Span("Base"),)


def test_a_value_that_is_no_ref_stays_text() -> None:
    text = fill_linked("{version}", {"version": "not.a_record"}, REGISTRY)

    assert text.spans == (Span("not.a_record"),)


def test_an_arg_never_given_keeps_its_placeholder() -> None:
    assert fill_linked("[{N}]", {}, REGISTRY).spans == (Span("[{N}]"),)


def test_the_plain_form_reads_the_labels_alone() -> None:
    args = {"version": "ability.take_cover", "speed": "speed.slow", "N": -2}
    rule = REGISTRY.specials["to_hit"]

    assert str(interpolate_linked(rule, args, REGISTRY)) == "Take Cover[Slow][-2]"
    assert fill("{version}", args, REGISTRY) == "Take Cover[Slow]"


def test_empty_text_is_falsy_and_written_text_is_not() -> None:
    assert not LinkedText()
    assert LinkedText((Span("x"),))


def test_joining_merges_adjacent_plain_spans_and_keeps_links() -> None:
    joined = LinkedText.join(
        "; ",
        [
            LinkedText((Span("Poison", ref="damage_type.poison"),)),
            LinkedText((Span("Fire"),)),
        ],
    )

    assert joined.spans == (
        Span("Poison", ref="damage_type.poison"),
        Span("; Fire"),
    )


def test_resolving_anchors_only_the_refs_with_an_entry() -> None:
    text = LinkedText(
        (Span("Poison", ref="damage_type.poison"), Span(" and "), Span("X", ref="a.x"))
    )

    resolved = text.resolved({"damage_type.poison": "rule-poison"}.get)

    assert resolved.spans == (
        Span("Poison", ref="damage_type.poison", anchor="rule-poison"),
        Span(" and "),
        Span("X", ref="a.x"),
    )


def test_an_authored_link_prints_its_label_as_a_rule_link() -> None:
    text = linked_prose("Gain a {poison token:damage_type.poison} now.")

    assert text.spans == (
        Span("Gain a "),
        Span("poison token", ref="damage_type.poison"),
        Span(" now."),
    )


def test_prose_with_no_args_keeps_its_placeholders_verbatim() -> None:
    text = linked_prose("Roll {N} and take {Poison[{N}]:damage_type.poison}.")

    assert text.spans == (
        Span("Roll {N} and take "),
        Span("Poison[{N}]", ref="damage_type.poison"),
        Span("."),
    )


def test_a_colon_in_a_label_stays_in_the_label() -> None:
    assert linked_prose("{Note: poison:damage_type.poison}").spans == (
        Span("Note: poison", ref="damage_type.poison"),
    )


def test_absent_prose_has_nothing_to_print() -> None:
    assert not linked_prose(None)


def test_linked_prose_anchors_when_given_a_lookup() -> None:
    text = linked_prose("{Poison:damage_type.poison}", {"damage_type.poison": "a"}.get)

    assert text.spans == (Span("Poison", ref="damage_type.poison", anchor="a"),)


def test_a_filled_label_keeps_its_authored_ref() -> None:
    text = fill_linked("{Bleed[{N}]:damage_type.poison}", {"N": 4}, REGISTRY)

    assert text.spans == (Span("Bleed[4]", ref="damage_type.poison"),)


def test_a_ref_placeholder_in_a_label_adds_text_but_no_nested_link() -> None:
    args: dict[str, int | str] = {"kind": "speed.slow"}

    text = fill_linked("{Very {kind}:damage_type.poison}", args, REGISTRY)

    assert text.spans == (Span("Very Slow", ref="damage_type.poison"),)


def test_fill_keeps_only_the_label() -> None:
    assert fill("Take {Poison:damage_type.poison}.", {}, REGISTRY) == "Take Poison."


def test_plain_reduces_a_link_to_its_label() -> None:
    assert plain("{Poison[{N}]:token.poison} and {N}") == "Poison[{N}] and {N}"
    assert plain(None) is None


def test_link_refs_lists_each_ref_written() -> None:
    assert link_refs("{a:token.one} then {b {N}:hex.two}") == ["token.one", "hex.two"]


def test_malformed_links_finds_what_the_grammar_rejects() -> None:
    malformed = malformed_links("{ok:token.one} {bad:Token} {:token.two} {x {y:z} w}")

    assert malformed == ["{bad:Token}", "{:token.two}", "{y:z}"]


def test_a_placeholder_is_not_a_malformed_link() -> None:
    assert malformed_links("Roll {N} or {version.id}, then {ok[{N}]:token.a}") == []


def test_a_rule_link_after_a_spawn_id_leaves_the_id_alone() -> None:
    instance = SpecialInstance(text="tiny_snake: place {it:token.bleed} nearby.")

    assert spawn_reference(instance) == "tiny_snake"
