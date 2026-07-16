"""The Image Asset kind: AI-generated race/unit art via ComfyUI.

Registers the `image` `Kind`, laid out at
`<race>/images/<name>.png`, backed by
`ComfyUIService`. This module is pure wiring: it
builds the service from the configured ComfyUI **Environment** and registers
the Kind. The provider — one stdlib client across local ComfyUI and Comfy Cloud
— lives in `spf.assets.comfyui` (see ADR 0009).
"""

from spf.assets.comfyui import ComfyUIService
from spf.assets.kinds import Kind, register_kind
from spf.config import config


def _build_service() -> ComfyUIService:
    """Build the Image `ComfyUIService` from config.

    Reads neither the network nor the Workflow file; a missing or invalid
    `env` raises here (a config typo, worth failing loudly at import).
    """
    comfyui = config.assets.image.comfyui
    env = comfyui.selected()  # ComfyUIEnvConfig for comfyui.env; raises on bad env
    return ComfyUIService(
        base_url=env.base_url,
        workflow_path=env.workflow,
        api_key_env=env.api_key_env,
        timeout_s=comfyui.timeout_s,
    )


IMAGE = register_kind(
    Kind(
        name="image",
        service=_build_service(),
        subdir="images",
        extension="png",
    )
)
