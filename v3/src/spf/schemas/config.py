"""Schema for configuration of SteamPunkFantasy."""

from pathlib import Path

from pydantic import Field

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


class LintConfig(StrictModel):
    """Naming conventions the Race-data linter treats as legitimate.

    Divergences between a key and its display name are allowed only by rule,
    never per instance -- an annotation on a single entry would let a real
    defect be silenced by marking it intentional.
    """

    aliases: dict[str, str] = Field(default_factory=dict)
    """Key spellings rewritten before comparison, e.g. `darkelf` to `dark_elf`.

    Applied to the key only, so the name must match the expansion.
    """

    optional_key_prefixes: list[str] = Field(default_factory=list)
    optional_key_suffixes: list[str] = Field(default_factory=list)
    """Affixes a key may carry that its display name omits, e.g. `_free`."""

    function_words: list[str] = Field(default_factory=list)
    """Words that must stay lowercase anywhere but the start of a name."""


class SteamPunkFantasyConfig(StrictModel):
    paths: PathsConfig
    render: RenderConfig = RenderConfig()
    assets: AssetsConfig
    lint: LintConfig = LintConfig()
