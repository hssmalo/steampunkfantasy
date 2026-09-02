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
                        "variants": {
                            "while_an_elite_lives": "While at least one elite is alive",
                            "versus_shaken": "Versus Shaken models",
                        },
                    }
                ),
                "venom": r.SpecialRuleConfig.model_validate(
                    {
                        "name": "Venom",
                        "slots": ["assault"],
                        "effect": "One poison token per {N} hits.",
                        "variables": {
                            "N": {"type": "int", "values": [4, 6, 8, 10, 12]},
                            "M": {"type": "int", "min": 1, "max": 4, "optional": True},
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
                "endurance": r.SpecialRuleConfig.model_validate(
                    {
                        "name": "Endurance",
                        "slots": ["unit"],
                        "effect": "Gets {N} endurance tokens as a {model_class}.",
                        "variables": {
                            "N": {"type": "int"},
                            "model_class": {"type": "str"},
                        },
                    }
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
                "fire_order": r.SpecialRuleConfig.model_validate(
                    {
                        "name": "Fire Order",
                        "slots": ["unit"],
                        "effect": "Fires {N} shots.",
                        "variables": {"N": {"type": "int", "optional": True}},
                        "variants": {
                            "load_n_shots": "May load up to {N} shots",
                            "fire_together": "Fire every weapon at once",
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
    (error,) = check({"venom": [{"args": {"N": 5}}]}, slot="assault")

    assert "N" in error
    assert "5" in error


def test_an_optional_variable_may_be_left_out() -> None:
    assert check({"venom": [{"args": {"N": 6}}]}, slot="assault") == []


def test_a_required_variable_left_out_is_still_rejected() -> None:
    (error,) = check({"venom": [{"args": {"M": 2}}]}, slot="assault")

    assert "missing argument 'N'" in error


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


def test_an_unbounded_int_arg_is_still_type_checked() -> None:
    # `endurance.N` declares no min, max or values, so the type is the whole
    # constraint -- and it is the constraint that gets interpolated.
    (error,) = check(
        {"endurance": [{"args": {"N": "not a number", "model_class": "elite model"}}]}
    )

    assert "N" in error
    assert "not an int" in error


def test_an_unbounded_str_arg_is_still_type_checked() -> None:
    (error,) = check({"endurance": [{"args": {"N": 2, "model_class": 7}}]})

    assert "model_class" in error
    assert "not a str" in error


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
# 4b. A case-shaped instance validates once per case, over merged args
# ---------------------------------------------------------------------------


def test_every_case_of_an_instance_is_checked() -> None:
    errors = check({"endurance": [{"cases": [{"args": {"N": 1}}, {"args": {"N": 2}}]}]})

    assert len(errors) == 2
    assert all("missing argument 'model_class'" in error for error in errors)


def test_a_broken_case_names_its_position() -> None:
    (error,) = check(
        {
            "endurance": [
                {
                    "args": {"model_class": "Infantry"},
                    "cases": [{"args": {"N": 1}}, {}],
                }
            ]
        }
    )

    assert "case 2" in error
    assert "missing argument 'N'" in error


def test_an_instance_level_arg_satisfies_every_case() -> None:
    errors = check(
        {
            "endurance": [
                {
                    "args": {"model_class": "Infantry"},
                    "cases": [{"args": {"N": 1}}, {"args": {"N": 2}}],
                }
            ]
        }
    )

    assert errors == []


def test_a_case_may_override_an_instance_level_arg() -> None:
    errors = check(
        {
            "endurance": [
                {
                    "args": {"N": 1, "model_class": "Infantry"},
                    "cases": [{"args": {"N": 2}}],
                }
            ]
        }
    )

    assert errors == []


def test_an_unknown_arg_in_a_case_is_rejected() -> None:
    (error,) = check({"fear": [{"cases": [{"args": {"N": 6}}]}]}, slot="assault")

    assert "case 1" in error
    assert "N" in error


def test_a_ref_named_on_the_instance_lends_its_variables_to_every_case() -> None:
    # The ref is written once on the instance; the variables it lends are in
    # scope for every case.
    errors = check(
        {
            "resistance": [
                {
                    "args": {"version": "damage_type.poison"},
                    "cases": [{"args": {"N": 1}}, {"args": {"N": 2}}],
                }
            ]
        }
    )

    assert errors == []


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
# Every named variant is one the rule defines (ADR 0032)
# ---------------------------------------------------------------------------


def test_a_known_variant_resolves() -> None:
    errors = check(
        {
            "resistance": [
                {
                    "variant": "while_an_elite_lives",
                    "args": {"version": "damage_type.poison", "N": 4},
                }
            ]
        }
    )

    assert errors == []


def test_an_unknown_variant_is_rejected() -> None:
    errors = check(
        {
            "resistance": [
                {
                    "variant": "while_an_elite_lved",
                    "args": {"version": "damage_type.poison", "N": 4},
                }
            ]
        }
    )

    # The pool is the rule's own, so naming it is what makes the typo findable.
    assert errors == [
        "unit 'Squad': 'resistance': no variant 'while_an_elite_lved';"
        " the rule defines versus_shaken, while_an_elite_lives"
    ]


def test_a_variant_on_a_rule_defining_none_is_rejected() -> None:
    errors = check({"fear": [{"variant": "whenever"}]}, slot="assault")

    assert errors == [
        "unit 'Squad': 'fear': no variant 'whenever'; the rule defines none"
    ]


def test_an_unknown_variant_on_a_case_names_its_position() -> None:
    errors = check(
        {
            "resistance": [
                {
                    "args": {"version": "damage_type.poison"},
                    "cases": [
                        {"variant": "while_an_elite_lives", "args": {"N": 4}},
                        {"variant": "versus_shakn", "args": {"N": 6}},
                    ],
                }
            ]
        }
    )

    assert errors == [
        "unit 'Squad': 'resistance', case 2: no variant 'versus_shakn';"
        " the rule defines versus_shaken, while_an_elite_lives"
    ]


def test_a_case_shaped_instances_own_variant_is_checked_too() -> None:
    # The preamble slot resolves against the same pool as a case's text.
    errors = check(
        {
            "resistance": [
                {
                    "variant": "no_such_preamble",
                    "args": {"version": "damage_type.poison"},
                    "cases": [{"args": {"N": 4}}],
                }
            ]
        }
    )

    assert any("no variant 'no_such_preamble'" in error for error in errors)


# ---------------------------------------------------------------------------
# Every placeholder the instance's prose writes is filled (ADR 0037)
# ---------------------------------------------------------------------------


def test_a_filled_placeholder_resolves() -> None:
    errors = check({"fire_order": [{"variant": "load_n_shots", "args": {"N": 5}}]})

    assert errors == []


def test_a_variant_naming_an_argument_the_instance_omits_is_rejected() -> None:
    errors = check({"fire_order": [{"variant": "load_n_shots"}]})

    # `optional` is a claim about the variable, not about the prose naming it.
    assert errors == [
        "unit 'Squad': 'fire_order': variant 'load_n_shots' names {N},"
        " and the instance gives no N"
    ]


def test_inline_prose_naming_an_argument_the_instance_omits_is_rejected() -> None:
    # Checking only variants would make `text` the way around the gate.
    errors = check({"fire_order": [{"text": "May load up to {N} shots"}]})

    assert errors == [
        "unit 'Squad': 'fire_order': prose names {N}, and the instance gives no N"
    ]


def test_a_variant_naming_no_placeholder_needs_no_argument() -> None:
    errors = check({"fire_order": [{"variant": "fire_together"}]})

    assert errors == []


def test_a_case_may_supply_what_the_instance_omits() -> None:
    errors = check(
        {
            "fire_order": [
                {"cases": [{"variant": "load_n_shots", "args": {"N": 5}}]},
            ]
        }
    )

    assert errors == []


def test_a_cases_prose_naming_an_unsupplied_argument_names_its_position() -> None:
    errors = check(
        {
            "fire_order": [
                {
                    "cases": [
                        {"variant": "load_n_shots", "args": {"N": 5}},
                        {"variant": "load_n_shots"},
                    ]
                }
            ]
        }
    )

    assert errors == [
        "unit 'Squad': 'fire_order', case 2: variant 'load_n_shots' names {N},"
        " and the instance gives no N"
    ]


def test_a_preamble_does_not_see_the_args_its_cases_supply() -> None:
    # The author's instinct is that the value is right there in the file below.
    errors = check(
        {
            "fire_order": [
                {
                    "variant": "load_n_shots",
                    "cases": [{"args": {"N": 5}}, {"args": {"N": 2}}],
                }
            ]
        }
    )

    assert errors == [
        "unit 'Squad': 'fire_order': a preamble scopes every case, so it sees"
        " only the instance's args; N is given by cases 1 and 2"
    ]


# ---------------------------------------------------------------------------
# The registry itself
# ---------------------------------------------------------------------------


def test_the_committed_registries_load() -> None:
    # That every declared namespace was loaded, not which records it holds:
    # naming one here would make adding or renaming a rule a test edit.
    registry = reg.load_registry()

    assert set(registry.namespaces) == set(registry.records)
    assert all(registry.records[namespace] for namespace in registry.namespaces)


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
        'order = { name = "Orders", label = "order", file = "cards.toml",'
        ' table = "order" }\n'
        "\n[damage_type.regular]\n"
        'name = "Regular"\ntodo = "Rule text not yet written."\n'
    )

    with pytest.raises(ValueError, match="No loader"):
        reg.load_registry(rules_dir)


def test_a_namespace_grouped_under_nothing_is_rejected(tmp_path: Path) -> None:
    # A display group is another namespace, and a dangling one would drop its
    # members out of the to-hit table without saying so.
    rules_dir = _copied_rules(tmp_path)
    (rules_dir / "namespaces.toml").write_text(
        "[namespaces]\n"
        'hex = { name = "Hexes", label = "hex", file = "hexes.toml",'
        ' table = "hexes", group = "terrain" }\n'
        "\n[damage_type.regular]\n"
        'name = "Regular"\ntodo = "Rule text not yet written."\n'
    )

    with pytest.raises(ValueError, match="undeclared group: terrain"):
        reg.load_registry(rules_dir)


def test_an_incomplete_rules_file_fails_to_load(tmp_path: Path) -> None:
    rules_dir = _copied_rules(tmp_path)
    (rules_dir / "special.toml").write_text(
        '[special.fear]\nname = "Fear"\nslots = ["assault"]\n'
    )

    with pytest.raises(ValidationError, match="has neither"):
        reg.load_registry(rules_dir)


def test_a_version_overlay_pointing_nowhere_fails_to_load(tmp_path: Path) -> None:
    # A version overlay is keyed by a ref, so a typo is a ref that resolves to
    # no record -- otherwise the overlay is silently invisible.
    rules_dir = _copied_rules(tmp_path)
    (rules_dir / "special.toml").write_text(
        '[special.fear]\nname = "Fear"\nslots = ["assault"]\n'
        'effect = "Causes fear."\n'
        '\n[special.fear.versions."damage_type.nonesuch"]\n'
        'effect = "Fear of the unknown."\n'
    )

    with pytest.raises(ValueError, match=r"damage_type\.nonesuch"):
        reg.load_registry(rules_dir)
