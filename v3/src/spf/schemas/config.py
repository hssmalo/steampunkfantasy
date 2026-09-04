"""Schema for configuration of SteamPunkFantasy."""

from pathlib import Path
from typing import Literal, get_args

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


type ComfyUIEnvName = Literal["local", "cloud"]
"""The ComfyUI Environments this project knows about.

One Environment per committed `workflows/<env>/` directory. Kept as a Literal
so the names have a single source: `ComfyUIConfig` derives its lookup and its
error message from it, and `spf assets profiles` iterates it.
"""

COMFYUI_ENV_NAMES: tuple[ComfyUIEnvName, ...] = get_args(ComfyUIEnvName.__value__)


class ComfyUIEnvConfig(StrictModel):
    """A single ComfyUI Environment: where to reach it and its default Profile."""

    base_url: str
    profile: str
    api_key_env: str = ""


class ComfyUIConfig(StrictModel):
    """The ComfyUI provider config: the two Environments and the selector."""

    env: str = "local"
    timeout_s: int = 900
    profile: str = ""
    local: ComfyUIEnvConfig
    cloud: ComfyUIEnvConfig

    def selected(self, name: str | None = None) -> ComfyUIEnvConfig:
        """Return the Environment block named by `name` (or `self.env`).

        Raises `ValueError` naming the two valid Environments when
        the name is neither (mirrors `spf.assets.get_kind`).
        """
        env_name = name if name is not None else self.env
        if env_name in COMFYUI_ENV_NAMES:
            block: ComfyUIEnvConfig = getattr(self, env_name)
            return block
        known = ", ".join(COMFYUI_ENV_NAMES)
        msg = f"Unknown ComfyUI env {env_name!r}; known envs: {known}"
        raise ValueError(msg)


class ImageAssetConfig(StrictModel):
    """Image asset settings: count, the two prompt files, and the provider.

    Both prompt files are configured paths rather than hardcoded basenames,
    following the Workflows' resolved paths. They sit here and not in an
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

    order_names: list[str] = Field(default_factory=list)
    """Every order an Order Card may name, spelled as the card prints it.

    Authored here rather than read from `rules/orders.toml`, which is still
    being drafted: a linter reading it would hold a draft to a schema.
    """


class SteamPunkFantasyConfig(StrictModel):
    paths: PathsConfig
    render: RenderConfig = RenderConfig()
    assets: AssetsConfig
    lint: LintConfig = LintConfig()
