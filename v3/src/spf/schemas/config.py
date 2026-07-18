"""Schema for configuration of SteamPunkFantasy."""

from pathlib import Path

from spf.schemas import StrictModel


class PathsConfig(StrictModel):
    project: Path
    armies: Path
    races: Path
    rules: Path
    templates: Path
    prompts: Path
    output: Path
    candidates: Path
    assets: Path
    workflows: Path


class LatexConfig(StrictModel):
    engine: str = "pdflatex"


class RenderConfig(StrictModel):
    latex: LatexConfig = LatexConfig()


class AssetKindConfig(StrictModel):
    """Per-kind Asset settings (how many Candidates to generate, ...)."""

    count: int


class ComfyUIEnvConfig(StrictModel):
    """A single ComfyUI Environment: where to reach it and what to run."""

    base_url: str
    workflow: Path
    refine_workflow: Path
    api_key_env: str = ""


class ComfyUIConfig(StrictModel):
    """The ComfyUI provider config: the two Environments and the selector."""

    env: str = "local"
    timeout_s: int = 900
    local: ComfyUIEnvConfig
    cloud: ComfyUIEnvConfig

    def selected(self) -> ComfyUIEnvConfig:
        """Return the Environment block named by `env`.

        Raises `ValueError` naming the two valid Environments when
        `env` is neither (mirrors `spf.assets.get_kind`).
        """
        if self.env == "local":
            return self.local
        if self.env == "cloud":
            return self.cloud
        msg = f"Unknown ComfyUI env {self.env!r}; known envs: local, cloud"
        raise ValueError(msg)


class ImageAssetConfig(StrictModel):
    """Image asset settings: count, the two prompt files, and the provider.

    Both prompt files are configured paths rather than hardcoded basenames,
    following `ComfyUIEnvConfig`'s Workflow keys. They sit here and not in an
    Environment block because one pair serves both Environments and both
    operations (see ADR 0009's fifth amendment).
    """

    count: int
    prompt: Path
    negative_prompt: Path
    comfyui: ComfyUIConfig


class AssetsConfig(StrictModel):
    """Asset generation config, one entry per Asset kind."""

    lore: AssetKindConfig = AssetKindConfig(count=1)
    image: ImageAssetConfig
    model: AssetKindConfig = AssetKindConfig(count=2)


class SteamPunkFantasyConfig(StrictModel):
    paths: PathsConfig
    render: RenderConfig = RenderConfig()
    assets: AssetsConfig
