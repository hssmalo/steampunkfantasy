"""The shared Asset generation subsystem for SteamPunkFantasy.

Turns a source object into curated, committed Assets in three steps: **generate**
Candidates under `candidates/`, a human reviews them, then **promote** exactly
one into the committed store under `assets/`. Behavior is driven by data
records (`Kind`, `Service`) rather than per-kind code. The seams are
`generate` and `promote`; concrete kinds plug in via
`register_kind`.
"""

from spf.assets.kinds import (
    Kind,
    Refiner,
    Service,
    TargetLevel,
    get_kind,
    register_kind,
)
from spf.assets.spine import (
    generate,
    promote,
    refine,
    stage_promoted,
    validate_lineage,
)
from spf.assets.survey import Coverage, Survey, survey
from spf.assets.targets import Target, targets

__all__ = [
    "Coverage",
    "Kind",
    "Refiner",
    "Service",
    "Survey",
    "Target",
    "TargetLevel",
    "generate",
    "get_kind",
    "promote",
    "refine",
    "register_kind",
    "stage_promoted",
    "survey",
    "targets",
    "validate_lineage",
]
