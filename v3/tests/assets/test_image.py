"""The Image kind: Pollinations-backed Service, URL building, registration."""

from pathlib import Path
from urllib.parse import parse_qs, unquote, urlsplit

import pytest

from spf.assets import get_kind
from spf.assets import image as img
from spf.config import config
from spf.frontends.cli import app

_OGRE_TOML = """\
[races.ogre]
name = "Ogre"
description = "Yellow, tiny, little men"

[units.ogre_grunt]
race = "ogre"
name = "Ogre Grunt"
description = "A stout ogre grunt hefting a huge wrench"
models = []
size = "Small"
[units.ogre_grunt.shaken]
speed = "slow"
movement_order = ["-", "-", "flee"]
[units.ogre_grunt.orders]
[units.ogre_grunt.damage_tables]

[units.ogre_blank]
race = "ogre"
name = "Ogre Blank"
models = []
size = "Small"
[units.ogre_blank.shaken]
speed = "slow"
movement_order = ["-", "-", "flee"]
[units.ogre_blank.orders]
[units.ogre_blank.damage_tables]

[models]
[equipment]
"""

_GNOME_TOML = """\
[races.gnome]
name = "Gnome"

[units]
[models]
[equipment]
"""


@pytest.fixture
def image_env(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> Path:
    """Point config at tmp race/prompt/store dirs and fake the network fetch."""
    races = tmp_path / "races"
    races.mkdir()
    (races / "ogre.toml").write_text(_OGRE_TOML, encoding="utf-8")
    (races / "gnome.toml").write_text(_GNOME_TOML, encoding="utf-8")
    prompts = tmp_path / "prompts"
    prompts.mkdir()
    (prompts / "image.txt").write_text("Preamble one.\ntwo.\n", encoding="utf-8")
    monkeypatch.setattr(config.paths, "races", races)
    monkeypatch.setattr(config.paths, "prompts", prompts)
    monkeypatch.setattr(config.paths, "candidates", tmp_path / "candidates")
    monkeypatch.setattr(config.paths, "assets", tmp_path / "assets")
    monkeypatch.setattr(img, "_fetch", lambda url: b"PNG:" + url.encode("utf-8"))
    return tmp_path


def _run(*argv: str) -> None:
    app([*argv], exit_on_error=False, result_action="return_value")


def test_service_derives_deterministic_distinct_seeds(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(img, "_fetch", lambda url: url.encode("utf-8"))
    service = img.PollinationsService()

    first = service.generate("a prompt", 3, seed=42)
    again = service.generate("a prompt", 3, seed=42)

    assert len(first) == 3
    assert first == again  # deterministic given the base seed
    assert len(set(first)) == 3  # count distinct sub-seeds derived from one base


def test_service_returns_blobs_in_order(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(img, "_fetch", lambda url: url.encode("utf-8"))
    service = img.PollinationsService()

    blobs = service.generate("a prompt", 2, seed=1)

    seeds = [int(parse_qs(urlsplit(b.decode()).query)["seed"][0]) for b in blobs]
    rng = __import__("random").Random(1)
    expected = [rng.randrange(2**31) for _ in range(2)]
    assert seeds == expected


def test_build_url_encodes_prompt_and_params() -> None:
    url = img._build_url("Ogre Infantry, side by side", seed=99)

    split = urlsplit(url)
    assert split.netloc == "gen.pollinations.ai"
    assert " " not in url  # prompt is URL-encoded
    assert "Ogre%20Infantry" in url
    params = parse_qs(split.query)
    assert params["width"] == ["1024"]
    assert params["height"] == ["1024"]
    assert params["model"] == ["zimage"]
    assert params["seed"] == ["99"]


def test_image_kind_is_registered() -> None:
    kind = get_kind("image")
    assert kind.subdir == "images"
    assert kind.extension == "png"
    assert isinstance(kind.service, img.PollinationsService)


def test_cli_unit_image_writes_candidates(
    image_env: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    _run("assets", "image", "ogre", "ogre_grunt", "--seed", "5")

    images = image_env / "candidates" / "ogre" / "images"
    written = sorted(p.name for p in images.glob("*.png"))
    assert written == ["ogre_grunt.1.png", "ogre_grunt.2.png", "ogre_grunt.3.png"]
    assert (images / "ogre_grunt.1.png").read_bytes().startswith(b"PNG:")
    out = capsys.readouterr().out
    assert "5" in out  # the seed is printed
    assert "spf assets promote ogre image ogre_grunt --pick" in out


def test_cli_unit_image_prompt_composes_preamble_name_description(
    image_env: Path,
) -> None:
    _run("assets", "image", "ogre", "ogre_grunt", "--seed", "5")

    blob = image_env / "candidates" / "ogre" / "images" / "ogre_grunt.1.png"
    url = blob.read_bytes().removeprefix(b"PNG:").decode("utf-8")
    prompt = unquote(urlsplit(url).path.split("/image/", 1)[1])
    assert prompt == (
        "Preamble one. two. Ogre Grunt. A stout ogre grunt hefting a huge wrench"
    )


def test_cli_race_image_uses_race_name_layout(image_env: Path) -> None:
    _run("assets", "image", "ogre", "--seed", "5")

    images = image_env / "candidates" / "ogre" / "images"
    assert sorted(p.name for p in images.glob("*.png")) == [
        "ogre.1.png",
        "ogre.2.png",
        "ogre.3.png",
    ]


def test_cli_blank_unit_description_exits_without_writing(
    image_env: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    with pytest.raises(SystemExit) as excinfo:
        _run("assets", "image", "ogre", "ogre_blank")

    assert excinfo.value.code == 1
    assert not (image_env / "candidates").exists()
    assert "no description" in capsys.readouterr().err


def test_cli_blank_race_description_exits_without_writing(image_env: Path) -> None:
    with pytest.raises(SystemExit) as excinfo:
        _run("assets", "image", "gnome")

    assert excinfo.value.code == 1
    assert not (image_env / "candidates").exists()


@pytest.mark.usefixtures("image_env")
def test_cli_unknown_race_errors(capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit) as excinfo:
        _run("assets", "image", "nope")

    assert excinfo.value.code == 1
    assert "nope" in capsys.readouterr().err


@pytest.mark.usefixtures("image_env")
def test_cli_unknown_unit_lists_available(
    capsys: pytest.CaptureFixture[str],
) -> None:
    with pytest.raises(SystemExit) as excinfo:
        _run("assets", "image", "ogre", "not_a_unit")

    assert excinfo.value.code == 1
    err = capsys.readouterr().err
    assert "not_a_unit" in err
    assert "ogre_grunt" in err  # available units listed


def _urls(images: Path, name: str) -> list[str]:
    return [
        p.read_bytes().removeprefix(b"PNG:").decode("utf-8")
        for p in sorted(images.glob(f"{name}.*.png"))
    ]


def test_cli_same_seed_reproduces_batch(image_env: Path) -> None:
    images = image_env / "candidates" / "ogre" / "images"
    _run("assets", "image", "ogre", "ogre_grunt", "--seed", "123")
    first = _urls(images, "ogre_grunt")
    _run("assets", "image", "ogre", "ogre_grunt", "--seed", "123")
    assert _urls(images, "ogre_grunt") == first


def test_cli_count_override_beats_config(image_env: Path) -> None:
    _run("assets", "image", "ogre", "ogre_grunt", "--seed", "1", "--count", "1")

    images = image_env / "candidates" / "ogre" / "images"
    assert [p.name for p in images.glob("*.png")] == ["ogre_grunt.1.png"]


@pytest.mark.integration
def test_live_pollinations_returns_png_bytes() -> None:
    """Opt-in: really call Pollinations for one small image (skipped by default).

    Run with ``pytest -m integration``. Skips when the anonymous path is
    unavailable (rate-limited/401) and no ``SPF_POLLINATIONS_API_KEY`` is set.
    """
    service = img.PollinationsService()
    try:
        blobs = service.generate(
            "A single steampunk gear on a plain background", 1, seed=1
        )
    except OSError as err:  # anonymous tier rate-limited / unauthorized
        pytest.skip(f"Pollinations unavailable: {err}")

    assert len(blobs) == 1
    assert isinstance(blobs[0], bytes)
    assert len(blobs[0]) > 0
    assert blobs[0][:8] == b"\x89PNG\r\n\x1a\n"
