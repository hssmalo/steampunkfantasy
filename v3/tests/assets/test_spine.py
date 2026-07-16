"""S2 + S3: the generate and promote spine functions."""

from pathlib import Path

import pytest

from spf.assets import Kind, generate, promote
from tests.assets.conftest import FakeService


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
    kind = Kind(name="_seedy", service=service, subdir="_test", extension="txt")
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
        pick=2,
        candidates_root=candidates,
        assets_root=store,
    )
    assert asset == store / "orks" / "_test" / "grunt.txt"
    assert asset.read_bytes() == b"two"


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
            pick=99,
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
        pick=1,
        candidates_root=candidates,
        assets_root=store,
    )
    asset = promote(
        test_kind,
        race="orks",
        name="grunt",
        pick=3,
        candidates_root=candidates,
        assets_root=store,
    )
    assert asset.read_bytes() == b"three"
