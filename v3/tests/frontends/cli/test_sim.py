"""`spf sim damage` against a live Unit: the report's shape, never its numbers.

The Unit is picked at run time from whatever the committed Races hold, so no
rules edit can break these tests.
"""

from dataclasses import replace
from pathlib import Path
from typing import cast

import pytest
from rich.text import Text

from spf import races
from spf.console import stdout
from spf.frontends.cli import app, sim
from spf.frontends.cli.sim import (
    NO_POINTS,
    UNPARSED_STYLE,
    damage_table,
    expected_points_text,
    points_text,
    print_army_report,
    print_report,
    token_columns,
)
from spf.schemas.type_aliases import DamageTable, RaceName
from spf.sim.effects import Vocabulary
from spf.sim.report import DamageReport, RoundSummary, simulate
from spf.sim.scenario import Scenario
from spf.sim.tables import CompiledTable, compile_table
from tests.conftest import (
    InstallRegistry,
    synthetic_model,
    synthetic_race,
    synthetic_unit,
    write_army_json,
    write_race_toml,
)


@pytest.fixture(autouse=True)
def _wide_console(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(stdout, "width", 200)


def _live_unit() -> tuple[str, str]:
    """Any committed Unit with a Regular Damage table, as `race.unit`."""
    for race_name in races.list_races(validate=True):
        for key, unit in races.get_units(race_name).items():
            if "Regular" in unit.damage_tables:
                return f"{race_name}.{key}", unit.name
    pytest.skip("no committed Unit has a Regular Damage table")


def _sim(*args: str) -> None:
    app(["sim", "damage", *args], exit_on_error=False, result_action="return_value")


def test_damage_reports_a_live_unit(capsys: pytest.CaptureFixture[str]) -> None:
    unit, name = _live_unit()
    _sim(unit, "--start", "d6, bleed=4, future=1", "--runs", "50", "--seed", "7")
    out = capsys.readouterr().out
    assert name in out
    assert "seed 7" in out
    assert "50 runs" in out
    assert "P(Destroyed)" in out
    assert "Points" in out
    assert out.index("P(Destroyed)") < out.index("E(Points Destroyed)")


def test_attrition_reports_a_live_unit(capsys: pytest.CaptureFixture[str]) -> None:
    unit, name = _live_unit()
    _sim(unit, "--incoming", "d6-2", "--runs", "20", "--max-rounds", "3")
    assert name in capsys.readouterr().out


def test_an_unknown_unit_is_rejected_with_a_suggestion() -> None:
    unit, _ = _live_unit()
    with pytest.raises(ValueError, match="Did you mean"):
        _sim(f"{unit}x", "--start", "d6")


def test_a_bad_start_names_the_option() -> None:
    unit, _ = _live_unit()
    with pytest.raises(ValueError, match="--start"):
        _sim(unit, "--start", "bleed")


def test_damage_prints_the_units_tables_above_the_report(
    capsys: pytest.CaptureFixture[str],
) -> None:
    unit, _ = _live_unit()
    _sim(unit, "--start", "d6", "--runs", "5")
    out = capsys.readouterr().out
    assert "Regular damage table" in out
    assert out.index("Regular damage table") < out.index("P(Destroyed)")


def _sim_race(*args: str) -> None:
    app(
        ["sim", "damage-race", *args], exit_on_error=False, result_action="return_value"
    )


def test_damage_race_reports_one_line_per_unit(
    capsys: pytest.CaptureFixture[str],
) -> None:
    unit, _ = _live_unit()
    race_name = unit.partition(".")[0]
    names = [
        config.name
        for config in races.get_units(cast("RaceName", race_name)).values()
        if "Regular" in config.damage_tables
    ]
    _sim_race(race_name, "--start", "d6, bleed=4", "--runs", "3", "--seed", "7")
    out = capsys.readouterr().out
    assert "seed 7" in out
    header = next(line for line in out.splitlines() if "P(Destroyed)" in line)
    assert (
        header.index("Points")
        < header.index("P(Destroyed)")
        < header.index("E(Points Destroyed)")
    )
    for name in names:
        assert name in out


def test_damage_race_rejects_an_unknown_race() -> None:
    unit, _ = _live_unit()
    with pytest.raises(ValueError, match="Did you mean"):
        _sim_race(f"{unit.partition('.')[0]}x", "--start", "d6")


def _compiled(*rows: str, notes: list[str] | None = None) -> CompiledTable:
    table = DamageTable.model_validate({"rows": list(rows), "notes": notes or []})
    return compile_table("Regular", table, vocabulary=Vocabulary(tokens={}))


def _styles(text: Text) -> dict[str, str]:
    """Map each styled stretch of a cell to its style."""
    return {text.plain[span.start : span.end]: str(span.style) for span in text.spans}


def test_an_unparsed_stretch_is_colored() -> None:
    table = damage_table(_compiled("1: Kill 1 model, Wobble twice"))
    effect = cast("Text", next(iter(table.columns[1].cells)))
    assert effect.plain == "Kill 1 model, Wobble twice"
    assert _styles(effect) == {"Wobble twice": UNPARSED_STYLE}


def _round(**tokens: float) -> RoundSummary:
    return RoundSummary(round=0, models=1.0, future=0.0, future_crew=0.0, tokens=tokens)


def test_token_columns_order_strengths_by_size() -> None:
    per_round = [
        _round(**{"bleed[10]": 0.1, "shaken": 1.0}),
        _round(**{"bleed[4]": 0.5, "poison[6]": 0.2, "bleed[6]": 0.3}),
    ]
    assert token_columns(per_round) == [
        "bleed[4]",
        "bleed[6]",
        "bleed[10]",
        "poison[6]",
        "shaken",
    ]


def test_an_unparsed_note_is_colored() -> None:
    notes = ["Bleed does not cause more Bleed", "Count the models first"]
    table = damage_table(_compiled("1: Kill 1 model", notes=notes))
    caption = cast("Text", table.caption)
    assert "Bleed does not cause more Bleed" in caption.plain
    assert _styles(caption) == {"Count the models first": UNPARSED_STYLE}


def test_points_show_as_a_whole_number_and_zero_is_a_value() -> None:
    assert points_text(None) == NO_POINTS
    assert points_text(0) == "0"
    assert points_text(16) == "16"


def test_expected_points_show_two_decimals() -> None:
    assert expected_points_text(None) == NO_POINTS
    assert expected_points_text(0.0) == "0.00"
    assert expected_points_text(4.4875) == "4.49"


def _report(unit: str, *, points: int | None, p_destroyed: float) -> DamageReport:
    """Build a report with the Points and P(Destroyed) a test names."""
    scenario = Scenario(
        unit=unit,
        models=1,
        tables={"Regular": _compiled("1+: Dazed")},
    )
    report = simulate(scenario, runs=1, seed=1)
    return replace(report, points=points, p_destroyed=p_destroyed)


def _cells(out: str, label: str) -> list[str]:
    """Split the table row holding `label` into its stripped cells."""
    rows = [
        [cell.strip() for cell in line.split("│")[1:-1]] for line in out.splitlines()
    ]
    return next(row for row in rows if label in row)


def test_the_army_report_numbers_its_columns_first(
    capsys: pytest.CaptureFixture[str],
) -> None:
    report = _report("Squad", points=4, p_destroyed=0.5)
    print_army_report([report], title="Army", positions=[1])
    out = capsys.readouterr().out
    header = next(line for line in out.splitlines() if "P(Destroyed)" in line)
    assert (
        header.index("#")
        < header.index("Unit")
        < header.index("Points")
        < header.index("P(Destroyed)")
        < header.index("E(Points Destroyed)")
    )


def test_the_army_report_keeps_each_units_position(
    capsys: pytest.CaptureFixture[str],
) -> None:
    reports = [
        _report("Red Squad", points=4, p_destroyed=0.5),
        _report("Blue Squad", points=4, p_destroyed=0.5),
    ]
    print_army_report(reports, title="Army", positions=[1, 3])
    out = capsys.readouterr().out
    assert _cells(out, "Red Squad")[:2] == ["1", "Red Squad"]
    assert _cells(out, "Blue Squad")[:2] == ["3", "Blue Squad"]


def test_the_army_total_sums_the_costed_units(
    capsys: pytest.CaptureFixture[str],
) -> None:
    reports = [
        _report("Red Squad", points=4, p_destroyed=0.5),
        _report("Mob", points=None, p_destroyed=1.0),
        _report("Blue Squad", points=8, p_destroyed=0.25),
    ]
    print_army_report(reports, title="Army", positions=[1, 2, 3])
    total = _cells(capsys.readouterr().out, "Total")
    assert total[:5] == ["", "Total", "12", "", "4.00"]
    assert set(total[5:]) == {""}


def test_an_army_with_no_costed_unit_has_no_total(
    capsys: pytest.CaptureFixture[str],
) -> None:
    reports = [_report("Mob", points=None, p_destroyed=1.0)]
    print_army_report(reports, title="Army", positions=[1])
    total = _cells(capsys.readouterr().out, "Total")
    assert total[2] == NO_POINTS
    assert total[4] == NO_POINTS


def _army_unit(name: str, *, nick: str | None = None) -> dict[str, object]:
    return {"name": name, "nick": nick, "models": [{"name": "soldier", "upgrades": []}]}


@pytest.fixture
def army_on_disk(
    races_dir: Path, armies_dir: Path, install_registry: InstallRegistry
) -> str:
    """Write a Race and an Army of it: a nicked squad, a beast, another squad.

    Only the squads have a Regular Damage table.
    """
    install_registry()
    race = synthetic_race(
        units={
            "squad": synthetic_unit(),
            "beast": synthetic_unit(
                name="Beast", damage_tables={"Crew": {"rows": ["1+: Fine"]}}
            ),
        },
        models={"soldier": synthetic_model(equipment=[])},
        equipment={},
    )
    write_race_toml(races_dir, race)
    (armies_dir / "cup").mkdir()
    army = {
        "race": next(iter(race.races)),
        "nick": "Reds",
        "units": [
            _army_unit("squad", nick="Red Squad"),
            _army_unit("beast"),
            _army_unit("squad"),
        ],
    }
    write_army_json(armies_dir / "cup", "reds", army)
    return "cup/reds"


def _sim_army(*args: str) -> None:
    app(
        ["sim", "damage-army", *args], exit_on_error=False, result_action="return_value"
    )


def test_damage_army_names_the_army_and_how_it_ran(
    capsys: pytest.CaptureFixture[str], army_on_disk: str
) -> None:
    _sim_army(army_on_disk, "--start", "d6", "--runs", "50", "--seed", "7")
    heading = capsys.readouterr().out.splitlines()[0]
    assert "Reds (Goblin)" in heading
    assert "50 runs per Unit" in heading
    assert "seed 7" in heading


def test_damage_army_numbers_its_units_and_skips_by_table(
    capsys: pytest.CaptureFixture[str], army_on_disk: str
) -> None:
    _sim_army(army_on_disk, "--start", "d6", "--runs", "5", "--seed", "7")
    out = capsys.readouterr().out
    assert _cells(out, "Red Squad")[:2] == ["1", "Red Squad"]
    assert _cells(out, "Squad")[:2] == ["3", "Squad"]
    assert "skipped: Beast" in out


def _spy_on_healing(monkeypatch: pytest.MonkeyPatch, builder: str) -> list[bool]:
    """Record, per Scenario `builder` builds, whether it was allowed to heal."""
    could_heal: list[bool] = []
    build = getattr(sim, builder)

    def spy(*args: object, **kwargs: object) -> Scenario:
        scenario = build(*args, **kwargs)
        could_heal.append(bool(scenario.healers) or kwargs.get("healing") is not False)
        return scenario

    monkeypatch.setattr(sim, builder, spy)
    return could_heal


@pytest.mark.parametrize(
    ("command", "builder"),
    [("damage", "unit_scenario"), ("damage-race", "unit_scenario")],
)
def test_no_healing_builds_scenarios_without_healers(
    monkeypatch: pytest.MonkeyPatch, command: str, builder: str
) -> None:
    could_heal = _spy_on_healing(monkeypatch, builder)
    unit, _ = _live_unit()
    target = unit if command == "damage" else unit.partition(".")[0]
    app(
        ["sim", command, target, "--start", "d6", "--runs", "1", "--no-healing"],
        exit_on_error=False,
        result_action="return_value",
    )
    assert could_heal
    assert not any(could_heal)


def test_damage_army_takes_no_healing_too(
    monkeypatch: pytest.MonkeyPatch, army_on_disk: str
) -> None:
    could_heal = _spy_on_healing(monkeypatch, "scenario_of")
    _sim_army(army_on_disk, "--start", "d6", "--runs", "1", "--no-healing")
    assert could_heal
    assert not any(could_heal)


def test_damage_army_rejects_an_unknown_army(
    capsys: pytest.CaptureFixture[str], army_on_disk: str
) -> None:
    with pytest.raises(SystemExit):
        _sim_army(f"{army_on_disk}x", "--start", "d6")
    assert "Error" in capsys.readouterr().err


def test_the_report_counts_each_healing_action(
    capsys: pytest.CaptureFixture[str],
) -> None:
    report = replace(
        _report("Squad", points=4, p_destroyed=0.5),
        healing={"Extinguish one Fire": 7},
    )
    print_report(report)
    out = capsys.readouterr().out
    assert "Healing and repair" in out
    assert _cells(out, "Extinguish one Fire") == ["Extinguish one Fire", "7"]


def test_unplayed_healing_is_listed_as_not_simulated(
    capsys: pytest.CaptureFixture[str],
) -> None:
    report = replace(
        _report("Squad", points=4, p_destroyed=0.5),
        unparsed=[],
        unplayed_healing=["Repair[one per alive drone, self, 2nd Healing]"],
    )
    print_report(report)
    out = capsys.readouterr().out
    assert "Not simulated" in out
    row = _cells(out, "Repair[one per alive drone, self, 2nd Healing]")
    assert row == ["Repair", "—", "Repair[one per alive drone, self, 2nd Healing]", "—"]
