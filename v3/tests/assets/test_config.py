"""S4: the assets layout paths and per-kind counts resolve from config."""

from pathlib import Path

import pytest

from spf.config import config
from spf.schemas.config import ComfyUIConfig, ComfyUIEnvConfig


def test_candidates_and_assets_paths_resolve() -> None:
    assert isinstance(config.paths.candidates, Path)
    assert config.paths.candidates.name == "candidates"
    assert isinstance(config.paths.assets, Path)
    assert config.paths.assets.name == "assets"


def test_prompts_path_resolves() -> None:
    assert isinstance(config.paths.prompts, Path)
    assert config.paths.prompts.name == "prompts"


def test_per_kind_counts_resolve() -> None:
    assert config.assets.lore.count == 1
    assert config.assets.image.count == 3
    assert config.assets.model.count == 2


def test_workflows_path_resolves() -> None:
    assert isinstance(config.paths.workflows, Path)
    assert config.paths.workflows.name == "workflows"


def test_comfyui_env_defaults_to_local() -> None:
    comfyui = config.assets.image.comfyui
    assert comfyui.env == "local"
    assert comfyui.selected() is comfyui.local
    assert comfyui.local.base_url == "http://127.0.0.1:8188"
    assert comfyui.cloud.api_key_env == "SPF_COMFYUI_API_KEY"


def _env(**kw: str) -> ComfyUIEnvConfig:
    base = {"base_url": "http://x", "workflow": "w.json"}
    return ComfyUIEnvConfig(**{**base, **kw})


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
