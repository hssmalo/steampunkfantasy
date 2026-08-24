"""Tests for the rule registries and the hard gate over Special instances.

The gate resolves Race data against `rules/`, so most of these tests build a
small registry of their own: the checks are about the resolver, not about the
shipped vocabulary, and a rule renamed in `rules/special.toml` should not
rewrite this file. The tests that do read the committed registries say so.
"""

from collections.abc import Mapping
from pathlib import Path

import pytest
from pydantic import ValidationError

from spf import registry as reg
from spf.config import config
from spf.schemas import rules as r
from spf.schemas.special import SpecialInstance


def _registry() -> reg.Registry:
    """Build a registry with a rule of every shape the gate has to handle."""
    return reg.Registry(
        records={
            "special": {
                "resistance": r.SpecialRuleConfig.model_validate(
                    {
                        "name": "Resistance",
                        "slots": ["unit"],
                        "effect": "Improved resilience versus {version}.",
                        "variables": {
                            "version": {
                                "type": "ref",
                                "namespaces": ["damage_type"],
                            },
                            "N": {"type": ["int", "die"], "min": 1, "max": 12},
                        },
                    }
                ),
                "assault_poison": r.SpecialRuleConfig.model_validate(
                    {
                        "name": "Assault Poison",
                        "slots": ["assault"],
                        "effect": "One poison token per {N} hits.",
                        "variables": {
                            "N": {"type": "int", "values": [4, 6, 8, 10, 12]}
                        },
                    }
                ),
                "to_hit": r.SpecialRuleConfig.model_validate(
                    {
                        "name": "To Hit",
                        "slots": ["unit", "model"],
                        "effect": "The unit has {ability}.",
                        "variables": {
                            "ability": {"type": "ref", "namespaces": ["ability"]}
                        },
                    }
                ),
                "fear": r.SpecialRuleConfig.model_validate(
                    {"name": "Fear", "slots": ["assault"], "effect": "Causes fear."}
                ),
                "shadowed": r.SpecialRuleConfig.model_validate(
                    {
                        "name": "Shadowed",
                        "slots": ["unit"],
                        "effect": "Hides in {terrain}.",
                        "variables": {
                            "ability": {"type": "ref", "namespaces": ["ability"]},
                            "terrain": {"type": "str"},
                        },
                    }
                ),
            },
            "ability": {
                "good_shot": r.ModifierRuleConfig.model_validate(
                    {"name": "Good Shot", "to_hit": "+1"}
                ),
                "camouflage": r.ModifierRuleConfig.model_validate(
                    {
                        "name": "Camouflage",
                        "to_be_hit": "-1",
                        "variables": {
                            "terrain": {"type": "ref", "namespaces": ["terrain"]}
                        },
                    }
                ),
            },
            "terrain": {
                "forest": r.TerrainRuleConfig.model_validate(
                    {"name": "Forest", "effect": "Blocks sight."}
                ),
            },
            "damage_type": {
                "poison": r.DamageTypeRuleConfig.model_validate(
                    {"name": "Poison", "effect": "Poison damage."}
                ),
            },
        }
    )


def check(
    specials: Mapping[str, list[Mapping[str, object]]], slot: str = "unit"
) -> list[str]:
    """Run the gate over instances written the way a Race file writes them."""
    return reg.check_instances(
        {
            key: [SpecialInstance.model_validate(one) for one in instances]
            for key, instances in specials.items()
        },
        slot=slot,  # pyright: ignore[reportArgumentType]
        context="unit 'Squad'",
        registry=_registry(),
    )


# ---------------------------------------------------------------------------
# 1. Every id resolves to a rule record
# ---------------------------------------------------------------------------


def test_a_known_id_resolves() -> None:
    assert check({"fear": [{}]}, slot="assault") == []


def test_an_unknown_id_is_rejected() -> None:
    (error,) = check({"terrifying": [{}]})

    assert "terrifying" in error
    assert "unit 'Squad'" in error


# ---------------------------------------------------------------------------
# 2. Every id is used in a slot the rule declares
# ---------------------------------------------------------------------------


def test_an_id_used_outside_its_slots_is_rejected() -> None:
    (error,) = check({"fear": [{}]}, slot="unit")

    assert "fear" in error
    assert "assault" in error


def test_a_rule_may_declare_several_slots() -> None:
    instance = {"args": {"ability": "ability.good_shot"}}

    assert check({"to_hit": [instance]}, slot="unit") == []
    assert check({"to_hit": [instance]}, slot="model") == []


# ---------------------------------------------------------------------------
# 3. Every ref resolves, and lands in the permitted value set
# ---------------------------------------------------------------------------


def test_a_ref_resolves_into_its_namespace() -> None:
    assert (
        check({"resistance": [{"args": {"version": "damage_type.poison", "N": 6}}]})
        == []
    )


def test_a_ref_into_an_unpermitted_namespace_is_rejected() -> None:
    (error,) = check({"resistance": [{"args": {"version": "terrain.forest", "N": 6}}]})

    assert "terrain.forest" in error
    assert "damage_type" in error


def test_a_ref_to_a_missing_record_is_rejected() -> None:
    (error,) = check(
        {"resistance": [{"args": {"version": "damage_type.sonic", "N": 6}}]}
    )

    assert "damage_type.sonic" in error


def test_an_unqualified_ref_is_rejected() -> None:
    (error,) = check({"resistance": [{"args": {"version": "poison", "N": 6}}]})

    assert "poison" in error
    assert "reference" in error


# ---------------------------------------------------------------------------
# 4. Args validate against the union of the rule's and every ref target's
# ---------------------------------------------------------------------------


def test_an_int_arg_outside_the_declared_values_is_rejected() -> None:
    (error,) = check({"assault_poison": [{"args": {"N": 5}}]}, slot="assault")

    assert "N" in error
    assert "5" in error


def test_a_union_arg_may_be_a_die() -> None:
    assert (
        check({"resistance": [{"args": {"version": "damage_type.poison", "N": "d6"}}]})
        == []
    )


def test_a_union_arg_may_not_be_prose() -> None:
    (error,) = check(
        {"resistance": [{"args": {"version": "damage_type.poison", "N": "some"}}]}
    )

    assert "an int or a die" in error


def test_an_unknown_arg_is_rejected() -> None:
    (error,) = check({"fear": [{"args": {"N": 6}}]}, slot="assault")

    assert "N" in error


def test_a_missing_arg_is_rejected() -> None:
    (error,) = check({"resistance": [{"args": {"version": "damage_type.poison"}}]})

    assert "N" in error


def test_a_ref_target_lends_its_variables_to_the_instance() -> None:
    # `terrain` is Camouflage's variable, not To Hit's: the arg set an instance
    # is checked against grows with the ref it carries.
    assert (
        check(
            {
                "to_hit": [
                    {
                        "args": {
                            "ability": "ability.camouflage",
                            "terrain": "terrain.forest",
                        }
                    }
                ]
            }
        )
        == []
    )


def test_a_ref_targets_variable_is_required_too() -> None:
    (error,) = check({"to_hit": [{"args": {"ability": "ability.camouflage"}}]})

    assert "terrain" in error


def test_a_variable_a_ref_target_does_not_lend_is_still_unknown() -> None:
    (error,) = check(
        {
            "to_hit": [
                {"args": {"ability": "ability.good_shot", "terrain": "terrain.forest"}}
            ]
        }
    )

    assert "terrain" in error


# ---------------------------------------------------------------------------
# 5. A rule variable colliding with a ref target's is an error
# ---------------------------------------------------------------------------


def test_a_variable_colliding_with_a_ref_targets_variable_is_rejected() -> None:
    # `shadowed` declares `terrain` itself, and `ability.camouflage` brings one
    # too -- one of the two has to be renamed, since a single arg cannot mean
    # both.
    errors = check(
        {
            "shadowed": [
                {"args": {"ability": "ability.camouflage", "terrain": "terrain.forest"}}
            ]
        }
    )

    assert any("terrain" in error and "collides" in error for error in errors)


# ---------------------------------------------------------------------------
# The registry itself
# ---------------------------------------------------------------------------


def test_the_committed_registries_load() -> None:
    registry = reg.load_registry()

    assert set(registry.namespaces) == set(registry.records)
    assert "resistance" in registry.records["special"]
    assert registry.records["damage_type"]["acid"].name == "Acid"


def test_a_record_is_resolved_by_its_qualified_ref() -> None:
    registry = reg.load_registry()

    assert registry.record("token.poison") is not None
    assert registry.record("token.nonesuch") is None
    assert registry.record("nonesuch.poison") is None


def test_the_gate_runs_against_the_committed_registries() -> None:
    # 7. Record completeness is wired in by construction: loading the registry
    # validates every record, so a rules file that fails phase 1's
    # exactly-one-of check fails a Race load too.
    errors = reg.check_instances(
        {
            "resistance": [
                SpecialInstance(args={"version": "damage_type.acid", "N": 12})
            ]
        },
        slot="unit",
        context="unit 'Armored Unicorn Rider'",
        registry=reg.load_registry(),
    )

    assert errors == []


def _copied_rules(tmp_path: Path) -> Path:
    """Copy the committed rules files somewhere a test may break one."""
    rules_dir = tmp_path / "rules"
    rules_dir.mkdir()
    for name in (
        "special.toml",
        "tokens.toml",
        "hexes.toml",
        "terrain.toml",
        "modifiers.toml",
        "namespaces.toml",
    ):
        (rules_dir / name).write_text((config.paths.rules / name).read_text())
    return rules_dir


def test_a_namespace_naming_a_file_nothing_reads_is_rejected(tmp_path: Path) -> None:
    rules_dir = _copied_rules(tmp_path)
    (rules_dir / "namespaces.toml").write_text(
        "[namespaces]\n"
        'order = { name = "Orders", file = "cards.toml", table = "order" }\n'
        "\n[damage_type.regular]\n"
        'name = "Regular"\ntodo = "Rule text not yet written."\n'
    )

    with pytest.raises(ValueError, match="No loader"):
        reg.load_registry(rules_dir)


def test_an_incomplete_rules_file_fails_to_load(tmp_path: Path) -> None:
    rules_dir = _copied_rules(tmp_path)
    (rules_dir / "special.toml").write_text(
        '[special.fear]\nname = "Fear"\nslots = ["assault"]\n'
    )

    with pytest.raises(ValidationError, match="exactly one of"):
        reg.load_registry(rules_dir)
