"""One simulated run, on synthetic Damage tables, against a scripted die."""

from collections.abc import Mapping
from typing import cast

from spf.schemas.type_aliases import DamageTable, DamageTableName
from spf.sim.dice import Dice
from spf.sim.effects import PlaceToken, Vocabulary
from spf.sim.engine import RunResult, run_once
from spf.sim.scenario import Hit, Scenario, Start
from spf.sim.tables import compile_table
from tests.sim.conftest import ScriptedRoller

VOCABULARY = Vocabulary(
    tokens={
        "dazed": "dazed",
        "shaken": "shaken",
        "crippled crew": "crippled_crew",
        "bleed": "bleed",
        "poison": "poison",
        "fire": "fire",
        "acid": "acid",
        "minor acid": "minor_acid",
    }
)
"""Token names the synthetic tables use. The Continuing Damage ids are real."""

LADDER = ["1-3: +1 to future damage", "4-5: Kill 1 model", "6+: Unit destroyed"]
"""A small Regular table: a nudge, a kill, and destruction at the top."""


def _scenario(  # noqa: PLR0913
    tables: Mapping[DamageTableName, list[str]] | None = None,
    *,
    models: int = 3,
    hits: list[str] | None = None,
    tokens: list[PlaceToken] | None = None,
    future: int = 0,
    notes: list[str] | None = None,
    resistance: Mapping[str, str] | None = None,
    endurance: int = 0,
    incoming: list[str] | None = None,
    max_rounds: int = 20,
) -> Scenario:
    tables = tables or {"Regular": LADDER}
    return Scenario(
        unit="Squad",
        models=models,
        tables={
            name: compile_table(
                name,
                DamageTable.model_validate(
                    {"rows": rows, "notes": (notes or []) if name == "Regular" else []}
                ),
                vocabulary=VOCABULARY,
            )
            for name, rows in tables.items()
        },
        start=Start(
            hits=[_hit(hit) for hit in hits or []],
            tokens=tokens or [],
            future=future,
        ),
        incoming=[_hit(hit) for hit in incoming or []],
        resistance={
            kind: Dice.parse(dice) for kind, dice in (resistance or {}).items()
        },
        endurance=endurance,
        max_rounds=max_rounds,
    )


def _hit(spelled: str) -> Hit:
    """Spell a hit `d6` for the Regular table or `table:d6` for another."""
    table, _, dice = spelled.rpartition(":")
    return Hit(
        dice=Dice.parse(dice),
        table=cast("DamageTableName", table.capitalize() or "Regular"),
    )


def _run(scenario: Scenario, rolls: list[tuple[int, int]]) -> RunResult:
    roller = ScriptedRoller(rolls)
    result = run_once(scenario, roller)
    assert roller.exhausted, "the run used fewer rolls than scripted"
    return result


def test_a_starting_hit_applies_its_row() -> None:
    result = _run(_scenario(hits=["d6"]), [(6, 4)])
    assert (result.destroyed, result.models_lost, result.rounds) == (False, 1, 0)
    assert result.ended_by == "no continuing damage"


def test_future_damage_adds_to_the_regular_roll() -> None:
    result = _run(_scenario(hits=["d6"], future=2), [(6, 4)])
    assert result.destroyed


def test_future_damage_is_placed_by_a_row() -> None:
    result = _run(_scenario(hits=["d6", "d6"]), [(6, 1), (6, 2)])
    assert result.snapshots[-1].future == 2
    assert result.models_lost == 0


def test_killing_the_last_model_destroys_the_unit() -> None:
    result = _run(_scenario(models=1, hits=["d6"]), [(6, 5)])
    assert (result.destroyed, result.models_lost) == (True, 1)
    assert result.ended_by == "destroyed"


def test_a_destroyed_unit_stops_resolving() -> None:
    result = _run(_scenario(hits=["d6", "d6"]), [(6, 6)])
    assert result.destroyed
    assert result.models_lost == 3


def test_damage_on_another_table_ignores_future_damage() -> None:
    tables: dict[DamageTableName, list[str]] = {
        "Regular": ["1+: d6 psychic damage"],
        "Psychic": ["1-4: Dazed", "5+: Kill 1 model"],
    }
    result = _run(_scenario(tables, hits=["d6"], future=5), [(6, 1), (6, 4)])
    assert result.models_lost == 0
    assert result.snapshots[-1].tokens["dazed"] == 1
    assert result.table_rolls == {"Regular": 1, "Psychic": 1}


def test_a_missing_table_has_no_effect_but_is_counted() -> None:
    tables: dict[DamageTableName, list[str]] = {"Regular": ["1+: d6 critical damage"]}
    result = _run(_scenario(tables, hits=["d6"]), [(6, 1), (6, 6)])
    assert result.missing_tables == {"Critical": 1}


def test_shaken_is_placed_twice_the_first_time() -> None:
    tables: dict[DamageTableName, list[str]] = {"Regular": ["1+: Shaken"]}
    once = _run(_scenario(tables, hits=["d6"]), [(6, 1)])
    twice = _run(_scenario(tables, hits=["d6", "d6"]), [(6, 1), (6, 1)])
    assert once.snapshots[0].tokens["shaken"] == 2
    assert twice.snapshots[0].tokens["shaken"] == 3


def test_crippled_crew_and_shaken_turn_psychic_into_crew_damage() -> None:
    tables: dict[DamageTableName, list[str]] = {
        "Regular": ["1: Crippled Crew", "2: Shaken", "3+: d6 psychic damage"],
        "Psychic": ["1+: Dazed"],
        "Crew": ["1-6: +1 to future crew damage", "7+: Unit destroyed"],
    }
    rolls = [(6, 1), (6, 2), (6, 3), (6, 6), (6, 3), (6, 6)]
    result = _run(_scenario(tables, hits=["d6"] * 4), rolls)
    assert result.table_rolls == {"Regular": 4, "Crew": 2}
    assert result.destroyed


def test_unparsed_and_spillover_are_counted() -> None:
    tables: dict[DamageTableName, list[str]] = {
        "Regular": ["1+: Rotate unit, d4 damage to all transported units"]
    }
    result = _run(_scenario(tables, hits=["d6", "d6"]), [(6, 1), (6, 2)])
    assert result.unparsed == {("Regular", "1+", "Rotate unit"): 2}
    assert result.spillover == {"d4 damage to all transported units": 2}


def _bleed(strength: int) -> PlaceToken:
    return PlaceToken(name="bleed", strength=strength)


def test_bleed_ends_at_a_one() -> None:
    result = _run(_scenario(tokens=[_bleed(4)]), [(4, 1)])
    assert (result.rounds, result.ended_by) == (1, "no continuing damage")
    assert result.snapshots[0].tokens["bleed"] == 1
    assert result.snapshots[1].tokens["bleed"] == 0


def test_bleed_rolls_on_the_regular_table_with_future_damage() -> None:
    result = _run(_scenario(tokens=[_bleed(6)], future=1), [(6, 2), (6, 1)])
    assert result.rounds == 2
    assert [snapshot.future for snapshot in result.snapshots] == [1, 2, 2]


def test_bleed_that_kills_a_model_is_removed() -> None:
    result = _run(_scenario(tokens=[_bleed(4)]), [(4, 4)])
    assert (result.rounds, result.models_lost) == (1, 1)
    assert result.snapshots[-1].tokens["bleed"] == 0


def test_each_bleed_rolls_on_its_own() -> None:
    result = _run(_scenario(tokens=[_bleed(4), _bleed(8)]), [(4, 1), (8, 1)])
    assert result.rounds == 1


def test_a_run_stops_at_the_round_cap() -> None:
    tables: dict[DamageTableName, list[str]] = {"Regular": ["1+: Dazed"]}
    scenario = _scenario(tables, tokens=[_bleed(4)], max_rounds=3)
    result = _run(scenario, [(4, 2)] * 3)
    assert (result.rounds, result.ended_by) == (3, "max rounds")
    assert result.snapshots[-1].tokens["dazed"] == 3


def _poison(strength: int) -> PlaceToken:
    return PlaceToken(name="poison", strength=strength)


def test_poison_downgrades_when_it_does_not_kill() -> None:
    result = _run(_scenario(tokens=[_poison(6)]), [(6, 2), (4, 2)])
    assert (result.rounds, result.ended_by) == (2, "no continuing damage")
    assert [snapshot.future for snapshot in result.snapshots] == [0, 1, 2]
    assert [snapshot.tokens["poison"] for snapshot in result.snapshots] == [1, 1, 0]


def test_poison_that_kills_a_model_is_removed() -> None:
    result = _run(_scenario(tokens=[_poison(8)]), [(8, 5)])
    assert (result.rounds, result.models_lost) == (1, 1)
    assert result.snapshots[-1].tokens["poison"] == 0


FIRE = PlaceToken(name="fire")


def test_fire_goes_out_at_a_one() -> None:
    result = _run(_scenario(tokens=[FIRE]), [(6, 1)])
    assert (result.rounds, result.snapshots[-1].tokens["fire"]) == (1, 0)


def test_fire_burns_on_the_regular_table_and_keeps_burning() -> None:
    result = _run(_scenario(tokens=[FIRE], max_rounds=2), [(6, 2), (6, 2)])
    assert result.ended_by == "max rounds"
    assert [snapshot.future for snapshot in result.snapshots] == [0, 1, 2]
    assert result.snapshots[-1].tokens["fire"] == 1


def test_fire_accumulates_and_every_token_rolls() -> None:
    tables: dict[DamageTableName, list[str]] = {
        "Regular": ["1-5: Fire", "6+: Kill 1 model"]
    }
    scenario = _scenario(tables, hits=["d6", "d6"], max_rounds=1)
    result = _run(scenario, [(6, 1), (6, 1), (6, 6), (6, 1)])
    assert result.snapshots[0].tokens["fire"] == 2
    assert result.snapshots[1].tokens["fire"] == 1
    assert result.models_lost == 1


MINOR_ACID = PlaceToken(name="minor_acid")
ACID = PlaceToken(name="acid")


def test_minor_acid_adds_future_damage_until_it_fails() -> None:
    result = _run(_scenario(tokens=[MINOR_ACID]), [(6, 3), (6, 2)])
    assert (result.rounds, result.ended_by) == (2, "no continuing damage")
    assert result.snapshots[-1].future == 1


def test_acid_at_one_downgrades_to_minor_acid_that_rolls_the_same_round() -> None:
    result = _run(_scenario(tokens=[ACID]), [(8, 1), (6, 1)])
    assert result.rounds == 1
    tokens = result.snapshots[1].tokens
    assert (tokens["acid"], tokens["minor_acid"]) == (0, 0)


def test_acid_adds_future_damage_and_stays() -> None:
    result = _run(_scenario(tokens=[ACID], max_rounds=1), [(8, 2)])
    assert result.ended_by == "max rounds"
    assert result.snapshots[-1].future == 1
    assert result.snapshots[-1].tokens["acid"] == 1


def test_acid_spills_onto_the_hex_and_places_terror() -> None:
    result = _run(_scenario(tokens=[ACID], max_rounds=1), [(8, 6)])
    assert result.snapshots[-1].future == 1
    assert result.snapshots[-1].tokens["terror"] == 1
    assert sum(result.spillover.values()) == 2


def test_terror_spills_onto_friendly_units_each_round() -> None:
    scenario = _scenario(tokens=[ACID, PlaceToken(name="terror")], max_rounds=1)
    result = _run(scenario, [(8, 2)])
    assert sum(result.spillover.values()) == 1


def test_acid_at_seven_sets_the_unit_on_fire() -> None:
    result = _run(_scenario(tokens=[ACID], max_rounds=1), [(8, 7), (6, 1)])
    assert result.snapshots[-1].tokens["terror"] == 1


def test_acid_at_eight_rolls_three_more_times() -> None:
    scenario = _scenario(tokens=[ACID], max_rounds=1)
    result = _run(scenario, [(8, 8), (8, 2), (8, 2), (8, 2)])
    assert result.snapshots[-1].future == 3


def test_amplify_bleeding_steps_every_bleed_up_to_twelve() -> None:
    tables: dict[DamageTableName, list[str]] = {"Regular": ["1+: Amplify all bleeding"]}
    scenario = _scenario(tables, hits=["d6"], tokens=[_bleed(4), _bleed(12)])
    result = _run(scenario, [(6, 1), (6, 1), (12, 1)])
    assert result.rounds == 1


def test_amplify_if_caused_by_bleeding_ignores_other_hits() -> None:
    tables: dict[DamageTableName, list[str]] = {
        "Regular": ["1-2: Dazed", "3+: if caused by bleeding, amplify bleeding"]
    }
    scenario = _scenario(tables, hits=["d6"], tokens=[_bleed(4)])
    result = _run(scenario, [(6, 3), (4, 3), (6, 1)])
    assert result.rounds == 2


def test_roll_again_rerolls_the_same_dice() -> None:
    tables: dict[DamageTableName, list[str]] = {
        "Regular": ["1: Dazed", "2: Roll two times on this table"]
    }
    result = _run(_scenario(tables, hits=["d6"]), [(6, 2), (6, 1), (6, 1)])
    assert result.snapshots[0].tokens["dazed"] == 2


def test_attrition_lands_incoming_hits_every_round() -> None:
    scenario = _scenario(incoming=["d6"], max_rounds=2)
    result = _run(scenario, [(6, 1), (6, 1)])
    assert (result.rounds, result.ended_by) == (2, "max rounds")
    assert [snapshot.future for snapshot in result.snapshots] == [0, 1, 2]


def test_incoming_hits_land_before_the_agony_phases() -> None:
    tables: dict[DamageTableName, list[str]] = {
        "Regular": ["1-3: Bleed[4]", *LADDER[1:]]
    }
    scenario = _scenario(tables, models=1, incoming=["d6"])
    result = _run(scenario, [(6, 1), (4, 4)])
    assert (result.rounds, result.ended_by) == (1, "destroyed")


def test_a_run_stops_when_the_unit_is_destroyed() -> None:
    result = _run(_scenario(models=1, tokens=[_bleed(4)]), [(4, 4)])
    assert (result.rounds, result.ended_by, result.destroyed) == (1, "destroyed", True)
