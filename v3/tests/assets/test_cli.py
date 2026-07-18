"""S5: the shared `spf assets promote` CLI command over a throwaway kind."""

from pathlib import Path

import pytest
from cyclopts.exceptions import CycloptsError

from spf.assets import Kind, generate
from spf.assets.kinds import KINDS
from spf.config import config
from spf.frontends.cli import app
from tests.assets.conftest import FakeService


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
