"""S4: the assets layout paths and per-kind counts resolve from config."""

from pathlib import Path

from spf.config import config


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
