"""Tests for config. Do not test for specific config values."""

from pathlib import Path

import pytest

from spf.config import config
from spf.schemas.config import ComfyUIConfig, ComfyUIEnvConfig


def test_paths_resolve() -> None:
    assert isinstance(config.paths.candidates, Path)
    assert isinstance(config.paths.assets, Path)
    assert isinstance(config.paths.prompts, Path)
    assert isinstance(config.paths.workflows, Path)


def _env(**kw: str) -> ComfyUIEnvConfig:
    base = {"base_url": "http://x", "workflow": Path("w.json")}
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
