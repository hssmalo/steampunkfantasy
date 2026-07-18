"""S5: the shared `spf assets promote` CLI command over a throwaway kind."""

from pathlib import Path

import pytest
from cyclopts.exceptions import CycloptsError

from spf.assets import Kind, generate
from spf.assets.kinds import KINDS
from spf.config import config
from spf.frontends.cli import app
from tests.assets.conftest import FakeRefiner, FakeService


@pytest.fixture
def registered_kind(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> Kind:
    """Register a throwaway kind and point the config roots under tmp."""
    kind = Kind(name="_test", service=FakeService(), subdir="_test", extension="txt")
    monkeypatch.setitem(KINDS, kind.name, kind)
    monkeypatch.setattr(config.paths, "candidates", tmp_path / "candidates")
    monkeypatch.setattr(config.paths, "assets", tmp_path / "assets")
    return kind


def test_promote_command_lands_picked_candidate(registered_kind: Kind) -> None:
    generate(
        registered_kind,
        source="a grunt description",
        race="ork",
        name="grunt",
        count=3,
        candidates_root=config.paths.candidates,
    )
    app(
        ["assets", "promote", "ork", "_test", "grunt", "--pick", "2"],
        exit_on_error=False,
        result_action="return_value",
    )
    asset = config.paths.assets / "ork" / "_test" / "grunt.txt"
    assert asset.read_bytes() == b"two"


@pytest.mark.usefixtures("registered_kind")
def test_promote_command_accepts_a_dotted_lineage_pick() -> None:
    candidates = config.paths.candidates / "ork" / "_test"
    candidates.mkdir(parents=True)
    (candidates / "grunt.2.1.txt").write_bytes(b"refined")
    app(
        ["assets", "promote", "ork", "_test", "grunt", "--pick", "2.1"],
        exit_on_error=False,
        result_action="return_value",
    )
    asset = config.paths.assets / "ork" / "_test" / "grunt.txt"
    assert asset.read_bytes() == b"refined"


@pytest.mark.usefixtures("registered_kind")
def test_promote_command_rejects_a_malformed_pick() -> None:
    with pytest.raises(CycloptsError, match=r"[Ll]ineage"):
        app(
            ["assets", "promote", "ork", "_test", "grunt", "--pick", "2..1"],
            exit_on_error=False,
        )


def test_promote_command_unknown_kind_errors(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setattr(config.paths, "candidates", tmp_path / "candidates")
    monkeypatch.setattr(config.paths, "assets", tmp_path / "assets")
    with pytest.raises(CycloptsError, match="Unknown kind"):
        app(
            ["assets", "promote", "ork", "nope", "grunt", "--pick", "1"],
            exit_on_error=False,
        )


# --- Cycle 8: the refine command --------------------------------------------


@pytest.fixture
def refinable_registered_kind(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> Kind:
    """Register a throwaway refinable kind with a Candidate already on disk."""
    kind = Kind(
        name="_refinable", service=FakeRefiner(), subdir="_test", extension="txt"
    )
    monkeypatch.setitem(KINDS, kind.name, kind)
    monkeypatch.setattr(config.paths, "candidates", tmp_path / "candidates")
    monkeypatch.setattr(config.paths, "assets", tmp_path / "assets")
    candidates = config.paths.candidates / "ork" / "_test"
    candidates.mkdir(parents=True)
    (candidates / "grunt.2.txt").write_bytes(b"the original")
    return kind


def _refine_argv(*extra: str) -> list[str]:
    return [
        "assets",
        "refine",
        "ork",
        "_refinable",
        "grunt",
        "--from",
        "2",
        "make the hat brass",
        *extra,
    ]


@pytest.mark.usefixtures("refinable_registered_kind")
def test_refine_command_writes_candidates_under_the_lineage() -> None:
    app(_refine_argv("--count", "2"), exit_on_error=False, result_action="return_value")

    candidates = config.paths.candidates / "ork" / "_test"
    assert (candidates / "grunt.2.1.txt").read_bytes() == b"one"
    assert (candidates / "grunt.2.2.txt").read_bytes() == b"two"
    assert (candidates / "grunt.2.txt").read_bytes() == b"the original"


@pytest.mark.usefixtures("refinable_registered_kind")
def test_refine_omits_the_negative_prompt_line_for_a_non_image_kind(
    capsys: pytest.CaptureFixture[str],
) -> None:
    # `refine` serves every Kind; the Negative Prompt is an image concern, so
    # naming its file during a lore or model refinement would be a lie.
    app(_refine_argv("--count", "1"), exit_on_error=False, result_action="return_value")

    assert "image-negative.txt" not in capsys.readouterr().out


def test_refine_command_passes_the_correction_verbatim(
    refinable_registered_kind: Kind,
) -> None:
    app(_refine_argv("--count", "1"), exit_on_error=False, result_action="return_value")

    service = refinable_registered_kind.service
    assert isinstance(service, FakeRefiner)
    # No prompts/image.txt preamble, no race description: just the Correction.
    assert service.seen_source == "make the hat brass"


@pytest.mark.usefixtures("refinable_registered_kind")
def test_refine_command_rejects_a_malformed_from() -> None:
    argv = [
        "assets",
        "refine",
        "ork",
        "_refinable",
        "grunt",
        "--from",
        "2..1",
        "fix it",
    ]
    with pytest.raises(CycloptsError, match=r"[Ll]ineage"):
        app(argv, exit_on_error=False, result_action="return_value")


@pytest.mark.usefixtures("refinable_registered_kind")
def test_refine_command_errors_cleanly_on_a_missing_source_candidate(
    capsys: pytest.CaptureFixture[str],
) -> None:
    argv = ["assets", "refine", "ork", "_refinable", "grunt", "--from", "9", "fix it"]
    with pytest.raises(SystemExit):
        app(argv, exit_on_error=False, result_action="return_value")

    # Names the path it looked for, rather than raising a traceback.
    assert "grunt.9.txt" in capsys.readouterr().err


def test_refine_command_errors_cleanly_on_a_kind_that_cannot_refine(
    registered_kind: Kind,  # noqa: ARG001  registers the generate-only _test kind
    capsys: pytest.CaptureFixture[str],
) -> None:
    candidates = config.paths.candidates / "ork" / "_test"
    candidates.mkdir(parents=True)
    (candidates / "grunt.2.txt").write_bytes(b"the original")
    argv = ["assets", "refine", "ork", "_test", "grunt", "--from", "2", "fix it"]

    with pytest.raises(SystemExit):
        app(argv, exit_on_error=False, result_action="return_value")

    assert "does not support refinement" in capsys.readouterr().err
