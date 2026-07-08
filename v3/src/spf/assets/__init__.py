"""The shared Asset generation subsystem for SteamPunkFantasy.

Turns a source object into curated, committed Assets in three steps: **generate**
Candidates under ``candidates/``, a human reviews them, then **promote** exactly
one into the committed store under ``assets/``. Behavior is driven by data
records (:class:`Kind`, :class:`Service`) rather than per-kind code. The seams are
:func:`generate` and :func:`promote`; concrete kinds plug in via
:func:`register_kind`.
"""

from spf.assets.kinds import Kind, Service, get_kind, register_kind
from spf.assets.spine import generate, promote

__all__ = [
    "Kind",
    "Service",
    "generate",
    "get_kind",
    "promote",
    "register_kind",
]
