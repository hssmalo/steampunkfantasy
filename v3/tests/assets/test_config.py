"""Tests for config. Do not test for specific config values."""

from pathlib import Path

import configaroo
import pytest
from pydantic import ValidationError

from spf.config import config
from spf.schemas.config import (
    ComfyUIConfig,
    ComfyUIEnvConfig,
    ImageAssetConfig,
    SteamPunkFantasyConfig,
)


def test_paths_resolve() -> None:
    assert isinstance(config.paths.candidates, Path)
    assert isinstance(config.paths.assets, Path)
    assert isinstance(config.paths.prompts, Path)
    assert isinstance(config.paths.workflows, Path)


def test_image_prompt_paths_resolve() -> None:
    image = config.assets.image
    assert image.prompt.parent == config.paths.prompts
    assert image.negative_prompt.parent == config.paths.prompts


def test_image_asset_requires_both_prompt_paths() -> None:
    with pytest.raises(ValidationError, match="negative_prompt"):
        ImageAssetConfig(  # pyright: ignore[reportCallIssue]  the omission is the point
            count=3, prompt=Path("image.txt"), comfyui=config.assets.image.comfyui
        )


def _env(**kw: str) -> ComfyUIEnvConfig:
    base = {
        "base_url": "http://x",
        "profile": "qwen",
    }
    return ComfyUIEnvConfig(**{**base, **kw})


def test_comfyui_env_requires_a_profile() -> None:
    with pytest.raises(ValidationError, match="profile"):
        ComfyUIEnvConfig(base_url="http://x")  # pyright: ignore[reportCallIssue]  the omission is the point


def test_comfyui_env_carries_profile() -> None:
    env = _env()
    assert env.profile == "qwen"


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


def test_comfyui_profile_defaults_empty() -> None:
    comfyui = ComfyUIConfig(local=_env(), cloud=_env())
    assert comfyui.profile == ""


def test_comfyui_profile_round_trips_through_env_var(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("SPF_COMFYUI_PROFILE", "krea2")
    config_path = configaroo.find_pyproject_toml() / "configs" / "spf.toml"
    cfg = (
        configaroo.Configuration.from_file(config_path)
        .add_envs(
            {
                "COMFYUI_ENV": "assets.image.comfyui.env",
                "COMFYUI_PROFILE": "assets.image.comfyui.profile",
            },
            prefix="SPF_",
        )
        .parse_dynamic()
        .convert_model(SteamPunkFantasyConfig)
    )
    assert cfg.assets.image.comfyui.profile == "krea2"
