"""Tests for presenting Special instances: signatures, headings, grouping."""

from spf.registry import load_registry
from spf.render.specials import special_lines, special_row
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


# --- grouping ---------------------------------------------------------------


def test_instances_of_one_id_group_under_one_heading() -> None:
    specials = {
        "resistance": [
            SpecialInstance(args={"version": "damage_type.poison", "N": 12}),
            SpecialInstance(args={"version": "damage_type.fire", "N": 3}),
        ]
    }

    assert special_lines(specials, registry=REGISTRY) == [
        ("Resistance", "Poison[12]; Fire[3]")
    ]


def test_instances_that_read_alike_are_printed_once() -> None:
    # Three Models of a Unit each granting the same Resistance say one thing.
    instance = SpecialInstance(args={"version": "damage_type.psychic", "N": 1})
    specials = {"resistance": [instance, instance, instance]}

    assert special_lines(specials, registry=REGISTRY) == [("Resistance", "Psychic[1]")]


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
        ("Keen Eye", "Good Shot"),
        ("To Hit", "Bad Shot"),
    ]


def test_grouping_keeps_the_order_the_ids_were_contributed_in() -> None:
    specials = {
        "evasion": [SpecialInstance(args={"N": 4})],
        "sniper": [SpecialInstance(text="Choose the model")],
    }

    assert [heading for heading, _ in special_lines(specials, registry=REGISTRY)] == [
        "Evasion",
        "Sniper",
    ]
