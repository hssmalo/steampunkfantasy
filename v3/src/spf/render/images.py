"""The seam between a Rendering and the committed Image Asset store.

One place asks "what art is committed for this Target?" (ADR 0017), neutral
between Products so that no Product has to import another to find out. A
Product takes an `ImageLookup` as an argument, defaulting to `committed_image`;
`--no-images` swaps in `no_image`, and a test swaps in its own fake and needs
no filesystem at all.

A Product that embeds one Target's art asks through `ImageLookup`. One that
shows a whole Race's asks through `SurveyFor` instead, because the question is
the Survey's: which of this Race's Targets have art, driven by what should
exist rather than by what is on disk (ADR 0011).
"""

from collections.abc import Callable
from pathlib import Path

from spf.assets.image import IMAGE
from spf.assets.spine import asset_for
from spf.assets.survey import Survey, survey
from spf.schemas import type_aliases as t

type ImageLookup = Callable[[t.RaceName, str], Path | None]
"""Answers "what art is committed for this Target?" — see `committed_image`."""

type SurveyFor = Callable[[t.RaceName], Survey]
"""Answers "which of this Race's Targets have art?" — see `committed_survey`."""


def committed_image(race: t.RaceName, name: str) -> Path | None:
    """Return the committed Image Asset for `name`, or `None` when there is none."""
    return asset_for(IMAGE, race, name=name)


def no_image(race: t.RaceName, name: str) -> None:
    """Lookup that finds nothing — what `--no-images` passes."""


def committed_survey(race: t.RaceName) -> Survey:
    """Survey the committed store for every Image Target `race` declares."""
    return survey(IMAGE, race)


def no_survey(_race: t.RaceName) -> Survey:
    """Survey that finds nothing — what `--no-images` passes."""
    return Survey(rows=[], orphans=[])
