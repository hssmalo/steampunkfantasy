"""Tests for presenting Special instances: signatures, headings, grouping."""

from spf.registry import Registry, load_registry
from spf.render.specials import SpecialLine, special_lines, special_row
from spf.schemas.rules import SpecialRuleConfig
from spf.schemas.special import SpecialInstance

REGISTRY = load_registry()


def _row(identifier: str, **kwargs: object) -> tuple[str, str]:
    instance = SpecialInstance.model_validate(kwargs)
    return special_row(identifier, instance, registry=REGISTRY)


# --- one instance: heading and text -----------------------------------------


def test_the_heading_is_the_rules_name() -> None:
    heading, _ = _row("evasion", args={"N": 4})

    assert heading == "Evasion"


def test_an_atmospheric_name_overrides_the_rules_name() -> None:
    heading, text = _row(
        "to_hit", name="Enhanced Arrow", args={"ability": "ability.excellent_shot"}
    )

    assert heading == "Enhanced Arrow"
    # The vocabulary stays in one place: the ref still resolves to its own name.
    assert text == "Excellent Shot"


def test_the_signature_interpolates_the_instances_arguments() -> None:
    _, text = _row("evasion", args={"N": 4})

    assert text == "[4+]"


def test_a_ref_valued_variable_renders_the_targets_name() -> None:
    _, text = _row("resistance", args={"version": "damage_type.poison", "N": 12})

    assert text == "Poison[12]"


def test_a_refs_own_signature_travels_with_it() -> None:
    # `take_cover` lends `to_hit` both its name and its arguments, so the
    # numbers the instance carries for it are printed where it declares them.
    _, text = _row(
        "to_hit",
        args={"ability": "ability.take_cover", "speed": "speed.sneak", "N": -2},
    )

    assert text == "Take Cover[Sneak][-2]"


def test_a_versioned_rule_prints_the_versions_own_arguments() -> None:
    # Extra Damage is one rule per slot versioned over the kinds it applies, so
    # the poison strength prints inside the token's own signature.
    _, text = _row(
        "assault_extra_damage",
        args={"version": "token.poison", "N": 6, "M": 2},
    )

    assert text == "Poison[6][1 for 2]"


def test_an_absent_optional_argument_elides_its_group() -> None:
    # One fire token however many hits landed: the ratio group is not written,
    # so it is not printed either.
    _, text = _row("assault_extra_damage", args={"version": "token.fire"})

    assert text == "Fire"


def test_free_prose_follows_the_signature() -> None:
    _, text = _row(
        "resistance",
        args={"version": "damage_type.psychic", "N": 1},
        text="While at least one elite is alive",
    )

    assert text == "Psychic[1]. While at least one elite is alive"


def test_a_rule_with_neither_signature_nor_prose_has_no_text() -> None:
    _, text = _row("sniper")

    assert text == ""


# --- a case-shaped instance -------------------------------------------------


def test_a_preamble_precedes_the_cases_it_scopes() -> None:
    _, text = _row(
        "area",
        preamble=(
            "If not using aim, fire once at all enemy models within range"
            " and within front arc"
        ),
        cases=[
            {"args": {"N": 5}, "text": "at point blank range"},
            {"args": {"N": 6}, "text": "at normal and long range"},
        ],
    )

    assert text == (
        "If not using aim, fire once at all enemy models within range and"
        " within front arc: [5+] at point blank range, [6+] at normal and"
        " long range"
    )


def test_cases_without_a_preamble_stand_on_their_own() -> None:
    _, text = _row(
        "area",
        cases=[
            {"args": {"N": 4}, "text": "at point blank"},
            {"args": {"N": 5}, "text": "at range=2"},
        ],
    )

    assert text == "[4+] at point blank, [5+] at range=2"


def test_a_case_may_carry_values_without_prose() -> None:
    _, text = _row(
        "area",
        preamble="Choose one hex (per model firing this weapon) within normal range",
        cases=[{"args": {"N": 5}}],
    )

    assert text == (
        "Choose one hex (per model firing this weapon) within normal range: [5+]"
    )


def test_a_case_may_carry_prose_without_values() -> None:
    # An absent optional argument elides its group, leaving the prose alone.
    _, text = _row("area", cases=[{"text": "at any range"}])

    assert text == "at any range"


def test_a_case_inherits_the_instances_arguments() -> None:
    # The ref is constant across the cases, so it is written once.
    _, text = _row(
        "resistance",
        args={"version": "damage_type.poison"},
        cases=[{"args": {"N": 12}, "text": "on foot"}, {"args": {"N": 6}}],
    )

    assert text == "Poison[12] on foot, Poison[6]"


def test_two_case_shaped_instances_read_as_two_condition_groups() -> None:
    specials = {
        "area": [
            SpecialInstance.model_validate(
                {
                    "preamble": "If fired from a unit with 1-2 alive models",
                    "cases": [
                        {"args": {"N": 4}, "text": "at point blank"},
                        {"args": {"N": 5}, "text": "at range=2"},
                        {"args": {"N": 6}, "text": "at range=3 or 4"},
                    ],
                }
            ),
            SpecialInstance.model_validate(
                {
                    "preamble": "If fired from a unit with 3-4 alive models",
                    "cases": [
                        {"args": {"N": 2}, "text": "at point blank"},
                        {"args": {"N": 4}, "text": "at range=2"},
                        {"args": {"N": 5}, "text": "at range=3 or 4"},
                    ],
                }
            ),
        ]
    }

    assert special_lines(specials, registry=REGISTRY) == [
        SpecialLine(
            "Area",
            "If fired from a unit with 1-2 alive models: [4+] at point blank,"
            " [5+] at range=2, [6+] at range=3 or 4;"
            " If fired from a unit with 3-4 alive models: [2+] at point blank,"
            " [4+] at range=2, [5+] at range=3 or 4",
            None,
        )
    ]


def test_a_prose_shaped_instance_is_unchanged_by_the_case_shape() -> None:
    # The instances left prose-shaped render exactly as they always have: the
    # signature alone, with no separator and no empty case list showing.
    _, text = _row("area", args={"N": 5})

    assert text == "[5+]"


def test_two_cases_that_read_alike_are_both_printed() -> None:
    # Instance dedup exists because the source chain delivers repeats nobody
    # wrote; cases are hand-written in one array, so a repeat is visible.
    _, text = _row("area", cases=[{"args": {"N": 5}}, {"args": {"N": 5}}])

    assert text == "[5+], [5+]"


# --- grouping ---------------------------------------------------------------


def test_instances_of_one_id_group_under_one_heading() -> None:
    specials = {
        "resistance": [
            SpecialInstance(args={"version": "damage_type.poison", "N": 12}),
            SpecialInstance(args={"version": "damage_type.fire", "N": 3}),
        ]
    }

    assert special_lines(specials, registry=REGISTRY) == [
        SpecialLine("Resistance", "Poison[12]; Fire[3]", None)
    ]


def test_instances_that_read_alike_are_printed_once() -> None:
    # Three Models of a Unit each granting the same Resistance say one thing.
    instance = SpecialInstance(args={"version": "damage_type.psychic", "N": 1})
    specials = {"resistance": [instance, instance, instance]}

    assert special_lines(specials, registry=REGISTRY) == [
        SpecialLine("Resistance", "Psychic[1]", None)
    ]


def test_atmospheric_names_keep_their_own_headings() -> None:
    # Two instances of one id, named apart on purpose: collapsing them would
    # print one flavor name over the other's rule.
    specials = {
        "to_hit": [
            SpecialInstance(name="Keen Eye", args={"ability": "ability.good_shot"}),
            SpecialInstance(args={"ability": "ability.bad_shot"}),
        ]
    }

    assert special_lines(specials, registry=REGISTRY) == [
        SpecialLine("Keen Eye", "Good Shot", None),
        SpecialLine("To Hit", "Bad Shot", None),
    ]


def test_grouping_keeps_the_order_the_ids_were_contributed_in() -> None:
    specials = {
        "evasion": [SpecialInstance(args={"N": 4})],
        "sniper": [SpecialInstance(text="Choose the model")],
    }

    assert [line.name for line in special_lines(specials, registry=REGISTRY)] == [
        "Evasion",
        "Sniper",
    ]


# --- anchors ----------------------------------------------------------------


def test_a_line_carries_no_anchor_without_a_lookup() -> None:
    specials = {"evasion": [SpecialInstance(args={"N": 4})]}

    assert special_lines(specials, registry=REGISTRY)[0].anchor is None


def test_a_lookup_is_asked_about_the_identifier_not_the_heading() -> None:
    # An atmospheric name is what the reader sees; the Identifier is what
    # addresses the rule, so only it can find the rule's entry.
    specials = {"evasion": [SpecialInstance(name="Nimble", args={"N": 4})]}

    (line,) = special_lines(
        specials, registry=REGISTRY, anchor_for={"evasion": "rule-special-evasion"}.get
    )

    assert (line.name, line.anchor) == ("Nimble", "rule-special-evasion")


def test_an_identifier_the_lookup_does_not_know_leaves_the_anchor_unset() -> None:
    specials = {"evasion": [SpecialInstance(args={"N": 4})]}

    (line,) = special_lines(
        specials, registry=REGISTRY, anchor_for=lambda _identifier: None
    )

    assert line.anchor is None


# --- variants: shared prose drawn from the rule's pool (ADR 0031) -----------

VARIANTS = Registry(
    records={
        "special": {
            "ammo": SpecialRuleConfig.model_validate(
                {
                    "name": "Ammo",
                    "slots": ["range"],
                    "signature": "[{N}]",
                    "effect": "Carries {N} shots.",
                    "variables": {"N": {"type": "int"}},
                    "variants": {
                        "always_loaded": {"text": "Always treated as loaded"},
                        "point_blank": {"text": "at point blank"},
                    },
                }
            )
        }
    }
)
"""A registry of one rule with a variant pool, so the corpus stays free."""


def _variant_row(identifier: str, **kwargs: object) -> tuple[str, str]:
    instance = SpecialInstance.model_validate(kwargs)
    return special_row(identifier, instance, registry=VARIANTS)


def test_a_variant_renders_as_the_instances_own_prose() -> None:
    _, text = _variant_row("ammo", variant="always_loaded", args={"N": 2})

    assert text == "[2]. Always treated as loaded"


def test_a_variant_reads_identically_to_the_prose_written_inline() -> None:
    named = _variant_row("ammo", variant="always_loaded", args={"N": 2})
    longhand = _variant_row("ammo", text="Always treated as loaded", args={"N": 2})

    assert named == longhand


def test_a_variant_on_a_case_shaped_instance_renders_as_the_preamble() -> None:
    _, text = _variant_row("ammo", variant="always_loaded", cases=[{"args": {"N": 2}}])

    assert text == "Always treated as loaded: [2]"


def test_a_variant_on_a_case_renders_as_that_cases_text() -> None:
    _, text = _variant_row(
        "ammo",
        cases=[
            {"variant": "point_blank", "args": {"N": 4}},
            {"text": "at long range", "args": {"N": 1}},
        ],
    )

    assert text == "[4] at point blank, [1] at long range"


def test_a_named_and_a_longhand_instance_collapse_to_one_line() -> None:
    # Resolution happens before the grouping key, so the two spell one line.
    specials = {
        "ammo": [
            SpecialInstance(variant="always_loaded", args={"N": 2}),
            SpecialInstance(text="Always treated as loaded", args={"N": 2}),
        ]
    }

    (line,) = special_lines(specials, registry=VARIANTS)

    assert line.text == "[2]. Always treated as loaded"


def test_an_unresolvable_variant_renders_as_no_prose() -> None:
    # The load-time gate is what reports it; rendering stays total.
    _, text = _variant_row("ammo", variant="never_defined", args={"N": 2})

    assert text == "[2]"
