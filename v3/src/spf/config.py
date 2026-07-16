"""Configuration of SteamPunkFantasy."""

import configaroo

from spf.schemas.config import SteamPunkFantasyConfig

config_path = configaroo.find_pyproject_toml() / "configs" / "spf.toml"
config = (
    configaroo.Configuration.from_file(config_path)
    .add_envs({"COMFYUI_ENV": "assets.image.comfyui.env"}, prefix="SPF_")
    .parse_dynamic()
    .convert_model(SteamPunkFantasyConfig)
)
