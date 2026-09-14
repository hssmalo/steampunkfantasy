"""Tests for the Gallery product: `build_gallery()` and its Rendering.

The Gallery is built from a Survey, so these tests hand it one of their own
rather than reading the committed Asset store: what is on disk is `survey`'s
subject, not this Product's.
"""

import re
from pathlib import Path

from spf.assets.image import IMAGE
from spf.assets.kinds import TargetLevel
from spf.assets.survey import Coverage, Survey
from spf.assets.targets import Target, targets
from spf.frontends.cli.render import GALLERY, RACE_OVERVIEW
from spf.races import get_race
from spf.render import render
from spf.render.formats import get_format
from spf.render.gallery import Gallery, build_gallery
from spf.render.race_overview import build_overview, in_cost_order
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


# --- The Renderings ---------------------------------------------------------
#
# The templates stay dumb (ADR 0005); these pin the contract they have to keep
# — one picture per entry, and every caption landing on an anchor the Race
# Overview really emits — without asserting on a line of their prose.

_IMAGE = re.compile(r"!\[[^\]]*\]\(([^)]+)\)")
_CROSS_LINK = re.compile(r"\]\((?:\.\./)?race-overview/[^)#]+#([^)]+)\)")
_OVERVIEW_ANCHOR = re.compile(r'<a id="([^"]+)"></a>')
_INCLUDE = re.compile(r"\\includegraphics\[[^\]]*\]\{([^}]+)\}")


def _full_gallery(race_name: str) -> Gallery:
    """Build a committed Race's Gallery, with art for every Target it declares."""
    race_config = get_race(race_name)  # ty: ignore[invalid-argument-type]
    found = Survey(
        rows=[
            Coverage(target=target, asset=_art(target.name))
            for target in targets(IMAGE, race_name)  # ty: ignore[invalid-argument-type]
        ],
        orphans=[],
    )
    return build_gallery(race_config, stem=race_name, survey_for=lambda _: found)


def _rendered(gallery: Gallery, fmt: str, tmp_path: Path) -> str:
    """Render `gallery` through one Format and read the document back."""
    out = render(
        GALLERY, gallery, fmt=get_format(fmt), name=gallery.stem, output_root=tmp_path
    )
    return out.read_text(encoding="utf-8")


def test_the_markdown_document_shows_every_entry(tmp_path: Path) -> None:
    """A Gallery that skipped a picture would be hiding art the Race has."""
    gallery = _full_gallery(RACE)

    images = _IMAGE.findall(_rendered(gallery, "markdown", tmp_path))

    assert len(images) == len(gallery.entries)


def test_every_caption_lands_on_a_race_overview_anchor(tmp_path: Path) -> None:
    """The rules are one link away only if the link has something to land on."""
    gallery = _full_gallery(RACE)
    overview = build_overview(
        get_race(RACE),
        stem=RACE,
        image_for=lambda _race, _name: None,
    )
    out = render(
        RACE_OVERVIEW,
        overview,
        fmt=get_format("markdown"),
        name=RACE,
        output_root=tmp_path,
    )

    linked = _CROSS_LINK.findall(_rendered(gallery, "markdown", tmp_path))

    assert linked
    anchors = _OVERVIEW_ANCHOR.findall(out.read_text(encoding="utf-8"))
    assert set(linked) <= set(anchors)


def test_the_latex_document_embeds_every_entry(tmp_path: Path) -> None:
    """Both families show the same art; only the spelling is the family's own."""
    gallery = _full_gallery(RACE)

    latex = _rendered(gallery, "latex", tmp_path)

    assert len(_INCLUDE.findall(latex)) == len(gallery.entries)
    # A printed sheet cannot be clicked, so the captions carry no links.
    assert "hyperref" not in latex


def test_an_empty_gallery_still_renders(tmp_path: Path) -> None:
    """An artless Race yields a page with nothing on it, not a failed build."""
    gallery = build_gallery(
        synthetic_race(race=RACE), stem=RACE, survey_for=lambda _: _survey()
    )

    assert _rendered(gallery, "markdown", tmp_path)
    assert _rendered(gallery, "latex", tmp_path)
