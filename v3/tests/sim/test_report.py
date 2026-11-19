"""Many runs of a Scenario, gathered into the report.

The tables are built so each outcome is certain, so the expected figures hold
whatever the dice do.
"""

from collections.abc import Mapping

from spf.schemas.type_aliases import DamageTable, DamageTableName
from spf.sim.dice import Dice
from spf.sim.effects import PlaceToken, Vocabulary
from spf.sim.report import simulate
from spf.sim.scenario import Hit, Scenario, Start
from spf.sim.tables import compile_table

VOCABULARY = Vocabulary(tokens={"dazed": "dazed", "bleed": "bleed"})


def _scenario(
    tables: Mapping[DamageTableName, list[str]],
    *,
    hits: int = 1,
    tokens: list[PlaceToken] | None = None,
    max_rounds: int = 20,
) -> Scenario:
    return Scenario(
        unit="Squad",
        models=4,
        tables={
            name: compile_table(
                name, DamageTable.model_validate({"rows": rows}), vocabulary=VOCABULARY
            )
            for name, rows in tables.items()
        },
        start=Start(hits=[Hit(dice=Dice.parse("d6"))] * hits, tokens=tokens or []),
        max_rounds=max_rounds,
    )


def test_certain_destruction() -> None:
    report = simulate(_scenario({"Regular": ["1+: Unit destroyed"]}), runs=50, seed=1)
    assert report.p_destroyed == 1.0
    assert (report.models_lost.mean, report.models_lost.p90) == (4, 4)
    assert report.ended_by == {"destroyed": 50}


def test_models_lost_statistics() -> None:
    report = simulate(
        _scenario({"Regular": ["1+: Kill 1 model"]}, hits=2), runs=20, seed=1
    )
    lost = report.models_lost
    assert (lost.mean, lost.median, lost.p90) == (2, 2, 2)
    assert report.p_destroyed == 0.0


def test_the_seed_and_run_count_are_reported_and_reproduce_the_result() -> None:
    scenario = _scenario({"Regular": ["1-3: Kill 1 model", "4+: Dazed"]}, hits=3)
    first = simulate(scenario, runs=200, seed=42)
    assert (first.seed, first.runs) == (42, 200)
    assert simulate(scenario, runs=200, seed=42) == first


def test_a_seed_is_chosen_when_none_is_given() -> None:
    report = simulate(_scenario({"Regular": ["1+: Dazed"]}), runs=1, seed=None)
    assert isinstance(report.seed, int)


def test_rounds_until_continuing_damage_ends() -> None:
    bleed = PlaceToken(name="bleed", strength=4)
    scenario = _scenario(
        {"Regular": ["1+: Dazed"]}, hits=0, tokens=[bleed], max_rounds=2
    )
    report = simulate(scenario, runs=30, seed=3)
    assert set(report.rounds) <= {1, 2}
    assert sum(report.rounds.values()) == 30


def test_each_round_averages_over_every_run() -> None:
    # A Bleed here either stops at a 1 or kills a Model and is removed, so every
    # run ends in Round 1 having lost at most one Model.
    bleed = PlaceToken(name="bleed", strength=4)
    scenario = _scenario({"Regular": ["1+: Kill 1 model"]}, hits=0, tokens=[bleed])
    report = simulate(scenario, runs=40, seed=5)
    assert [summary.round for summary in report.per_round] == [0, 1]
    assert report.per_round[0].models == 4
    assert 3 < report.per_round[1].models < 4
    assert report.per_round[1].tokens == {}


def test_a_finished_run_is_carried_forward() -> None:
    bleed = PlaceToken(name="bleed", strength=4)
    scenario = _scenario(
        {"Regular": ["1+: Dazed"]}, hits=0, tokens=[bleed], max_rounds=6
    )
    report = simulate(scenario, runs=50, seed=2)
    dazed = [summary.tokens.get("dazed", 0.0) for summary in report.per_round]
    assert dazed == sorted(dazed)


def test_a_destroyed_unit_counts_as_no_models_alive() -> None:
    report = simulate(_scenario({"Regular": ["1+: Unit destroyed"]}), runs=5, seed=1)
    assert report.per_round[0].models == 0


def test_mean_token_counts_per_round() -> None:
    report = simulate(_scenario({"Regular": ["1+: Dazed"]}, hits=2), runs=5, seed=1)
    assert report.per_round[0].tokens == {"dazed": 2.0}


def test_the_entry_table_comes_first() -> None:
    tables: dict[DamageTableName, list[str]] = {
        "Psychic": ["1+: Wobble"],
        "Regular": ["1+: Rotate, d6 psychic damage"],
    }
    report = simulate(_scenario(tables), runs=4, seed=1, entry="Psychic")
    assert list(report.table_rolls) == ["Psychic", "Regular"]
    assert [(row.table, row.text, row.hits) for row in report.unparsed] == [
        ("Psychic", "Wobble", 4),
        ("Regular", "Rotate", 4),
    ]


def test_spillover_counts_add_up_over_runs() -> None:
    tables: dict[DamageTableName, list[str]] = {
        "Regular": ["1+: d4 damage to all transported units"]
    }
    report = simulate(_scenario(tables), runs=7, seed=1)
    assert report.spillover == {"d4 damage to all transported units": 7}
