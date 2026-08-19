"""The Image Asset kind: AI-generated race/unit art via ComfyUI.

Registers the `image` `Kind`, laid out at
`<race>/images/<name>.png`, backed by
`ComfyUIService`. This module is pure wiring: it
builds the service from the resolved ComfyUI **Environment** and **Profile** —
plus the configured Negative Prompt file, which is shared rather than
per-Environment — and registers the Kind. The provider — one stdlib client
across local ComfyUI and Comfy Cloud — lives in `spf.assets.comfyui`
(see ADR 0009).

Nothing scans the filesystem or validates config at import: `_build_service`
is the factory, called at generate/refine time, not at module load.
"""

import operator
from pathlib import Path

from spf.assets.comfyui import ComfyUIService
from spf.assets.kinds import Kind, register_kind
from spf.assets.profiles import REFINE_SUFFIX
from spf.assets.profiles import resolve as resolve_profile
from spf.assets.profiles import resolve_refine as resolve_refine_profile
from spf.config import config


def _build_service(
    *, env: str | None = None, profile: str | None = None
) -> ComfyUIService:
    """Build the Image `ComfyUIService` from the resolved env and profile.

    Resolution order per axis: config -> env var -> flag, last wins.
    Reads neither the network nor the Workflow file; a missing or invalid
    env/profile raises here (a config typo, worth failing loudly at invoke).

    Only the generate Workflow path is resolved; the refine Workflow is
    resolved lazily when a Refinement is actually run, so generating does
    not require a refine Workflow to exist.
    """
    comfyui = config.assets.image.comfyui
    env_name = env if env is not None else comfyui.env
    env_block = comfyui.selected(env_name)

    profile_name = profile or comfyui.profile or env_block.profile

    workflow_path = resolve_profile(
        config.paths.workflows,
        env_name,
        profile_name,
        project_root=config.paths.project,
    )
    refine_workflow_path = _lazy_refine_path(
        config.paths.workflows, env_name, profile_name
    )

    return ComfyUIService(
        base_url=env_block.base_url,
        workflow_path=workflow_path,
        refine_workflow_path=refine_workflow_path,
        negative_path=config.assets.image.negative_prompt,
        api_key_env=env_block.api_key_env,
        timeout_s=comfyui.timeout_s,
    )


def _lazy_refine_path(workflows_root: Path, env: str, profile: str) -> Path:
    """Return the refine Workflow path, without checking that it exists.

    A missing refine file is fine until a Refinement is actually run, so a
    contributor with only a generate Workflow locally can still generate.
    """
    return workflows_root / env / f"{profile}{REFINE_SUFFIX}.json"


def _resolve_refine(*, env: str | None = None, profile: str | None = None) -> Path:
    """Resolve and validate the refine Workflow path for a Refinement.

    Called only from the refine CLI path, where a missing refine file is
    a hard error.
    """
    comfyui = config.assets.image.comfyui
    env_name = env if env is not None else comfyui.env
    env_block = comfyui.selected(env_name)
    profile_name = profile or comfyui.profile or env_block.profile

    return resolve_refine_profile(
        config.paths.workflows,
        env_name,
        profile_name,
        project_root=config.paths.project,
    )


IMAGE = register_kind(
    Kind(
        name="image",
        service_factory=_build_service,
        subdir="images",
        extension="png",
        targets=frozenset({"race", "unit"}),
        brief=operator.attrgetter("description"),
    )
)
