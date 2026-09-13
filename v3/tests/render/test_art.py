"""The Site's `/art/` namespace: stable URLs, and the step that publishes them."""

from pathlib import Path, PureWindowsPath

import pytest

from spf.config import config
from spf.render.art import absolute_art_url, art_src, art_url, publish_art

# --- The URL: one stable spelling per Image Asset ----------------------------


def test_art_url_is_rooted_at_the_art_namespace(site_base_url: str) -> None:  # noqa: ARG001
    # Deliberately not a mirror of `assets/<race>/images/<name>.png`: the bytes
    # behind the URL are selected from the store, not served from it (ADR 0040).
    assert art_url("goblin", "grunt") == "/site/art/goblin/grunt.png"


def test_art_url_carries_the_path_the_site_is_served_under(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # A project Pages site lives under a subpath, so a URL rooted at the origin
    # would climb out of it exactly as a relative one climbs out of `output/`.
    monkeypatch.setattr(config.site, "base_url", "https://example.test")

    assert art_url("goblin", "grunt") == "/art/goblin/grunt.png"


def test_art_src_spells_a_committed_asset_as_its_url(site_base_url: str) -> None:  # noqa: ARG001
    asset = Path("/repo/assets/goblin/images/grunt.png")

    assert art_src(asset) == "/site/art/goblin/grunt.png"


def test_art_src_emits_forward_slashes_for_a_windows_path(site_base_url: str) -> None:  # noqa: ARG001
    # A backslash escapes punctuation in CommonMark, so a native-Windows path
    # would render as `....%5Cgrunt.png` and the image 404s.
    asset = PureWindowsPath(r"C:\repo\assets\goblin\images\grunt.png")

    assert art_src(asset) == "/site/art/goblin/grunt.png"


def test_absolute_art_url_names_the_origin_and_the_url_below_it(
    site_base_url: str,  # noqa: ARG001
) -> None:
    # The origin lives in exactly one place, so a custom domain is a config
    # change rather than a re-render.
    assert absolute_art_url("goblin", "grunt") == (
        "https://example.test/site/art/goblin/grunt.png"
    )


# --- The publish step: every committed Asset lands under `output/art/` -------


def _commit(assets_root: Path, race: str, name: str, content: bytes) -> Path:
    path = assets_root / race / "images" / f"{name}.png"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(content)
    return path


def test_publish_art_copies_every_committed_asset(tmp_path: Path) -> None:
    assets_root = tmp_path / "assets"
    _commit(assets_root, "goblin", "grunt", b"grunt bytes")
    _commit(assets_root, "elf", "scout", b"scout bytes")
    output_root = tmp_path / "output"

    published = publish_art(output_root, assets_root=assets_root)

    assert published == [
        output_root / "art" / "elf" / "scout.png",
        output_root / "art" / "goblin" / "grunt.png",
    ]
    assert (output_root / "art" / "goblin" / "grunt.png").read_bytes() == b"grunt bytes"
    assert (output_root / "art" / "elf" / "scout.png").read_bytes() == b"scout bytes"


def test_publish_art_publishes_the_best_bytes_at_the_same_url(tmp_path: Path) -> None:
    # One URL per image; the bytes behind it may improve without the URL moving.
    assets_root = tmp_path / "assets"
    _commit(assets_root, "goblin", "grunt", b"full size")
    _commit(assets_root, "goblin", "grunt.small", b"downscaled")
    output_root = tmp_path / "output"

    published = publish_art(output_root, assets_root=assets_root)

    assert published == [output_root / "art" / "goblin" / "grunt.png"]
    assert published[0].read_bytes() == b"downscaled"


def test_publish_art_writes_nothing_for_an_empty_store(tmp_path: Path) -> None:
    assert publish_art(tmp_path / "output", assets_root=tmp_path / "assets") == []
