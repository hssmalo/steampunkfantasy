"""Tests for resolving an Army's Rules Reference (ADR 0029)."""

import pytest

from spf.armies.army import Army
from spf.armies.model import Model
from spf.armies.unit import Unit
from spf.registry import Registry
from spf.render import rules_reference as rr
from spf.schemas import rules as r
from spf.schemas.race import (
    AssaultConfig,
    ModelConfig,
    OrdersConfig,
    ShakenConfig,
    UnitConfig,
)
from spf.schemas.special import SpecialInstance, Specials

_ASSAULT = AssaultConfig(
    strength=[1, 0, 0, 0],
    strength_die="4+",
    deflection=[1, 0, 0, 0],
    deflection_die="4+",
    damage="d4",
    ap=0,
)


def _army(unit_specials: Specials) -> Army:
    """Build a one-Unit, one-Model Army carrying `unit_specials`."""
    model = Model(
        name="Soldier",
        config=ModelConfig(
            race="elf",
            name="Soldier",  # pyright: ignore[reportArgumentType]
            equipment_limit=[],  # pyright: ignore[reportArgumentType]
            equipment=[],
            type=["Infantry"],
            assault=_ASSAULT,
            cost=None,
        ),
        default_equipment=[],
        upgrade_equipment=[],
    )
    unit = Unit(
        name="Squad",
        config=UnitConfig(
            race="elf",
            name="Squad",  # pyright: ignore[reportArgumentType]
            models=["Soldier"],  # pyright: ignore[reportArgumentType]
            size="Small",  # pyright: ignore[reportArgumentType]
            shaken=ShakenConfig(
                speed="slow", movement_order=["-", "-", "flee"], fire_order="None"
            ),
            orders=OrdersConfig(),
            specials=unit_specials,
            damage_tables={},
        ),
        models=[model],
    )
    return Army(race="elf", nick="Test", units=[unit])  # pyright: ignore[reportArgumentType]


def _namespaces() -> dict[str, r.NamespaceConfig]:
    return {
        "special": r.NamespaceConfig(
            name="Specials", label="special", file="special.toml", table="special"
        ),
        "token": r.NamespaceConfig(
            name="Tokens", label="token", file="tokens.toml", table="tokens"
        ),
        "hex": r.NamespaceConfig(
            name="Hex Effects", label="hex", file="hexes.toml", table="hexes"
        ),
        "damage_type": r.NamespaceConfig(
            name="Damage Types",
            label="damage type",
            file="namespaces.toml",
            table="damage_type",
        ),
        "ability": r.NamespaceConfig(
            name="Abilities", label="ability", file="modifiers.toml", table="ability"
        ),
    }


def _special(name: str, **kwargs: object) -> r.SpecialRuleConfig:
    return r.SpecialRuleConfig.model_validate(
        {"name": name, "slots": ["unit"]} | kwargs
    )


REGISTRY = Registry(
    namespaces=_namespaces(),
    records={
        "special": {
            "terror": _special(
                "Terror", effect="Place a Terror token.", see_also=["token.terror"]
            ),
            "fog": _special("Fog", effect="Fog rolls in.", see_also=["hex.fog"]),
            "resistance": _special("Resistance", effect="Ignore {N} damage."),
            "burst": _special("Burst", effect="Hits every model."),
            "corrode": _special(
                "Corrode", effect="Corrodes the target.", see_also=["token.acid"]
            ),
            "assault_poison": _special(
                "Assault Poison",
                effect="Poisons on a hit.",
                places=["token.poison"],
                see_also=["special.range_poison"],
            ),
            "range_poison": _special(
                "Range Poison",
                effect="Poisons at range.",
                places=["token.poison"],
                see_also=["special.assault_poison"],
            ),
            "unwritten": _special("Unwritten", todo="Nobody has written this."),
            "to_hit": _special("To Hit", effect="Shift the roll."),
        },
        "token": {
            "terror": r.TokenRuleConfig(
                name="Terror",
                effect="The model may not advance.",
                phases=["Aftermath"],
                remove="At the end of the round.",
            ),
            "poison": r.TokenRuleConfig(name="Poison", effect="Take 1 damage."),
            "acid": r.TokenRuleConfig(
                name="Acid",
                effect="Set the unit on fire.",
                places=["token.fire"],
                see_also=["damage_type.poison"],
            ),
            "fire": r.TokenRuleConfig(name="Fire", effect="Take d6 damage."),
        },
        "hex": {
            "fog": r.HexRuleConfig(
                name="Fog", effect="Line of sight is blocked.", remove="After a round."
            )
        },
        "damage_type": {
            "poison": r.DamageTypeRuleConfig(name="Poison", effect="Damage over time.")
        },
        "ability": {
            "good_shot": r.ModifierRuleConfig(name="Good Shot", to_hit="+1"),
        },
    },
)


def _resolve(
    *refs: str, aliases: list[tuple[str, str]] | None = None, prefix: str = ""
) -> rr.RulesReference:
    return rr.resolve(
        rr.Seeds(refs=list(refs), aliases=aliases or []), REGISTRY, prefix=prefix
    )


def _refs(reference: rr.RulesReference) -> list[str]:
    return [entry.ref for entry in reference.entries]


# --- The traversal ----------------------------------------------------------


def test_a_seed_becomes_an_entry() -> None:
    assert _refs(_resolve("special.burst")) == ["special.burst"]


def test_places_is_followed() -> None:
    reference = _resolve("special.assault_poison")

    assert "token.poison" in _refs(reference)


def test_a_places_cycle_terminates() -> None:
    # `assault_poison` and `range_poison` see_also each other; a visited-set is
    # what keeps a legal cycle from looping forever.
    reference = _resolve("special.assault_poison", "special.range_poison")

    assert _refs(reference).count("token.poison") == 1


def test_a_see_also_into_a_player_facing_namespace_is_promoted() -> None:
    # A token is a physical thing on the table, so it prints its own rule.
    reference = _resolve("special.terror")

    assert "token.terror" in _refs(reference)


def test_a_see_also_into_special_is_not_promoted() -> None:
    # Another Special is editorial cross-reference, not a thing to resolve.
    reference = _resolve("special.assault_poison")

    assert "special.range_poison" not in _refs(reference)


def test_a_hex_reached_only_by_see_also_prints_its_rule() -> None:
    reference = _resolve("special.fog")

    hex_entry = next(e for e in reference.entries if e.ref == "hex.fog")
    assert hex_entry.effect == "Line of sight is blocked."


def test_a_promoted_records_own_places_are_followed() -> None:
    # A promoted token that sets the unit on fire is no more explained without
    # the Fire token than a seeded rule would be.
    reference = _resolve("special.corrode")

    assert set(_refs(reference)) == {"special.corrode", "token.acid", "token.fire"}


def test_see_also_is_not_followed_from_a_promoted_record() -> None:
    # `places` is unbounded from everything; `see_also` stays one hop from the
    # rules the Army's own Specials reach, which is what bounds the walk.
    reference = _resolve("special.corrode")

    assert "damage_type.poison" not in _refs(reference)


def test_see_also_is_followed_one_hop_only() -> None:
    # `special.terror` promotes `token.terror`; nothing that token points at
    # joins in turn.
    reference = _resolve("special.terror")

    assert set(_refs(reference)) == {"special.terror", "token.terror"}


# --- Cross-references -------------------------------------------------------


def test_an_unpromoted_see_also_becomes_a_cross_reference() -> None:
    reference = _resolve("special.assault_poison")

    entry = next(e for e in reference.entries if e.ref == "special.assault_poison")
    assert [(link.name, link.qualifier) for link in entry.see_also] == [
        ("Range Poison", "special")
    ]


def test_a_cross_reference_links_when_its_target_is_an_entry() -> None:
    reference = _resolve("special.assault_poison", "special.range_poison")

    entry = next(e for e in reference.entries if e.ref == "special.assault_poison")
    assert entry.see_also[0].anchor == "rule-special-range-poison"


def test_a_cross_reference_to_a_non_entry_carries_no_anchor() -> None:
    reference = _resolve("special.assault_poison")

    entry = next(e for e in reference.entries if e.ref == "special.assault_poison")
    assert entry.see_also[0].anchor is None


def test_a_promoted_see_also_keeps_its_cross_reference_line() -> None:
    # A Stub whose `see_also` is the only thing explaining it would otherwise
    # print a heading and nothing else, beside the entry that explains it.
    reference = _resolve("special.terror")

    entry = next(e for e in reference.entries if e.ref == "special.terror")
    assert entry.see_also == [
        rr.RuleLink(name="Terror", qualifier="token", anchor="rule-token-terror")
    ]


# --- Entry content ----------------------------------------------------------


def test_a_stub_prints_the_pending_marker() -> None:
    reference = _resolve("special.unwritten")

    entry = reference.entries[0]
    assert (entry.written, entry.pending) == (False, True)


def test_a_written_rule_is_not_pending() -> None:
    assert _resolve("special.burst").entries[0].pending is False


def test_the_generic_text_keeps_its_placeholders() -> None:
    # The Unit line prints the filled signature; the general rule lives here.
    assert _resolve("special.resistance").entries[0].effect == "Ignore {N} damage."


def test_an_entry_carries_the_phases_and_removal_its_record_declares() -> None:
    entry = _resolve("token.terror").entries[0]

    assert (entry.phases, entry.remove) == (["Aftermath"], "At the end of the round.")


def test_a_record_with_no_such_fields_carries_neither() -> None:
    entry = _resolve("special.burst").entries[0]

    assert (entry.phases, entry.remove) == ([], None)


def test_a_modifier_record_prints_the_numbers_that_are_its_meaning() -> None:
    entry = _resolve("ability.good_shot").entries[0]

    assert (entry.to_hit, entry.pending) == ("+1", False)


# --- Kind Qualifiers and ordering -------------------------------------------


def test_every_entry_carries_a_kind_qualifier() -> None:
    reference = _resolve("special.terror", "token.poison", "damage_type.poison")

    assert {e.qualifier for e in reference.entries} == {
        "special",
        "token",
        "damage type",
    }


def test_both_members_of_a_name_collision_are_qualified() -> None:
    reference = _resolve("token.poison", "damage_type.poison")

    assert [e.heading for e in reference.entries] == [
        "Poison (damage type)",
        "Poison (token)",
    ]


def test_entries_sort_alphabetically_across_namespaces() -> None:
    reference = _resolve("special.terror", "hex.fog", "special.burst")

    assert [e.name for e in reference.entries] == ["Burst", "Fog", "Terror", "Terror"]


# --- Alias Entries ----------------------------------------------------------


def test_an_atmospheric_name_gets_its_own_alias_entry() -> None:
    reference = _resolve(
        "special.terror", aliases=[("Insanity Field", "special.terror")]
    )

    alias = next(e for e in reference.entries if e.name == "Insanity Field")
    assert alias.alias_for == rr.RuleLink(
        name="Terror", qualifier="special", anchor="rule-special-terror"
    )


def test_an_alias_files_alphabetically_among_the_rules() -> None:
    reference = _resolve(
        "special.terror",
        "special.burst",
        aliases=[("Insanity Field", "special.terror")],
    )

    assert [e.name for e in reference.entries][:2] == ["Burst", "Insanity Field"]


def test_a_name_matching_its_records_own_name_is_no_alias() -> None:
    reference = _resolve("special.terror", aliases=[("Terror", "special.terror")])

    assert [e.alias_for for e in reference.entries] == [None, None]


def test_one_name_over_two_records_gets_an_entry_each() -> None:
    # Dropping the second would silently redirect its readers to the wrong
    # rule, which is worse than listing the name twice.
    reference = _resolve(
        "special.terror",
        "special.burst",
        aliases=[("Dread", "special.terror"), ("Dread", "special.burst")],
    )

    dread = [e for e in reference.entries if e.name == "Dread"]
    assert [e.alias_for.name for e in dread if e.alias_for] == ["Terror", "Burst"]
    assert len({e.anchor for e in dread}) == 2


def test_the_same_alias_twice_over_one_record_is_one_entry() -> None:
    reference = _resolve(
        "special.terror",
        aliases=[("Insanity Field", "special.terror")] * 3,
    )

    assert [e.name for e in reference.entries].count("Insanity Field") == 1


def test_an_alias_carries_its_own_anchor() -> None:
    reference = _resolve(
        "special.terror", aliases=[("Insanity Field", "special.terror")]
    )

    alias = next(e for e in reference.entries if e.name == "Insanity Field")
    assert alias.anchor == "rule-alias-insanity-field"


# --- Anchors ----------------------------------------------------------------


def test_an_anchor_derives_from_the_qualified_ref() -> None:
    reference = _resolve("hex.fog", "special.fog")

    assert [e.anchor for e in reference.entries] == ["rule-hex-fog", "rule-special-fog"]


def test_a_prefix_namespaces_every_anchor() -> None:
    reference = _resolve("special.terror", prefix="abomination-")

    assert reference.entries[0].anchor == "abomination-rule-special-terror"


def test_a_specials_anchor_is_looked_up_by_its_identifier() -> None:
    reference = _resolve("special.terror", prefix="abomination-")

    assert reference.anchor_for("terror") == "abomination-rule-special-terror"


def test_an_identifier_that_is_no_entry_has_no_anchor() -> None:
    assert _resolve("special.terror").anchor_for("burst") is None


# --- Seeding from a resolved Army -------------------------------------------


def test_a_ref_valued_argument_seeds_the_record_it_names() -> None:
    # A Resistance whose Appendix says nothing about poison is the failure the
    # Rules Reference exists to prevent.
    army = _army(
        {
            "resistance": [
                SpecialInstance(args={"version": "damage_type.poison", "N": 3})
            ]
        }
    )

    assert "damage_type.poison" in rr.seeds(army, registry=REGISTRY).refs


def test_a_scalar_argument_seeds_nothing() -> None:
    army = _army({"resistance": [SpecialInstance(args={"N": 3})]})

    assert rr.seeds(army, registry=REGISTRY).refs == ["special.resistance"]


def test_an_instances_atmospheric_name_is_collected_as_an_alias() -> None:
    army = _army({"terror": [SpecialInstance(name="Insanity Field")]})

    assert rr.seeds(army, registry=REGISTRY).aliases == [
        ("Insanity Field", "special.terror")
    ]


if __name__ == "__main__":  # pragma: no cover
    pytest.main([__file__])
