"""Tests for spf.assets.profiles: pure filesystem discovery and resolution."""

from pathlib import Path

import pytest

from spf.assets.profiles import (
    available,
    check,
    describe,
    resolve,
    resolve_refine,
)


def _touch(root: Path, *rel: str) -> None:
    for r in rel:
        p = root / r
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text("{}")


def _workflows(tmp_path: Path) -> tuple[Path, Path]:
    project = tmp_path / "project"
    workflows = project / "workflows"
    return workflows, project


def test_available_returns_sorted_profile_names(tmp_path: Path) -> None:
    workflows, _ = _workflows(tmp_path)
    _touch(workflows, "cloud/qwen.json", "cloud/krea2.json", "cloud/alpha.json")
    assert available(workflows, "cloud") == ["alpha", "krea2", "qwen"]


def test_available_excludes_refine_workflows(tmp_path: Path) -> None:
    workflows, _ = _workflows(tmp_path)
    _touch(workflows, "cloud/qwen.json", "cloud/qwen-refine.json")
    assert available(workflows, "cloud") == ["qwen"]


def test_available_excludes_non_json(tmp_path: Path) -> None:
    workflows, _ = _workflows(tmp_path)
    _touch(workflows, "cloud/qwen.json", "cloud/notes.txt", "cloud/.gitkeep")
    assert available(workflows, "cloud") == ["qwen"]


def test_available_returns_empty_when_directory_missing(tmp_path: Path) -> None:
    workflows, _ = _workflows(tmp_path)
    assert available(workflows, "cloud") == []


def test_available_returns_empty_when_directory_empty(tmp_path: Path) -> None:
    workflows, _ = _workflows(tmp_path)
    (workflows / "cloud").mkdir(parents=True)
    assert available(workflows, "cloud") == []


def test_available_never_scans_examples(tmp_path: Path) -> None:
    workflows, _ = _workflows(tmp_path)
    _touch(workflows, "examples/qwen.json")
    assert available(workflows, "examples") == []


def test_resolve_returns_generate_workflow_path(tmp_path: Path) -> None:
    workflows, project = _workflows(tmp_path)
    _touch(workflows, "cloud/qwen.json")
    result = resolve(workflows, "cloud", "qwen", project_root=project)
    assert result == workflows / "cloud" / "qwen.json"


def test_resolve_raises_for_unknown_profile(tmp_path: Path) -> None:
    workflows, project = _workflows(tmp_path)
    _touch(workflows, "cloud/qwen.json", "cloud/krea2.json")
    with pytest.raises(
        ValueError,
        match=r"unknown profile 'krea3'.*available: krea2, qwen",
    ):
        resolve(workflows, "cloud", "krea3", project_root=project)


def test_resolve_raises_when_env_directory_missing(tmp_path: Path) -> None:
    workflows, project = _workflows(tmp_path)
    with pytest.raises(
        ValueError,
        match=r"no workflows for env 'local'.*workflows/local/",
    ):
        resolve(workflows, "local", "qwen", project_root=project)


def test_resolve_raises_when_env_directory_empty(tmp_path: Path) -> None:
    workflows, project = _workflows(tmp_path)
    (workflows / "local").mkdir(parents=True)
    with pytest.raises(
        ValueError,
        match=r"no workflows for env 'local'.*workflows/local/",
    ):
        resolve(workflows, "local", "qwen", project_root=project)


def test_resolve_error_shows_project_relative_path(tmp_path: Path) -> None:
    workflows, project = _workflows(tmp_path)
    with pytest.raises(ValueError, match="workflows/local/"):
        resolve(workflows, "local", "qwen", project_root=project)


def test_resolve_refine_returns_refine_workflow_path(tmp_path: Path) -> None:
    workflows, project = _workflows(tmp_path)
    _touch(workflows, "cloud/qwen.json", "cloud/qwen-refine.json")
    result = resolve_refine(workflows, "cloud", "qwen", project_root=project)
    assert result == workflows / "cloud" / "qwen-refine.json"


def test_resolve_refine_raises_when_refine_workflow_missing(
    tmp_path: Path,
) -> None:
    workflows, project = _workflows(tmp_path)
    _touch(workflows, "cloud/qwen.json")
    with pytest.raises(
        ValueError,
        match=r"profile 'qwen' has no refine workflow.*qwen-refine\.json",
    ):
        resolve_refine(workflows, "cloud", "qwen", project_root=project)


def test_resolve_refine_error_shows_project_relative_path(tmp_path: Path) -> None:
    workflows, project = _workflows(tmp_path)
    _touch(workflows, "local/qwen.json")
    with pytest.raises(ValueError, match=r"workflows/local/qwen-refine\.json"):
        resolve_refine(workflows, "local", "qwen", project_root=project)


def test_check_reports_ok_when_the_configured_profile_resolves(
    tmp_path: Path,
) -> None:
    workflows, project = _workflows(tmp_path)
    _touch(workflows, "cloud/qwen.json")
    status = check(workflows, "cloud", "qwen", project_root=project)
    assert status.state == "ok"
    assert status.detail == "workflows/cloud/qwen.json"


def test_check_reports_broken_when_the_profile_is_missing(tmp_path: Path) -> None:
    workflows, project = _workflows(tmp_path)
    _touch(workflows, "cloud/krea2.json")
    status = check(workflows, "cloud", "qwen", project_root=project)
    assert status.state == "broken"
    assert "krea2" in status.detail  # names what the env does offer


def test_check_skips_an_env_not_set_up_on_this_machine(tmp_path: Path) -> None:
    workflows, project = _workflows(tmp_path)
    _touch(workflows, "cloud/qwen.json")
    # `workflows/local/` is per-machine and gitignored, so its absence is a
    # fact about the machine, not a broken configuration.
    status = check(workflows, "local", "qwen", project_root=project)
    assert status.state == "not-set-up"


def test_check_skips_an_env_directory_that_offers_no_profiles(tmp_path: Path) -> None:
    workflows, project = _workflows(tmp_path)
    (workflows / "local").mkdir(parents=True)
    # Created but not yet populated: still a fact about the machine.
    status = check(workflows, "local", "qwen", project_root=project)
    assert status.state == "not-set-up"


def test_describe_lists_every_profile_in_the_env(tmp_path: Path) -> None:
    workflows, project = _workflows(tmp_path)
    _touch(workflows, "local/qwen.json", "local/krea2.json")

    report = describe(workflows, "local", "qwen", project_root=project)

    assert [p.name for p in report.profiles] == ["krea2", "qwen"]


def test_describe_marks_the_configured_profile(tmp_path: Path) -> None:
    workflows, project = _workflows(tmp_path)
    _touch(workflows, "local/qwen.json", "local/krea2.json")

    report = describe(workflows, "local", "qwen", project_root=project)

    assert [p.name for p in report.profiles if p.configured] == ["qwen"]


def test_describe_flags_a_profile_without_a_refine_workflow(tmp_path: Path) -> None:
    workflows, project = _workflows(tmp_path)
    _touch(workflows, "local/qwen.json", "local/qwen-refine.json", "local/krea2.json")

    report = describe(workflows, "local", "qwen", project_root=project)

    assert {p.name: p.has_refine for p in report.profiles} == {
        "qwen": True,
        "krea2": False,
    }


def test_describe_reports_an_env_that_is_not_set_up(tmp_path: Path) -> None:
    workflows, project = _workflows(tmp_path)
    _touch(workflows, "cloud/qwen.json")

    report = describe(workflows, "local", "qwen", project_root=project)

    assert report.status.state == "not-set-up"
    assert report.profiles == []
