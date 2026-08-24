"""Tests for the shared rule-record core (ADR 0024)."""

import pytest
from pydantic import ValidationError

from spf.schemas import rules as r


def test_a_record_is_complete_when_it_carries_its_meaning() -> None:
    special = r.SpecialRuleConfig.model_validate(
        {"name": "Fumble", "slots": ["range"], "effect": "A natural 1 is a fumble."}
    )

    assert special.effect == "A natural 1 is a fumble."
    assert special.todo is None


def test_a_record_is_a_stub_when_it_carries_only_a_todo() -> None:
    special = r.SpecialRuleConfig.model_validate(
        {"name": "Stacking Limit", "slots": ["unit"], "todo": "Rule text unwritten."}
    )

    assert special.effect is None
    assert special.todo == "Rule text unwritten."


def test_a_record_may_be_neither_complete_nor_a_stub() -> None:
    with pytest.raises(ValidationError, match="has neither"):
        r.SpecialRuleConfig.model_validate({"name": "Fumble", "slots": ["range"]})


def test_a_written_rule_may_carry_an_open_question() -> None:
    # A design question about a *finished* rule is the easiest kind to forget,
    # because the record looks done. `todo` is what makes it countable.
    record = r.SpecialRuleConfig.model_validate(
        {
            "name": "Fumble",
            "slots": ["range"],
            "effect": "A natural 1 is a fumble.",
            "todo": "Is this the same rule as Misfire?",
        }
    )

    assert record.written


def test_completeness_is_keyed_on_the_meaning_fields_of_the_registry() -> None:
    # A modifier record means its numbers, not its prose: keyed on `effect`
    # the rule would manufacture stubs for rows nobody considers unfinished.
    modifier = r.ModifierRuleConfig.model_validate(
        {"name": "Long Range", "to_hit": "-2", "to_be_hit": "0"}
    )

    assert modifier.effect is None
    assert modifier.todo is None


def test_a_modifier_without_numbers_is_a_stub() -> None:
    with pytest.raises(ValidationError, match="has neither"):
        r.ModifierRuleConfig.model_validate({"name": "Medium"})


def test_a_terrain_record_means_its_prose_not_its_numbers() -> None:
    # Terrain carries to-hit numbers but its rules are unwritten; keyed on the
    # numbers, every terrain record would count as finished.
    with pytest.raises(ValidationError, match="has neither"):
        r.TerrainRuleConfig.model_validate(
            {"name": "Forest", "to_hit": "0", "to_be_hit": "-1"}
        )


def test_a_record_carries_typed_cross_references() -> None:
    special = r.SpecialRuleConfig.model_validate(
        {
            "name": "Assault Poison",
            "slots": ["assault"],
            "effect": "Targets get a poison token.",
            "places": ["token.poison"],
            "see_also": ["special.range_poison"],
        }
    )

    assert special.places == ["token.poison"]
    assert special.see_also == ["special.range_poison"]


@pytest.mark.parametrize("ref", ["Token.poison", "poison", "token.poison.strong", ""])
def test_a_reference_is_lowercase_and_two_segments(ref: str) -> None:
    with pytest.raises(ValidationError):
        r.SpecialRuleConfig.model_validate(
            {
                "name": "Assault Poison",
                "slots": ["assault"],
                "effect": "Targets get a poison token.",
                "places": [ref],
            }
        )


def test_a_variable_may_draw_from_several_namespaces() -> None:
    special = r.SpecialRuleConfig.model_validate(
        {
            "name": "Immunity",
            "slots": ["unit"],
            "todo": "Rule text unwritten.",
            "variables": {
                "feature": {"type": "ref", "namespaces": ["token", "hex", "special"]}
            },
        }
    )

    feature = special.variables["feature"]
    assert isinstance(feature, r.RefVariableConfig)
    assert feature.namespaces == ["token", "hex", "special"]


def test_a_variable_may_be_a_die() -> None:
    special = r.SpecialRuleConfig.model_validate(
        {
            "name": "Fear",
            "slots": ["unit"],
            "effect": "Roll a d{N}.",
            "variables": {"N": {"type": "die"}},
        }
    )

    assert isinstance(special.variables["N"], r.DieVariableConfig)


def test_a_variable_may_be_a_union_of_scalar_types() -> None:
    # `Regular[6]` and `Regular[d6]` are both authored against one variable.
    special = r.SpecialRuleConfig.model_validate(
        {
            "name": "Resistance",
            "slots": ["unit"],
            "effect": "Improved resilience.",
            "variables": {"N": {"type": ["int", "die"], "min": 1, "max": 12}},
        }
    )

    variable = special.variables["N"]
    assert isinstance(variable, r.UnionVariableConfig)
    assert variable.type == ["int", "die"]


def test_a_die_value_is_a_die() -> None:
    variable = r.DieVariableConfig(type="die")

    assert variable.validate_value("d6") == "d6"
    with pytest.raises(ValueError, match="not a die"):
        variable.validate_value("6")


def test_a_token_record_declares_its_phases_and_a_hex_record_does_not() -> None:
    token = r.TokenRuleConfig.model_validate(
        {"name": "Aim", "effect": "Get +2 to hit.", "phases": ["Gunnery 1"]}
    )

    assert token.phases == ["Gunnery 1"]
    with pytest.raises(ValidationError):
        r.HexRuleConfig.model_validate(
            {"name": "Fog", "effect": "Blocks sight.", "phases": ["Gunnery 1"]}
        )


def test_a_namespace_names_where_its_registry_lives() -> None:
    namespaces = r.NamespacesConfig.model_validate(
        {
            "namespaces": {
                "hex": {
                    "name": "Hexes",
                    "file": "hexes.toml",
                    "table": "hexes",
                    "group": "terrain",
                }
            },
            "damage_type": {"acid": {"name": "Acid", "todo": "Unwritten."}},
        }
    )

    hexes = namespaces.namespaces["hex"]
    assert (hexes.file, hexes.table, hexes.group) == ("hexes.toml", "hexes", "terrain")
    assert namespaces.damage_type["acid"].name == "Acid"


def test_a_union_value_may_be_either_member_type() -> None:
    variable = r.UnionVariableConfig(type=["int", "die"], min=1, max=12)

    assert variable.validate_value(6) == 6
    assert variable.validate_value("d6") == "d6"


def test_a_union_bounds_only_its_numeric_member() -> None:
    variable = r.UnionVariableConfig(type=["int", "die"], min=1, max=12)

    with pytest.raises(ValueError, match="greater than maximum"):
        variable.validate_value(20)
    # A die is not a number, so `d20` is out of no range -- the union says
    # which shapes are legal, the bounds say which numbers are.
    assert variable.validate_value("d20") == "d20"


def test_a_union_rejects_a_value_of_neither_type() -> None:
    variable = r.UnionVariableConfig(type=["int", "die"])

    with pytest.raises(ValueError, match="not an int or a die"):
        variable.validate_value("six")
