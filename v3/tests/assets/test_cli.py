"""S5: the shared `spf assets promote` CLI command over a throwaway kind."""

from pathlib import Path

import pytest
from cyclopts.exceptions import CycloptsError

from spf.assets import Kind, generate, promote
from spf.assets.kinds import KINDS
from spf.config import config
from spf.frontends.cli import app
from tests.assets.conftest import FakeRefiner, FakeService


@pytest.fixture
def registered_kind(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> Kind:
    """Register a throwaway kind and point the config roots under tmp."""
    kind = Kind(
        name="_test",
        service=FakeService(),
        subdir="_test",
        extension="txt",
        targets=frozenset({"race", "unit"}),
    )
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
        name="_refinable",
        service=FakeRefiner(),
        subdir="_test",
        extension="txt",
        targets=frozenset({"race", "unit"}),
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


def test_image_command_errors_cleanly_on_an_unknown_unit(
    capsys: pytest.CaptureFixture[str],
) -> None:
    argv = ["assets", "image", "ork", "nosuchunit"]

    with pytest.raises(SystemExit):
        app(argv, exit_on_error=False, result_action="return_value")

    # Lists what the caller could have meant, rather than just rejecting it.
    err = capsys.readouterr().err
    assert "nosuchunit" in err
    assert "grunt" in err


def test_list_command_reports_coverage_for_one_race(
    registered_kind: Kind, capsys: pytest.CaptureFixture[str]
) -> None:
    generate(
        registered_kind,
        source="a grunt description",
        race="ork",
        name="grunt",
        count=2,
        candidates_root=config.paths.candidates,
    )
    promote(
        registered_kind,
        race="ork",
        name="grunt",
        pick="2",
        candidates_root=config.paths.candidates,
        assets_root=config.paths.assets,
    )

    app(
        ["assets", "list", "ork", "--kind", "_test"],
        exit_on_error=False,
        result_action="return_value",
    )

    out = capsys.readouterr().out
    assert "Ork" in out  # the race heading always prints
    grunt_line = next(line for line in out.splitlines() if "grunt" in line)
    assert "2 candidates" in grunt_line
    # Covered and uncovered read as a symmetric pair of glyphs, not a glyph
    # opposed to a word.
    assert "\N{CHECK MARK}" in grunt_line
    # A Target with neither Asset nor Candidates still gets a row.
    troll_line = next(line for line in out.splitlines() if "troll" in line)
    assert "\N{BALLOT X}" in troll_line


def test_list_command_expands_lineages_under_candidates(
    registered_kind: Kind, capsys: pytest.CaptureFixture[str]
) -> None:
    candidates = config.paths.candidates / "ork" / "_test"
    candidates.mkdir(parents=True)
    for lineage, content in [("10", b"a"), ("2", b"b"), ("4.1", b"chosen")]:
        (candidates / f"grunt.{lineage}.txt").write_bytes(content)
    promote(
        registered_kind,
        race="ork",
        name="grunt",
        pick="4.1",
        candidates_root=config.paths.candidates,
        assets_root=config.paths.assets,
    )

    app(
        ["assets", "list", "ork", "--kind", "_test", "--candidates"],
        exit_on_error=False,
        result_action="return_value",
    )

    out = capsys.readouterr().out
    lineage_line = next(
        line for line in out.splitlines() if line.strip().startswith("2")
    )
    # Numerically sorted: 10 sorts last, not straight after 1.
    assert [part.split()[0] for part in lineage_line.split(", ")] == ["2", "4.1", "10"]
    # The Asset is byte-identical to 4.1, so that is the one already promoted.
    assert "4.1 (promoted)" in lineage_line


@pytest.mark.usefixtures("registered_kind")
def test_list_command_without_a_race_covers_every_validating_race(
    capsys: pytest.CaptureFixture[str],
) -> None:
    app(
        ["assets", "list", "--kind", "_test"],
        exit_on_error=False,
        result_action="return_value",
    )

    out = capsys.readouterr().out
    # Full detail for every race, not a summary (D12).
    assert "Ork" in out
    assert "Goblin" in out
    assert "grunt" in out


def test_list_command_surfaces_orphans_under_unknown(
    registered_kind: Kind,  # noqa: ARG001  registers the _test kind and tmp roots
    capsys: pytest.CaptureFixture[str],
) -> None:
    assets = config.paths.assets / "ork" / "_test"
    assets.mkdir(parents=True)
    (assets / "gigant_snake_cavalry.txt").write_bytes(b"typo")

    app(
        ["assets", "list", "ork", "--kind", "_test"],
        exit_on_error=False,
        result_action="return_value",
    )

    out = capsys.readouterr().out
    assert "Unknown" in out
    assert "gigant_snake_cavalry.txt" in out


@pytest.mark.usefixtures("registered_kind")
def test_list_command_errors_on_an_explicitly_named_invalid_race(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    # The bare-race sweep omits a non-validating race silently (ADR 0004), but
    # naming one explicitly must say so rather than raise ValidationError.
    races_dir = tmp_path / "broken-races"
    races_dir.mkdir()
    (races_dir / "gnome.toml").write_text("[races.gnome]\nname = 123\n")
    monkeypatch.setattr(config.paths, "races", races_dir)

    with pytest.raises(SystemExit) as excinfo:
        app(
            ["assets", "list", "gnome", "--kind", "_test"],
            exit_on_error=False,
            result_action="return_value",
        )

    assert excinfo.value.code == 1
    assert "gnome" in capsys.readouterr().err


@pytest.mark.usefixtures("registered_kind")
def test_list_command_defaults_to_every_registered_kind(
    capsys: pytest.CaptureFixture[str],
) -> None:
    # An omitted --kind must not be run through the kind validator.
    app(["assets", "list", "ork"], exit_on_error=False, result_action="return_value")

    assert "Ork" in capsys.readouterr().out
