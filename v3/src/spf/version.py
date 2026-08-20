"""The `spf` version, read from installed package metadata.

`pyproject.toml`'s `[project].version` is the single source of truth — it is
what `bumpver` rewrites when `just release` cuts a release — so no constant is
maintained here alongside it.
"""

from importlib.metadata import version


def spf_version() -> str:
    """Return the version of the installed `spf` distribution."""
    return version("spf")
