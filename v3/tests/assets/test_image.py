"""The Image kind: ComfyUI-backed Service wiring, env selection, CLI flow.

The provider internals (patching, submit/poll/fetch, retries) are covered in
`test_comfyui.py`. Here we test the *wiring*: that the Kind is registered,
that `_build_service` honours the configured Environment, and that the
`spf assets image` command composes prompts and writes Candidates end-to-end
over a monkeypatched `comfyui._request`.
"""

import urllib.parse
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pytest
from cyclopts.exceptions import CycloptsError

from spf.assets import comfyui, get_kind
from spf.assets import image as img
from spf.config import config
from spf.frontends.cli import app

_FIXTURES = Path(__file__).parent / "fixtures"
_MINI = _FIXTURES / "mini_workflow.json"
_MINI_REFINE = _FIXTURES / "mini_refine_workflow.json"
_PNG = b"\x89PNG\r\n\x1a\n"
_POSITIVE = "2"  # the positive text node in mini_workflow.json
_NEGATIVE_NODE = "3"  # the negative text node in mini_workflow.json
_SAMPLER = "5"  # the KSampler in mini_workflow.json
_NEGATIVE_TEXT = "blurry, watermarked"

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

_DWARF_TOML = """\
[races.dwarf]
name = "Dwarf"
description = "Stubborn engineers with brass-plated beards"

[units.dwarf_grunt]
race = "dwarf"
name = "Dwarf Grunt"
description = "A dwarf grunt swinging a riveted club"
models = []
size = "Small"
[units.dwarf_grunt.shaken]
speed = "slow"
movement_order = ["-", "-", "flee"]
[units.dwarf_grunt.orders]
[units.dwarf_grunt.damage_tables]

[units.dwarf_scout]
race = "dwarf"
name = "Dwarf Scout"
description = "A wiry dwarf scout with a spyglass"
models = []
size = "Small"
[units.dwarf_scout.shaken]
speed = "slow"
movement_order = ["-", "-", "flee"]
[units.dwarf_scout.orders]
[units.dwarf_scout.damage_tables]

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


class _FakeRequest:
    """A stand-in for `comfyui._request` for the CLI flow.

    Records the submitted graphs, then serves a completed job and PNG bytes.
    Set `fail` to make every job report a `failed` status, so the CLI's
    error path can be exercised.
    """

    def __init__(self, *, fail: bool = False) -> None:
        self.submissions: list[dict[str, Any]] = []
        self._fail = fail
        self._counter = 0

    def __call__(  # noqa: PLR0913  mirrors the _request seam's fixed shape
        self,
        base: str,  # noqa: ARG002  positional to match _request; unused here
        path: str,
        *,
        api_key: str | None = None,  # noqa: ARG002  unused in this fake
        body: dict[str, Any] | None = None,
        upload: tuple[str, bytes] | None = None,
        raw: bool = False,
        timeout: float = 120,  # noqa: ARG002  part of the seam signature; unused
    ) -> Any:  # noqa: ANN401  mirrors _request's dynamic return
        if path == "/api/upload/image":  # a Refinement uploads its init image
            assert upload is not None
            return {"name": upload[0], "subfolder": "", "type": "input"}
        if path == "/api/prompt":
            self._counter += 1
            assert body is not None
            self.submissions.append(body["prompt"])
            return {"prompt_id": f"pid-{self._counter}"}
        if raw:  # /api/view — echo the requested filename so blobs are per-job
            query = urllib.parse.parse_qs(path.split("?", 1)[1])
            return _PNG + query["filename"][0].encode()
        if self._fail:
            return {"status": "failed", "node_errors": {"5": "CUDA out of memory"}}
        pid = path.rsplit("/", 1)[-1]
        outputs = {"7": {"images": [{"filename": f"{pid}.png", "type": "output"}]}}
        return {"status": "completed", "outputs": outputs}


@dataclass
class _ImageEnv:
    """A configured tmp project plus the scripted ComfyUI seam."""

    root: Path
    comfy: _FakeRequest

    @property
    def candidates(self) -> Path:
        return self.root / "candidates"

    def prompts(self) -> list[str]:
        """Return the positive prompt patched into each submitted job, in order."""
        return [g[_POSITIVE]["inputs"]["text"] for g in self.comfy.submissions]

    def seeds(self) -> list[int]:
        """Return the seed patched into each submitted job, in order."""
        return [g[_SAMPLER]["inputs"]["seed"] for g in self.comfy.submissions]


def _make_env(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, *, fail: bool = False
) -> _ImageEnv:
    races = tmp_path / "races"
    races.mkdir()
    (races / "ogre.toml").write_text(_OGRE_TOML, encoding="utf-8")
    (races / "gnome.toml").write_text(_GNOME_TOML, encoding="utf-8")
    (races / "dwarf.toml").write_text(_DWARF_TOML, encoding="utf-8")
    prompts = tmp_path / "prompts"
    prompts.mkdir()
    positive = prompts / "image.txt"
    negative = prompts / "image-negative.txt"
    positive.write_text("Preamble one.\ntwo.\n", encoding="utf-8")
    negative.write_text(_NEGATIVE_TEXT, encoding="utf-8")
    monkeypatch.setattr(config.paths, "races", races)
    monkeypatch.setattr(config.paths, "prompts", prompts)
    monkeypatch.setattr(config.paths, "project", tmp_path)
    monkeypatch.setattr(config.paths, "candidates", tmp_path / "candidates")
    monkeypatch.setattr(config.paths, "assets", tmp_path / "assets")
    # Both prompt files are configured paths now, so the CLI reads them from
    # here rather than from `paths.prompts` plus a hardcoded basename.
    monkeypatch.setattr(config.assets.image, "prompt", positive)
    monkeypatch.setattr(config.assets.image, "negative_prompt", negative)

    comfy = _FakeRequest(fail=fail)
    monkeypatch.setattr(comfyui, "_request", comfy)
    # The wired service points at the (gitignored) real workflow; aim it at the
    # committed fixture so the flow runs without a per-machine local.json.
    monkeypatch.setattr(img.IMAGE.service, "_workflow_path", _MINI)
    monkeypatch.setattr(img.IMAGE.service, "_refine_workflow_path", _MINI_REFINE)
    # Likewise the Negative Prompt: the service bound the configured path at
    # import, so aim it at this project's own file.
    monkeypatch.setattr(img.IMAGE.service, "_negative_path", negative)
    return _ImageEnv(tmp_path, comfy)


@pytest.fixture
def image_env(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> _ImageEnv:
    """Configure a tmp project with a happy scripted ComfyUI."""
    return _make_env(monkeypatch, tmp_path)


def _run(*argv: str) -> None:
    app([*argv], exit_on_error=False, result_action="return_value")


# --- Kind registration + service wiring -------------------------------------


def test_image_kind_is_registered() -> None:
    kind = get_kind("image")
    assert kind.subdir == "images"
    assert kind.extension == "png"
    assert isinstance(kind.service, comfyui.ComfyUIService)


def test_build_service_points_at_the_selected_env(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    cu = config.assets.image.comfyui
    monkeypatch.setattr(cu, "env", "cloud")

    service = img._build_service()

    assert service._base_url == cu.cloud.base_url
    assert service._workflow_path == config.paths.workflows / cu.cloud.workflow
    assert service._api_key_env == cu.cloud.api_key_env
    # The Environment's refine Workflow is wired through too, so a Refinement
    # uses the same Environment's authored edit graph.
    refine = config.paths.workflows / cu.cloud.refine_workflow
    assert service._refine_workflow_path == refine
    # The Negative Prompt file is shared, not per-Environment (issue 50, D2),
    # so it comes off `assets.image` rather than the Environment block.
    assert service._negative_path == config.assets.image.negative_prompt


def test_build_service_rejects_an_unknown_env(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(config.assets.image.comfyui, "env", "staging")
    with pytest.raises(ValueError, match="Unknown ComfyUI env"):
        img._build_service()


# --- CLI flow (provider-agnostic, over the scripted seam) -------------------


def test_cli_unit_image_writes_candidates(
    image_env: _ImageEnv, capsys: pytest.CaptureFixture[str]
) -> None:
    _run("assets", "image", "ogre", "ogre_grunt", "--seed", "5")

    images = image_env.candidates / "ogre" / "images"
    written = sorted(p.name for p in images.glob("*.png"))
    assert written == ["ogre_grunt.1.png", "ogre_grunt.2.png", "ogre_grunt.3.png"]
    assert (images / "ogre_grunt.1.png").read_bytes().startswith(_PNG)
    out = capsys.readouterr().out
    assert "5" in out  # the seed is printed
    # The composed prompt is echoed before the request goes out.
    assert "A stout ogre grunt hefting a huge wrench" in out
    # The Negative Prompt is static, so only its path is named — project-
    # relative, short enough to read and to retype (issue 50, D7).
    assert "Negative: prompts/image-negative.txt" in out
    # Each Candidate's path is reported as it lands (one "Wrote" per image).
    assert out.count("Wrote ") == 3
    assert "ogre_grunt.1.png" in out
    assert "spf assets promote ogre image ogre_grunt --pick" in out


def test_cli_unit_image_patches_the_authored_negative_prompt(
    image_env: _ImageEnv,
) -> None:
    _run("assets", "image", "ogre", "ogre_grunt", "--seed", "5")

    negatives = [
        g[_NEGATIVE_NODE]["inputs"]["text"] for g in image_env.comfy.submissions
    ]
    assert negatives == [_NEGATIVE_TEXT] * 3  # every job in the batch


def test_cli_refine_image_names_the_negative_prompt_file(
    image_env: _ImageEnv, capsys: pytest.CaptureFixture[str]
) -> None:
    candidates = image_env.candidates / "ogre" / "images"
    candidates.mkdir(parents=True)
    (candidates / "ogre_grunt.2.png").write_bytes(_PNG)

    _run(
        "assets",
        "refine",
        "ogre",
        "image",
        "ogre_grunt",
        "--from",
        "2",
        "make the hat brass",
        "--count",
        "1",
    )

    assert "Negative: prompts/image-negative.txt" in capsys.readouterr().out


def test_cli_unit_image_prompt_composes_preamble_name_description(
    image_env: _ImageEnv,
) -> None:
    _run("assets", "image", "ogre", "ogre_grunt", "--seed", "5")

    assert image_env.prompts()[0] == (
        "Subject: Ogre Grunt."
        "\nDetails: A stout ogre grunt hefting a huge wrench"
        "\nPreamble one.\ntwo.\n"
    )


def test_cli_race_image_uses_race_name_layout(image_env: _ImageEnv) -> None:
    _run("assets", "image", "ogre", "--seed", "5")

    images = image_env.candidates / "ogre" / "images"
    assert sorted(p.name for p in images.glob("*.png")) == [
        "ogre.1.png",
        "ogre.2.png",
        "ogre.3.png",
    ]


def test_cli_same_seed_reproduces_batch(image_env: _ImageEnv) -> None:
    _run("assets", "image", "ogre", "ogre_grunt", "--seed", "123")
    first = image_env.seeds()
    image_env.comfy.submissions.clear()
    _run("assets", "image", "ogre", "ogre_grunt", "--seed", "123")

    assert image_env.seeds() == first  # same base seed → same sub-seeds


def test_cli_count_override_beats_config(image_env: _ImageEnv) -> None:
    _run("assets", "image", "ogre", "ogre_grunt", "--seed", "1", "--count", "1")

    images = image_env.candidates / "ogre" / "images"
    assert [p.name for p in images.glob("*.png")] == ["ogre_grunt.1.png"]


def test_cli_blank_unit_description_exits_without_writing(
    image_env: _ImageEnv, capsys: pytest.CaptureFixture[str]
) -> None:
    with pytest.raises(SystemExit) as excinfo:
        _run("assets", "image", "ogre", "ogre_blank")

    assert excinfo.value.code == 1
    assert not image_env.candidates.exists()
    assert "no description" in capsys.readouterr().err


def test_cli_blank_race_description_exits_without_writing(
    image_env: _ImageEnv,
) -> None:
    with pytest.raises(SystemExit) as excinfo:
        _run("assets", "image", "gnome")

    assert excinfo.value.code == 1
    assert not image_env.candidates.exists()


def test_cli_failed_job_surfaces_red_error(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    *,
    capsys: pytest.CaptureFixture[str],
) -> None:
    _make_env(monkeypatch, tmp_path, fail=True)

    with pytest.raises(SystemExit) as excinfo:
        _run("assets", "image", "ogre", "ogre_grunt", "--seed", "5")

    assert excinfo.value.code == 1
    err = capsys.readouterr().err
    assert "image generation failed" in err
    assert "CUDA out of memory" in err  # ComfyUI's node_errors surfaced


@pytest.mark.usefixtures("image_env")
def test_cli_unknown_race_errors() -> None:
    # RACE is typed as a Literal, so cyclopts rejects unknown values itself.
    with pytest.raises(CycloptsError, match="nope"):
        _run("assets", "image", "nope")


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


def test_cli_all_flag_covers_the_race_and_every_unit(image_env: _ImageEnv) -> None:
    _run("assets", "image", "dwarf", "--all", "--seed", "5", "--count", "1")

    images = image_env.candidates / "dwarf" / "images"
    assert sorted(p.name for p in images.glob("*.png")) == [
        "dwarf.1.png",
        "dwarf_grunt.1.png",
        "dwarf_scout.1.png",
    ]


def test_cli_missing_flag_skips_targets_that_already_have_assets(
    image_env: _ImageEnv,
) -> None:
    assets = image_env.root / "assets" / "dwarf" / "images"
    assets.mkdir(parents=True)
    (assets / "dwarf_grunt.png").write_bytes(_PNG)

    _run("assets", "image", "dwarf", "--missing", "--seed", "5", "--count", "1")

    images = image_env.candidates / "dwarf" / "images"
    # dwarf_grunt is already promoted; the race-level Target is included.
    assert sorted(p.name for p in images.glob("*.png")) == [
        "dwarf.1.png",
        "dwarf_scout.1.png",
    ]


@pytest.mark.usefixtures("image_env")
@pytest.mark.parametrize(
    "argv",
    [
        ["assets", "image", "dwarf", "--all", "--missing"],
        ["assets", "image", "dwarf", "dwarf_grunt", "--all"],
    ],
)
def test_cli_selectors_are_mutually_exclusive(argv: list[str]) -> None:
    with pytest.raises(CycloptsError, match=r"[Mm]utually exclusive"):
        _run(*argv)


@pytest.mark.usefixtures("image_env")
def test_cli_magic_all_unit_is_gone() -> None:
    # `image <race> all` used to mean --all; it is now just an unknown unit.
    with pytest.raises(SystemExit):
        _run("assets", "image", "dwarf", "all")
