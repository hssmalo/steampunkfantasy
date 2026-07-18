"""Tests for config. Do not test for specific config values."""

from pathlib import Path

import pytest
from pydantic import ValidationError

from spf.config import config
from spf.schemas.config import ComfyUIConfig, ComfyUIEnvConfig, ImageAssetConfig


def test_paths_resolve() -> None:
    assert isinstance(config.paths.candidates, Path)
    assert isinstance(config.paths.assets, Path)
    assert isinstance(config.paths.prompts, Path)
    assert isinstance(config.paths.workflows, Path)


def test_image_prompt_paths_resolve() -> None:
    # Both prompt files are configured paths, not hardcoded basenames, and
    # interpolate under `paths.prompts` the way the Workflows do under
    # `paths.workflows` (ADR 0009's fifth amendment).
    image = config.assets.image
    assert image.prompt.parent == config.paths.prompts
    assert image.negative_prompt.parent == config.paths.prompts


def test_image_asset_requires_both_prompt_paths() -> None:
    # Neither key has a default: a missing one fails at load, not at generate.
    with pytest.raises(ValidationError, match="negative_prompt"):
        ImageAssetConfig(  # pyright: ignore[reportCallIssue]  the omission is the point
            count=3, prompt=Path("image.txt"), comfyui=config.assets.image.comfyui
        )


def _env(**kw: str) -> ComfyUIEnvConfig:
    base = {
        "base_url": "http://x",
        "workflow": Path("w.json"),
        "refine_workflow": Path("w-refine.json"),
    }
    return ComfyUIEnvConfig(**{**base, **kw})


def test_comfyui_env_requires_a_refine_workflow() -> None:
    # Every Environment names its refine Workflow; the file it points at need
    # not exist until a Refinement is actually run.
    with pytest.raises(ValidationError, match="refine_workflow"):
        ComfyUIEnvConfig(base_url="http://x", workflow=Path("w.json"))  # pyright: ignore[reportCallIssue]  the omission is the point


def test_comfyui_env_carries_both_workflows() -> None:
    env = _env()
    assert env.workflow == Path("w.json")
    assert env.refine_workflow == Path("w-refine.json")


def test_comfyui_selected_returns_named_block() -> None:
    comfyui = ComfyUIConfig(
        env="cloud",
        local=_env(base_url="http://local"),
        cloud=_env(base_url="http://cloud"),
    )
    assert comfyui.selected().base_url == "http://cloud"


def test_comfyui_selected_rejects_unknown_env() -> None:
    comfyui = ComfyUIConfig(env="staging", local=_env(), cloud=_env())
    with pytest.raises(ValueError, match=r"local.*cloud"):
        comfyui.selected()
