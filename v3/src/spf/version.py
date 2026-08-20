"""The `spf` version, read from installed package metadata.

`pyproject.toml`'s `[project].version` is the single source of truth — it is
what `bumpver` rewrites when `just release` cuts a release — so no constant is
maintained here alongside it.
"""

from importlib.metadata import PackageNotFoundError, version

UNKNOWN_VERSION = "unknown"  # Stand-in when `spf` is not installed


def spf_version() -> str:
    """Return the version of the installed `spf` distribution."""
    try:
        return version("spf")
    except PackageNotFoundError:
        return UNKNOWN_VERSION
