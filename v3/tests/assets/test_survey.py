"""The Survey: a Kind's Targets for a Race, checked against the two stores."""

from pathlib import Path

import pytest

from spf.assets import Kind, stage_promoted, survey


@pytest.fixture
def stores(tmp_path: Path) -> tuple[Path, Path]:
    """Return empty `(assets_root, candidates_root)` under tmp."""
    return tmp_path / "assets", tmp_path / "candidates"


def _write(root: Path, name: str, content: bytes = b"x") -> Path:
    """Write `content` to `<root>/ork/_test/<name>`, making parents."""
    path = root / "ork" / "_test" / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(content)
    return path


def test_survey_reports_one_row_per_target_with_its_asset(
    test_kind: Kind, stores: tuple[Path, Path]
) -> None:
    assets_root, _ = stores
    grunt_asset = _write(assets_root, "grunt.txt")

    found = survey(test_kind, "ork", assets_root=assets_root)

    by_name = {row.target.name: row for row in found.rows}
    assert by_name["grunt"].asset == grunt_asset
    assert by_name["ork_infantry"].asset is None
    # Rows follow targets() order: the race first, then units as declared.
    assert [row.target.name for row in found.rows][:2] == ["ork", "ork_infantry"]


def test_survey_lists_candidate_lineages_sorted_numerically(
    test_kind: Kind, stores: tuple[Path, Path]
) -> None:
    assets_root, candidates_root = stores
    for lineage in ["10", "2", "4.3", "4.1", "2.1", "4"]:
        _write(candidates_root, f"grunt.{lineage}.txt")

    found = survey(
        test_kind, "ork", assets_root=assets_root, candidates_root=candidates_root
    )

    by_name = {row.target.name: row for row in found.rows}
    # Dotted components sort as integers: 10 comes last, not after 1.
    assert by_name["grunt"].candidates == ["2", "2.1", "4", "4.1", "4.3", "10"]
    assert by_name["ork_infantry"].candidates == []


def test_survey_keeps_digits_that_belong_to_the_target_name(
    test_kind: Kind, stores: tuple[Path, Path]
) -> None:
    # `ork_char_b1` is a real ork unit key ending in a digit. Splitting on the
    # first dot, or treating the trailing "1" as a Lineage, would misfile these.
    assets_root, candidates_root = stores
    _write(candidates_root, "ork_char_b1.2.txt")
    _write(candidates_root, "ork_char_b1.4.1.txt")

    found = survey(
        test_kind, "ork", assets_root=assets_root, candidates_root=candidates_root
    )

    by_name = {row.target.name: row for row in found.rows}
    assert by_name["ork_char_b1"].candidates == ["2", "4.1"]


def test_survey_reports_asset_files_matching_no_target_as_orphans(
    test_kind: Kind, stores: tuple[Path, Path]
) -> None:
    # The real case this view exists to surface: a typo'd file name that no
    # longer matches any unit key, so it silently covers nothing.
    assets_root, candidates_root = stores
    _write(assets_root, "grunt.txt")
    typo = _write(assets_root, "gigant_snake_cavalry.txt")

    found = survey(
        test_kind, "ork", assets_root=assets_root, candidates_root=candidates_root
    )

    assert found.orphans == [typo]


def test_survey_recovers_which_candidate_was_promoted(
    test_kind: Kind, stores: tuple[Path, Path]
) -> None:
    assets_root, candidates_root = stores
    _write(candidates_root, "grunt.2.txt", b"the other one")
    _write(candidates_root, "grunt.4.1.txt", b"the chosen one")
    _write(assets_root, "grunt.txt", b"the chosen one")

    found = survey(
        test_kind,
        "ork",
        assets_root=assets_root,
        candidates_root=candidates_root,
        with_candidates=True,
    )

    by_name = {row.target.name: row for row in found.rows}
    assert by_name["grunt"].promoted_from == ["4.1"]


def test_survey_skips_provenance_unless_candidates_are_asked_for(
    test_kind: Kind, stores: tuple[Path, Path]
) -> None:
    # Hashing the Candidate store is the expensive part; the default listing
    # must not pay for it (ADR 0012).
    assets_root, candidates_root = stores
    _write(candidates_root, "grunt.2.txt", b"the chosen one")
    _write(assets_root, "grunt.txt", b"the chosen one")

    found = survey(
        test_kind, "ork", assets_root=assets_root, candidates_root=candidates_root
    )

    by_name = {row.target.name: row for row in found.rows}
    assert by_name["grunt"].promoted_from == []
    assert by_name["grunt"].candidates == ["2"]


def test_survey_reports_every_candidate_matching_the_asset(
    test_kind: Kind, stores: tuple[Path, Path]
) -> None:
    # Seeds are deterministic, so two Candidates can be byte-identical. Both are
    # reported rather than one guessed (ADR 0012).
    assets_root, candidates_root = stores
    _write(candidates_root, "grunt.2.txt", b"identical")
    _write(candidates_root, "grunt.5.txt", b"identical")
    _write(candidates_root, "grunt.3.txt", b"different")
    _write(assets_root, "grunt.txt", b"identical")

    found = survey(
        test_kind,
        "ork",
        assets_root=assets_root,
        candidates_root=candidates_root,
        with_candidates=True,
    )

    by_name = {row.target.name: row for row in found.rows}
    assert by_name["grunt"].promoted_from == ["2", "5"]


def test_survey_extends_orphans_to_candidates_when_asked(
    test_kind: Kind, stores: tuple[Path, Path]
) -> None:
    assets_root, candidates_root = stores
    stray = _write(candidates_root, "gigant_snake_cavalry.2.txt")
    _write(candidates_root, "grunt.2.txt")

    default = survey(
        test_kind, "ork", assets_root=assets_root, candidates_root=candidates_root
    )
    detailed = survey(
        test_kind,
        "ork",
        assets_root=assets_root,
        candidates_root=candidates_root,
        with_candidates=True,
    )

    # By default the Unknown section covers Assets only.
    assert default.orphans == []
    assert detailed.orphans == [stray]


def test_survey_recognizes_a_staged_promoted_asset_as_promoted(
    test_kind: Kind, stores: tuple[Path, Path]
) -> None:
    # `stage_promoted` is a plain copy, so the staged Candidate is
    # byte-identical to the Asset and `--candidates` renders it as
    # "N (promoted)" with no labelling code of its own (ADR 0012).
    assets_root, candidates_root = stores
    _write(assets_root, "grunt.txt", b"the committed asset")
    _write(candidates_root, "grunt.1.txt", b"something else")

    lineage = stage_promoted(
        test_kind,
        race="ork",
        name="grunt",
        candidates_root=candidates_root,
        assets_root=assets_root,
    )
    found = survey(
        test_kind,
        "ork",
        assets_root=assets_root,
        candidates_root=candidates_root,
        with_candidates=True,
    )

    by_name = {row.target.name: row for row in found.rows}
    assert lineage == "2"
    assert by_name["grunt"].promoted_from == [lineage]
