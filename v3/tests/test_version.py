"""Tests for the version seam: package metadata and the `--version` flag."""

import tomllib
from pathlib import Path

import pytest

from spf.frontends.cli import app
from spf.version import spf_version

PYPROJECT = Path(__file__).parent.parent / "pyproject.toml"


def test_spf_version_matches_pyproject() -> None:
    # `[project].version` is the single source of truth `bumpver` rewrites, so
    # a stale editable install shows up here rather than in a rendered document.
    declared = tomllib.loads(PYPROJECT.read_text(encoding="utf-8"))["project"]
    assert spf_version() == declared["version"]


def test_version_flag_prints_the_version(capsys: pytest.CaptureFixture[str]) -> None:
    app(["--version"], exit_on_error=False, result_action="return_value")

    assert spf_version() in capsys.readouterr().out
