"""Tests for the version seam: package metadata and the `--version` flag."""

import tomllib
from importlib.metadata import PackageNotFoundError
from pathlib import Path

import pytest

from spf.frontends.cli import app
from spf.version import UNKNOWN_VERSION, spf_version

PYPROJECT = Path(__file__).parent.parent / "pyproject.toml"


def test_spf_version_matches_pyproject() -> None:
    # `[project].version` is the single source of truth `bumpver` rewrites, so
    # a stale editable install shows up here rather than in a rendered document.
    declared = tomllib.loads(PYPROJECT.read_text(encoding="utf-8"))["project"]
    assert spf_version() == declared["version"]


def test_version_flag_prints_the_version(capsys: pytest.CaptureFixture[str]) -> None:
    app(["--version"], exit_on_error=False, result_action="return_value")

    assert spf_version() in capsys.readouterr().out


def test_spf_version_falls_back_without_installed_metadata(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # Rendering resolves the version through this call, so an uninstalled
    # source tree must degrade to a placeholder rather than fail every render.
    def missing(name: str) -> str:
        raise PackageNotFoundError(name)

    monkeypatch.setattr("spf.version.version", missing)

    assert spf_version() == UNKNOWN_VERSION
