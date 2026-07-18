"""The shared Asset generation subsystem for SteamPunkFantasy.

Turns a source object into curated, committed Assets in three steps: **generate**
Candidates under `candidates/`, a human reviews them, then **promote** exactly
one into the committed store under `assets/`. Behavior is driven by data
records (`Kind`, `Service`) rather than per-kind code. The seams are
`generate` and `promote`; concrete kinds plug in via
`register_kind`.
"""

from spf.assets.kinds import Kind, Refiner, Service, get_kind, register_kind
from spf.assets.spine import generate, promote, refine, validate_lineage

__all__ = [
    "Kind",
    "Refiner",
    "Service",
    "generate",
    "get_kind",
    "promote",
    "refine",
    "register_kind",
    "validate_lineage",
]
