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


class LatexConfig(StrictModel):
    engine: str = "pdflatex"


class RenderConfig(StrictModel):
    latex: LatexConfig = LatexConfig()


class AssetKindConfig(StrictModel):
    """Per-kind Asset settings (how many Candidates to generate, ...)."""

    count: int


class AssetsConfig(StrictModel):
    """Asset generation config, one entry per Asset kind."""

    lore: AssetKindConfig = AssetKindConfig(count=1)
    image: AssetKindConfig = AssetKindConfig(count=3)
    model: AssetKindConfig = AssetKindConfig(count=2)


class SteamPunkFantasyConfig(StrictModel):
    paths: PathsConfig
    render: RenderConfig = RenderConfig()
    assets: AssetsConfig = AssetsConfig()
