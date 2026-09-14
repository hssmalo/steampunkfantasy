"""Gallery view-model: one Race's Image Assets, art and names only.

The rules live in the Race Overview; this Product shows what a Race *looks*
like, with every entry one link away from the record it depicts (ADR 0031's
anchors). It is driven by the Race's Targets rather than by the Asset store's
directory listing, so a file matching no Target never appears here — that is
the Survey's job to report (ADR 0011), and a second coverage surface is what
this avoids.

Its one touch of disk is the `SurveyFor` from `spf.render.images`, injected the
way the `ImageLookup` is, so a test can build a Gallery without a filesystem.

Each entry carries the `Path` of the committed Asset, not a spelled URL: ADR
0017 leaves the spelling to the family, and the Gallery gives it a third
spelling. The Markdown family runs it through `image_src` — a published `/art/`
URL on the Site, a relative path in a local rendering — while the LaTeX family
embeds the full-size original by absolute path, as the Army Reference does.
"""

from dataclasses import dataclass
from pathlib import Path

from spf.assets.kinds import TargetLevel
from spf.render.images import SurveyFor, committed_survey
from spf.render.race_overview import MODEL, UNIT, anchor, in_cost_order
from spf.schemas import type_aliases as t
from spf.schemas.race import RaceConfig

_RECORD_SECTIONS: dict[TargetLevel, str] = {"unit": UNIT, "model": MODEL}
"""The Race Overview section each Target level is addressed under.

The `race` level is absent on purpose: a Race's own art depicts no record, so
there is no entry for its caption to link to.
"""


@dataclass(frozen=True)
class GalleryEntry:
    """One piece of a Race's art: what it depicts, and where its rules are."""

    name: str
    image: Path
    anchor: str | None
    """The Race Overview anchor of the record depicted, `None` for the Race."""


@dataclass(frozen=True)
class Gallery:
    """A Race's whole art sheet, in the order its Race Overview reads."""

    stem: str
    race: t.RaceName
    title: str
    entries: list[GalleryEntry]


def _positions(race_config: RaceConfig) -> dict[tuple[TargetLevel, str], int]:
    """Index every Target the catalogue could cover by where it prints.

    The Race Overview's own order — its title block, then Units and Models in
    Cost order — so the two pages list the same Race the same way.
    """
    race = next(iter(race_config.races))
    ordered: list[tuple[TargetLevel, str]] = [
        ("race", race),
        *(("unit", key) for key, _ in in_cost_order(race_config.units)),
        *(("model", key) for key, _ in in_cost_order(race_config.models)),
    ]
    return {key: index for index, key in enumerate(ordered)}


def build_gallery(
    race_config: RaceConfig,
    *,
    stem: str,
    survey_for: SurveyFor = committed_survey,
) -> Gallery:
    """Build a `Gallery` from a Race's catalogue and a Survey of its art.

    Only the Asset half of each `Coverage` is read: how many Candidates are
    waiting is authoring progress, and no business of a published page. A
    Target the Survey knows and the catalogue does not sorts last rather than
    vanishing, so nothing goes missing silently.
    """
    race, metadata = next(iter(race_config.races.items()))
    positions = _positions(race_config)
    rows = sorted(
        survey_for(race).rows,
        key=lambda row: positions.get(
            (row.target.level, row.target.name), len(positions)
        ),
    )
    entries = [
        GalleryEntry(
            name=row.target.human_name,
            image=row.asset,
            anchor=(
                anchor(section, row.target.name)
                if (section := _RECORD_SECTIONS.get(row.target.level)) is not None
                else None
            ),
        )
        for row in rows
        if row.asset is not None
    ]
    return Gallery(stem=stem, race=race, title=metadata.name, entries=entries)
