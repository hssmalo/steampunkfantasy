"""Profile discovery and resolution for the Image Asset Service.

A **Profile** is a named pair of Workflows within an Environment — one to
generate, one to refine — identified by the filename stem under
`workflows/<env>/`. Discovered by scanning that directory, not declared in
config.

This module is pure filesystem: no HTTP, no config import at module scope.
Roots are passed as arguments so it is trivially testable with `tmp_path`.
"""

from pathlib import Path

REFINE_SUFFIX = "-refine"
_EXCLUDED_ENVS = frozenset({"examples"})


def available(workflows_root: Path, env: str) -> list[str]:
    """Return the Profile names under `workflows_root/env`, sorted.

    A Profile is the stem of a `*.json` file that does not end in
    `-refine`. Returns [] when the directory does not exist or is excluded.
    """
    if env in _EXCLUDED_ENVS:
        return []
    env_dir = workflows_root / env
    if not env_dir.is_dir():
        return []
    return sorted(
        p.stem for p in env_dir.glob("*.json") if not p.stem.endswith(REFINE_SUFFIX)
    )


def _relative_path(path: Path, project_root: Path) -> str:
    """Show `path` project-relative where possible, absolute otherwise."""
    try:
        return str(path.relative_to(project_root))
    except ValueError:
        return str(path)


def resolve(
    workflows_root: Path, env: str, profile: str, *, project_root: Path
) -> Path:
    """Return the generate Workflow path, raising ValueError if absent.

    Errors are loud and name the available Profiles when the directory exists.
    """
    env_dir = workflows_root / env
    if not env_dir.is_dir() or not any(env_dir.glob("*.json")):
        shown = _relative_path(env_dir, project_root)
        msg = (
            f"no workflows for env '{env}' "
            f"(expected {shown}/); "
            "copy one from workflows/examples/"
        )
        raise ValueError(msg)

    path = env_dir / f"{profile}.json"
    if path.is_file():
        return path

    names = available(workflows_root, env)
    msg = f"unknown profile '{profile}' for env '{env}'; available: {', '.join(names)}"
    raise ValueError(msg)


def resolve_refine(
    workflows_root: Path, env: str, profile: str, *, project_root: Path
) -> Path:
    """Return the refine Workflow path for an existing Profile.

    Raises ValueError when the refine Workflow file is missing.
    """
    path = workflows_root / env / f"{profile}{REFINE_SUFFIX}.json"
    if path.is_file():
        return path
    shown = _relative_path(path, project_root)
    msg = f"profile '{profile}' has no refine workflow (expected {shown})"
    raise ValueError(msg)
