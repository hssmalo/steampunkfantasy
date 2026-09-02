"""Tests for the longhand-variant rule.

`check_longhand` is a predicate over two strings, so it is exercised without a
Race, a registry or a file. `check_specials` adds only the walk over the prose
slots an instance has.
"""

from spf.lint import variants
from spf.registry import Registry
from spf.schemas.special import SpecialInstance, Specials

POOL = {
    "ammo": {
        "always_loaded": "Always treated as loaded",
        "load_n_shots": "May load up to {N} shots",
    },
    "area": {"point_blank": "at point blank", "long_range": "at long range"},
}
"""Each rule's variants, the way the registry holds them."""

REGISTRY = Registry(records={})
"""Only ref-valued args reach the registry, and none of these instances has one."""


def _instances(**specials: list[dict[str, object]]) -> Specials:
    return {
        key: [SpecialInstance.model_validate(one) for one in instances]
        for key, instances in specials.items()
    }


# --- the predicate ----------------------------------------------------------


def test_prose_a_variant_already_spells_is_named() -> None:
    message = variants.check_longhand("Always treated as loaded", POOL["ammo"])

    assert message is not None
    assert "always_loaded" in message


def test_prose_no_variant_spells_is_clean() -> None:
    assert variants.check_longhand("Always loaded", POOL["ammo"]) is None


def test_an_absent_prose_slot_is_clean() -> None:
    assert variants.check_longhand(None, POOL["ammo"]) is None


def test_the_match_is_exact() -> None:
    # Near-duplicates are a rules judgment, not a mechanical one: deciding
    # that two spellings mean the same thing needs the maintainer's eyes.
    assert variants.check_longhand("always treated as loaded", POOL["ammo"]) is None
    assert variants.check_longhand("Always treated as loaded.", POOL["ammo"]) is None


# --- the walk over an instance's prose slots --------------------------------


def test_an_instances_longhand_text_is_reported() -> None:
    specials = _instances(ammo=[{"text": "Always treated as loaded"}])

    assert list(variants.check_specials(specials, POOL, registry=REGISTRY)) == [
        ("ammo", variants.check_longhand("Always treated as loaded", POOL["ammo"]))
    ]


def test_an_instance_already_naming_the_variant_is_clean() -> None:
    specials = _instances(ammo=[{"variant": "always_loaded"}])

    assert list(variants.check_specials(specials, POOL, registry=REGISTRY)) == []


def test_a_longhand_preamble_is_reported() -> None:
    specials = _instances(
        area=[{"preamble": "at long range", "cases": [{"args": {"N": 4}}]}]
    )

    (identifier, message) = next(
        iter(variants.check_specials(specials, POOL, registry=REGISTRY))
    )

    assert (identifier, "long_range" in message) == ("area", True)


def test_a_longhand_case_text_is_reported() -> None:
    specials = _instances(area=[{"cases": [{"text": "at point blank"}]}])

    (identifier, message) = next(
        iter(variants.check_specials(specials, POOL, registry=REGISTRY))
    )

    assert (identifier, "point_blank" in message) == ("area", True)


def test_a_rule_with_no_variants_reports_nothing() -> None:
    specials = _instances(sniper=[{"text": "Always treated as loaded"}])

    assert list(variants.check_specials(specials, POOL, registry=REGISTRY)) == []


def test_every_longhand_slot_of_one_instance_is_reported() -> None:
    specials = _instances(
        area=[
            {
                "preamble": "at long range",
                "cases": [{"text": "at point blank"}, {"text": "at long range"}],
            }
        ]
    )

    assert len(list(variants.check_specials(specials, POOL, registry=REGISTRY))) == 3


# --- the pool is filled before it is compared (ADR 0037) --------------------


def test_longhand_prose_matching_a_filled_variant_is_reported() -> None:
    # The author who typed the number out is precisely the one who did not
    # know the variant existed, so the comparison has to fill it first.
    specials = _instances(ammo=[{"text": "May load up to 5 shots", "args": {"N": 5}}])

    (identifier, message) = next(
        iter(variants.check_specials(specials, POOL, registry=REGISTRY))
    )

    assert (identifier, "load_n_shots" in message) == ("ammo", True)


def test_longhand_prose_with_a_different_number_is_clean() -> None:
    specials = _instances(ammo=[{"text": "May load up to 5 shots", "args": {"N": 2}}])

    assert list(variants.check_specials(specials, POOL, registry=REGISTRY)) == []


def test_a_cases_prose_is_compared_against_its_own_args() -> None:
    specials = _instances(
        ammo=[
            {
                "args": {"N": 2},
                "cases": [{"text": "May load up to 5 shots", "args": {"N": 5}}],
            }
        ]
    )

    (identifier, message) = next(
        iter(variants.check_specials(specials, POOL, registry=REGISTRY))
    )

    assert (identifier, "load_n_shots" in message) == ("ammo", True)
