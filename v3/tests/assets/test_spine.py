"""S2 + S3: the generate and promote spine functions."""

from pathlib import Path

import pytest

from spf.assets import Kind, generate, promote, refine, stage_promoted
from tests.assets.conftest import FakeRefiner, FakeService


def test_generate_writes_n_candidates_at_kind_layout(
    tmp_path: Path, test_kind: Kind
) -> None:
    paths = generate(
        test_kind,
        source="a grunt description",
        race="orks",
        name="grunt",
        count=3,
        candidates_root=tmp_path,
    )
    assert paths == [
        tmp_path / "orks" / "_test" / "grunt.1.txt",
        tmp_path / "orks" / "_test" / "grunt.2.txt",
        tmp_path / "orks" / "_test" / "grunt.3.txt",
    ]
    assert [p.read_bytes() for p in paths] == [b"one", b"two", b"three"]


def test_generate_persists_each_candidate_before_reporting_it(
    tmp_path: Path, test_kind: Kind
) -> None:
    # on_candidate fires per file, in order, with the bytes already on disk —
    # proving Candidates are saved incrementally, not as a final batch.
    seen: list[tuple[Path, bytes]] = []
    generate(
        test_kind,
        source="a grunt description",
        race="orks",
        name="grunt",
        count=3,
        candidates_root=tmp_path,
        on_candidate=lambda path: seen.append((path, path.read_bytes())),
    )
    base = tmp_path / "orks" / "_test"
    assert seen == [
        (base / "grunt.1.txt", b"one"),
        (base / "grunt.2.txt", b"two"),
        (base / "grunt.3.txt", b"three"),
    ]


def test_generate_threads_seed_to_service(tmp_path: Path) -> None:
    service = FakeService()
    kind = Kind(
        name="_seedy",
        service=service,
        subdir="_test",
        extension="txt",
        targets=frozenset({"race", "unit"}),
    )
    generate(
        kind,
        source="a grunt description",
        race="orks",
        name="grunt",
        count=2,
        seed=7,
        candidates_root=tmp_path,
    )
    assert service.seen_seed == 7


def test_generate_honors_count(tmp_path: Path, test_kind: Kind) -> None:
    paths = generate(
        test_kind,
        source="a grunt description",
        race="orks",
        name="grunt",
        count=2,
        candidates_root=tmp_path,
    )
    assert len(paths) == 2


def test_generate_without_subdir_writes_flat_text(tmp_path: Path) -> None:
    lore_kind = Kind(
        name="_lore",
        service=FakeService(values=("chapter one", "chapter two")),
        subdir=None,
        extension="md",
        targets=frozenset({"race"}),
    )
    paths = generate(
        lore_kind,
        source="a grunt description",
        race="orks",
        name="lore",
        count=2,
        candidates_root=tmp_path,
    )
    assert paths == [
        tmp_path / "orks" / "lore.1.md",
        tmp_path / "orks" / "lore.2.md",
    ]
    assert paths[0].read_text(encoding="utf-8") == "chapter one"


def test_promote_copies_picked_candidate_into_store(
    tmp_path: Path, test_kind: Kind
) -> None:
    candidates = tmp_path / "candidates"
    store = tmp_path / "assets"
    generate(
        test_kind,
        source="a grunt description",
        race="orks",
        name="grunt",
        count=3,
        candidates_root=candidates,
    )
    asset = promote(
        test_kind,
        race="orks",
        name="grunt",
        pick="2",
        candidates_root=candidates,
        assets_root=store,
    )
    assert asset == store / "orks" / "_test" / "grunt.txt"
    assert asset.read_bytes() == b"two"


def test_promote_picks_a_dotted_lineage_candidate(
    tmp_path: Path, test_kind: Kind
) -> None:
    # A Refinement's Candidates carry a dotted Lineage index; promoting one
    # still writes the plain `<name>.<extension>` Asset.
    candidates = tmp_path / "candidates" / "orks" / "_test"
    candidates.mkdir(parents=True)
    (candidates / "grunt.2.1.txt").write_bytes(b"refined")
    asset = promote(
        test_kind,
        race="orks",
        name="grunt",
        pick="2.1",
        candidates_root=tmp_path / "candidates",
        assets_root=tmp_path / "assets",
    )
    assert asset == tmp_path / "assets" / "orks" / "_test" / "grunt.txt"
    assert asset.read_bytes() == b"refined"


@pytest.mark.parametrize(
    "pick", ["", "0", "2.", ".1", "2..1", "2.0", "a", "2.1a", "-1"]
)
def test_promote_rejects_a_malformed_lineage(
    tmp_path: Path, test_kind: Kind, pick: str
) -> None:
    # A typo fails naming the Lineage, not as a confusing missing-file error.
    with pytest.raises(ValueError, match=r"[Ll]ineage"):
        promote(
            test_kind,
            race="orks",
            name="grunt",
            pick=pick,
            candidates_root=tmp_path / "candidates",
            assets_root=tmp_path / "assets",
        )


def test_promote_missing_candidate_raises(tmp_path: Path, test_kind: Kind) -> None:
    generate(
        test_kind,
        source="a grunt description",
        race="orks",
        name="grunt",
        count=3,
        candidates_root=tmp_path / "candidates",
    )
    with pytest.raises(ValueError, match="candidate"):
        promote(
            test_kind,
            race="orks",
            name="grunt",
            pick="99",
            candidates_root=tmp_path / "candidates",
            assets_root=tmp_path / "assets",
        )


def test_promote_overwrites_existing_asset_silently(
    tmp_path: Path, test_kind: Kind
) -> None:
    candidates = tmp_path / "candidates"
    store = tmp_path / "assets"
    generate(
        test_kind,
        source="a grunt description",
        race="orks",
        name="grunt",
        count=3,
        candidates_root=candidates,
    )
    promote(
        test_kind,
        race="orks",
        name="grunt",
        pick="1",
        candidates_root=candidates,
        assets_root=store,
    )
    asset = promote(
        test_kind,
        race="orks",
        name="grunt",
        pick="3",
        candidates_root=candidates,
        assets_root=store,
    )
    assert asset.read_bytes() == b"three"


# --- refine: generating from an existing Candidate --------------------------


def _seed_candidate(
    root: Path, lineage: str = "2", body: bytes = b"the original"
) -> Path:
    """Write a Candidate to refine from, at the test kind's layout."""
    path = root / "orks" / "_test" / f"grunt.{lineage}.txt"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(body)
    return path


def test_refine_writes_candidates_under_the_lineage_derived_name(
    tmp_path: Path, refinable_kind: Kind
) -> None:
    _seed_candidate(tmp_path)

    paths = refine(
        refinable_kind,
        source="make the hat brass",
        race="orks",
        name="grunt",
        lineage="2",
        count=3,
        candidates_root=tmp_path,
    )

    # Refining candidate 2 generates under the derived name "grunt.2", so the
    # Lineage reads straight off the filename.
    base = tmp_path / "orks" / "_test"
    assert paths == [
        base / "grunt.2.1.txt",
        base / "grunt.2.2.txt",
        base / "grunt.2.3.txt",
    ]
    assert [p.read_bytes() for p in paths] == [b"one", b"two", b"three"]


def test_refine_leaves_the_source_candidate_untouched(
    tmp_path: Path, refinable_kind: Kind
) -> None:
    # The whole point is being able to fall back when a nudge came out worse.
    source = _seed_candidate(tmp_path)

    refine(
        refinable_kind,
        source="make the hat brass",
        race="orks",
        name="grunt",
        lineage="2",
        count=2,
        candidates_root=tmp_path,
    )

    assert source.read_bytes() == b"the original"


def test_refine_chains_on_an_already_refined_candidate(
    tmp_path: Path, refinable_kind: Kind
) -> None:
    _seed_candidate(tmp_path, lineage="2.1")

    paths = refine(
        refinable_kind,
        source="now make the boots brass too",
        race="orks",
        name="grunt",
        lineage="2.1",
        count=1,
        candidates_root=tmp_path,
    )

    assert paths == [tmp_path / "orks" / "_test" / "grunt.2.1.1.txt"]


def test_refine_hands_the_service_the_candidate_bytes_and_correction(
    tmp_path: Path, refinable_kind: Kind
) -> None:
    _seed_candidate(tmp_path, body=b"the candidate's own bytes")

    refine(
        refinable_kind,
        source="make the hat brass",
        race="orks",
        name="grunt",
        lineage="2",
        count=1,
        seed=7,
        candidates_root=tmp_path,
    )

    service = refinable_kind.service
    assert isinstance(service, FakeRefiner)
    assert service.seen_init == b"the candidate's own bytes"
    assert service.seen_source == "make the hat brass"  # verbatim, no wrapper
    assert service.seen_seed == 7


def test_refine_persists_each_candidate_before_reporting_it(
    tmp_path: Path, refinable_kind: Kind
) -> None:
    _seed_candidate(tmp_path)
    seen: list[tuple[Path, bytes]] = []

    refine(
        refinable_kind,
        source="make the hat brass",
        race="orks",
        name="grunt",
        lineage="2",
        count=2,
        candidates_root=tmp_path,
        on_candidate=lambda path: seen.append((path, path.read_bytes())),
    )

    base = tmp_path / "orks" / "_test"
    assert seen == [
        (base / "grunt.2.1.txt", b"one"),
        (base / "grunt.2.2.txt", b"two"),
    ]


def test_refine_rejects_a_missing_source_candidate(
    tmp_path: Path, refinable_kind: Kind
) -> None:
    with pytest.raises(ValueError, match=r"grunt\.9\.txt"):
        refine(
            refinable_kind,
            source="make the hat brass",
            race="orks",
            name="grunt",
            lineage="9",
            count=1,
            candidates_root=tmp_path,
        )


def test_refine_rejects_a_malformed_lineage(
    tmp_path: Path, refinable_kind: Kind
) -> None:
    with pytest.raises(ValueError, match="Malformed lineage"):
        refine(
            refinable_kind,
            source="make the hat brass",
            race="orks",
            name="grunt",
            lineage="2..1",
            count=1,
            candidates_root=tmp_path,
        )


# --- kinds whose Service cannot refine --------------------------------------


def test_refine_rejects_a_kind_whose_service_cannot_refine(
    tmp_path: Path, test_kind: Kind
) -> None:
    # test_kind's FakeService only generates, like the Lore and Model kinds.
    _seed_candidate(tmp_path)

    with pytest.raises(TypeError, match=r"_test.*does not support refinement"):
        refine(
            test_kind,
            source="make the hat brass",
            race="orks",
            name="grunt",
            lineage="2",
            count=1,
            candidates_root=tmp_path,
        )


# --- candidate indices are allocated past what is already on disk -----------


def test_generate_twice_appends_rather_than_overwriting(
    tmp_path: Path, test_kind: Kind
) -> None:
    # The bug this repeals: a second run used to restart at 1 and silently
    # clobber the first run's Candidates.
    first = generate(
        test_kind,
        source="a grunt description",
        race="orks",
        name="grunt",
        count=3,
        candidates_root=tmp_path,
    )
    second = generate(
        test_kind,
        source="a grunt description",
        race="orks",
        name="grunt",
        count=3,
        candidates_root=tmp_path,
    )

    base = tmp_path / "orks" / "_test"
    assert second == [
        base / "grunt.4.txt",
        base / "grunt.5.txt",
        base / "grunt.6.txt",
    ]
    assert [p.read_bytes() for p in first] == [b"one", b"two", b"three"]


def test_generate_reserves_a_deleted_parent_of_a_surviving_refinement(
    tmp_path: Path, test_kind: Kind
) -> None:
    # The adoption guard. `grunt.4` is gone but its refinement `grunt.4.1`
    # survives, so 4 stays taken: a new Candidate landing on 4 would silently
    # adopt an orphan derived from different bytes, and `promote --pick 4.1`
    # would hand back an image from a parent that no longer exists.
    base = tmp_path / "orks" / "_test"
    base.mkdir(parents=True)
    (base / "grunt.4.1.txt").write_bytes(b"an orphaned refinement")

    paths = generate(
        test_kind,
        source="a grunt description",
        race="orks",
        name="grunt",
        count=1,
        candidates_root=tmp_path,
    )

    assert paths == [base / "grunt.5.txt"]


def test_generate_does_not_fill_gaps(tmp_path: Path, test_kind: Kind) -> None:
    base = tmp_path / "orks" / "_test"
    base.mkdir(parents=True)
    (base / "grunt.1.txt").write_bytes(b"kept")
    (base / "grunt.3.txt").write_bytes(b"kept")

    paths = generate(
        test_kind,
        source="a grunt description",
        race="orks",
        name="grunt",
        count=1,
        candidates_root=tmp_path,
    )

    assert paths == [base / "grunt.4.txt"]


def test_generate_ignores_a_prefix_sibling_target(
    tmp_path: Path, test_kind: Kind
) -> None:
    # `grunt_carrier` is a different Target that merely starts with `grunt`.
    # The `.` separator keeps the two apart.
    base = tmp_path / "orks" / "_test"
    base.mkdir(parents=True)
    (base / "grunt_carrier.9.txt").write_bytes(b"another target")

    paths = generate(
        test_kind,
        source="a grunt description",
        race="orks",
        name="grunt",
        count=1,
        candidates_root=tmp_path,
    )

    assert paths == [base / "grunt.1.txt"]


def test_refining_the_same_candidate_twice_continues_the_numbering(
    tmp_path: Path, refinable_kind: Kind
) -> None:
    _seed_candidate(tmp_path)

    refine(
        refinable_kind,
        source="make the hat brass",
        race="orks",
        name="grunt",
        lineage="2",
        count=2,
        candidates_root=tmp_path,
    )
    second = refine(
        refinable_kind,
        source="now make the boots brass",
        race="orks",
        name="grunt",
        lineage="2",
        count=2,
        candidates_root=tmp_path,
    )

    base = tmp_path / "orks" / "_test"
    assert second == [base / "grunt.2.3.txt", base / "grunt.2.4.txt"]


# --- staging a promoted Asset back as a Candidate ---------------------------


def test_stage_promoted_copies_the_asset_into_the_candidate_store(
    tmp_path: Path, test_kind: Kind
) -> None:
    candidates = tmp_path / "candidates"
    store = tmp_path / "assets"
    asset = store / "orks" / "_test" / "grunt.txt"
    asset.parent.mkdir(parents=True)
    asset.write_bytes(b"the committed asset")

    lineage = stage_promoted(
        test_kind,
        race="orks",
        name="grunt",
        candidates_root=candidates,
        assets_root=store,
    )

    assert lineage == "1"
    staged = candidates / "orks" / "_test" / "grunt.1.txt"
    assert staged.read_bytes() == b"the committed asset"


def test_stage_promoted_takes_the_next_free_index(
    tmp_path: Path, test_kind: Kind
) -> None:
    candidates = tmp_path / "candidates"
    store = tmp_path / "assets"
    asset = store / "orks" / "_test" / "grunt.txt"
    asset.parent.mkdir(parents=True)
    asset.write_bytes(b"the committed asset")
    generate(
        test_kind,
        source="a grunt description",
        race="orks",
        name="grunt",
        count=3,
        candidates_root=candidates,
    )

    lineage = stage_promoted(
        test_kind,
        race="orks",
        name="grunt",
        candidates_root=candidates,
        assets_root=store,
    )

    assert lineage == "4"


def test_stage_promoted_without_an_asset_raises(
    tmp_path: Path, test_kind: Kind
) -> None:
    with pytest.raises(ValueError, match="asset"):
        stage_promoted(
            test_kind,
            race="orks",
            name="grunt",
            candidates_root=tmp_path / "candidates",
            assets_root=tmp_path / "assets",
        )


def test_promote_then_stage_promoted_round_trips_the_bytes(
    tmp_path: Path, test_kind: Kind
) -> None:
    candidates = tmp_path / "candidates"
    store = tmp_path / "assets"
    generate(
        test_kind,
        source="a grunt description",
        race="orks",
        name="grunt",
        count=3,
        candidates_root=candidates,
    )
    promote(
        test_kind,
        race="orks",
        name="grunt",
        pick="2",
        candidates_root=candidates,
        assets_root=store,
    )

    lineage = stage_promoted(
        test_kind,
        race="orks",
        name="grunt",
        candidates_root=candidates,
        assets_root=store,
    )

    base = candidates / "orks" / "_test"
    assert lineage == "4"
    assert (base / f"grunt.{lineage}.txt").read_bytes() == (
        base / "grunt.2.txt"
    ).read_bytes()
