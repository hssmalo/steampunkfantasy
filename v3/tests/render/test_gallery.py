"""Tests for the Gallery product: `build_gallery()` and its Rendering.

The Gallery is built from a Survey, so these tests hand it one of their own
rather than reading the committed Asset store: what is on disk is `survey`'s
subject, not this Product's.
"""

from pathlib import Path

from spf.assets.kinds import TargetLevel
from spf.assets.survey import Coverage, Survey
from spf.assets.targets import Target
from spf.render.gallery import build_gallery
from spf.render.race_overview import in_cost_order
from spf.schemas.type_aliases import Cost
from tests.conftest import synthetic_race, synthetic_unit

RACE = "goblin"


def _target(name: str, *, human_name: str, level: TargetLevel = "unit") -> Target:
    """One thing the Image Kind could have an Asset for."""
    return Target(name=name, human_name=human_name, brief="", level=level)


def _survey(*rows: tuple[str, str, TargetLevel, Path | None]) -> Survey:
    """Build a Survey of the given Targets, each with or without an Asset."""
    return Survey(
        rows=[
            Coverage(target=_target(name, human_name=human, level=level), asset=asset)
            for name, human, level, asset in rows
        ],
        orphans=[],
    )


def _art(name: str) -> Path:
    """Point at a committed Image Asset that no test needs to exist on disk."""
    return Path(f"/assets/{RACE}/images/{name}.png")


def test_one_entry_per_target_that_has_art() -> None:
    """The Gallery shows the Race's Targets, named as a reader sees them."""
    race = synthetic_race(race=RACE)
    found = _survey(
        (RACE, "Goblin", "race", _art(RACE)),
        ("squad", "Squad", "unit", _art("squad")),
        ("mob", "Mob", "unit", _art("mob")),
    )

    gallery = build_gallery(race, stem=RACE, survey_for=lambda _: found)

    assert gallery.race == RACE
    assert gallery.title == "Goblin"
    assert gallery.stem == RACE
    assert [entry.name for entry in gallery.entries] == ["Goblin", "Squad", "Mob"]
    assert [entry.image for entry in gallery.entries] == [
        _art(RACE),
        _art("squad"),
        _art("mob"),
    ]


def test_a_target_with_no_asset_does_not_appear() -> None:
    """A Target nobody has generated art for has nothing to show."""
    race = synthetic_race(race=RACE)
    found = _survey(
        (RACE, "Goblin", "race", None),
        ("squad", "Squad", "unit", _art("squad")),
        ("mob", "Mob", "unit", None),
    )

    gallery = build_gallery(race, stem=RACE, survey_for=lambda _: found)

    assert [entry.name for entry in gallery.entries] == ["Squad"]


def test_a_race_with_no_art_yields_an_empty_gallery() -> None:
    """Rendered unconditionally: an artless Race is an empty page, not an error."""
    race = synthetic_race(race=RACE)
    found = _survey((RACE, "Goblin", "race", None), ("squad", "Squad", "unit", None))

    gallery = build_gallery(race, stem=RACE, survey_for=lambda _: found)

    assert gallery.entries == []
    assert gallery.title == "Goblin"


def test_a_unit_entry_links_its_race_overview_anchor() -> None:
    """The rules are one link away, at the anchor the Race Overview already has."""
    race = synthetic_race(race=RACE)
    found = _survey(("squad", "Squad", "unit", _art("squad")))

    gallery = build_gallery(race, stem=RACE, survey_for=lambda _: found)

    assert [entry.anchor for entry in gallery.entries] == ["unit-squad"]


def test_the_race_entry_has_no_anchor() -> None:
    """The Race's own art depicts no record, so there is no entry to link to."""
    race = synthetic_race(race=RACE)
    found = _survey((RACE, "Goblin", "race", _art(RACE)))

    gallery = build_gallery(race, stem=RACE, survey_for=lambda _: found)

    assert [entry.anchor for entry in gallery.entries] == [None]


def test_units_follow_the_race_overview_order() -> None:
    """The two pages read alike: the Race Overview's Cost order, not the Survey's."""
    race = synthetic_race(
        race=RACE,
        units={
            "cheap": synthetic_unit(race=RACE, name="Cheap", cost=Cost(mp=1)),
            "dear": synthetic_unit(race=RACE, name="Dear", cost=Cost(mp=9)),
        },
    )
    # The Survey lists Units in TOML order; the Gallery re-orders them.
    found = _survey(
        ("cheap", "Cheap", "unit", _art("cheap")),
        ("dear", "Dear", "unit", _art("dear")),
    )

    gallery = build_gallery(race, stem=RACE, survey_for=lambda _: found)

    # Whatever `Cost` order is, both pages take it from the same place.
    expected = [unit.name for _, unit in in_cost_order(race.units)]
    assert [entry.name for entry in gallery.entries] == expected


def test_the_race_is_asked_about_by_name() -> None:
    """The Survey is taken for the Race the catalogue holds."""
    asked: list[str] = []

    def survey_for(race: str) -> Survey:
        asked.append(race)
        return _survey()

    build_gallery(synthetic_race(race=RACE), stem=RACE, survey_for=survey_for)

    assert asked == [RACE]
