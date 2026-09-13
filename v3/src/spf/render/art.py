"""The Site's `/art/` namespace: where an Image Asset is published and reached.

A committed Image Asset lives outside the deployed artifact, so the Site cannot
reference it in place the way a local rendering does (ADR 0017). It publishes a
copy under `output/art/<race>/<name>.png` instead and spells it as a
root-relative URL, which is stable: the bytes behind it are the best available
in the store, and may improve without the URL moving (ADR 0040).
"""

import shutil
from pathlib import Path, PurePath

from spf.assets.image import IMAGE
from spf.assets.spine import SMALL, asset_for, committed_assets, locate
from spf.config import config


def art_url(race: str, name: str) -> str:
    """Return the Site URL that publishes `name`'s art, root-relative."""
    return f"/{config.site.art}/{race}/{name}.{IMAGE.extension}"


def absolute_art_url(race: str, name: str) -> str:
    """Return `art_url` against the configured origin, for an off-site caller.

    The HTML never needs the origin -- it is served from it. An API handing a
    client a URL does, and the origin is configured in one place so a custom
    domain stays a config change.
    """
    return f"{config.site.base_url.rstrip('/')}{art_url(race, name)}"


def art_src(asset: PurePath) -> str:
    """Spell the path of a committed Image Asset as its published Site URL."""
    return art_url(*locate(IMAGE, asset))


def publish_art(
    output_root: Path, *, assets_root: Path = config.paths.assets
) -> list[Path]:
    """Copy every committed Image Asset into the Site's `/art/` namespace.

    Publishes the whole store unconditionally rather than what some page
    happens to reference: a URL contract conditional on another page's content
    is not a contract. Each Asset is published at its best available bytes --
    its downscaled Rendition where one exists, the Asset itself otherwise.
    Returns the written paths.
    """
    published = []
    for race, name in committed_assets(IMAGE, assets_root=assets_root):
        source = asset_for(
            IMAGE, race, name=name, assets_root=assets_root, rendition=SMALL
        )
        if source is None:  # pragma: no cover  listed from the store a line above
            continue
        target = output_root / config.site.art / race / f"{name}.{IMAGE.extension}"
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, target)
        published.append(target)
    return published
