"""Tests for the placeholder grammar's linked form: spans carrying their Refs."""

from spf.prose import (
    LinkedText,
    Span,
    fill,
    fill_linked,
    interpolate_linked,
)
from spf.schemas import rules as r
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
