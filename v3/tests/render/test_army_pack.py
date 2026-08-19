"""Tests for the Army Pack product: index, loader, view-model, CLI."""

import re
from pathlib import Path

import pytest
from pydantic import ValidationError

from spf.armies import io
from spf.armies.army import Army
from spf.armies.build import ArmyList
from spf.config import config
from spf.frontends.cli.render import ARMY_PACK, ARMY_RULES
from spf.render import render
from spf.render.army_pack import ArmyPack, PackEntry, build_pack
from spf.render.army_rules import build_reference
from spf.render.formats import get_format
from spf.render.images import no_image
from spf.render.products import PRODUCTS
from spf.schemas.army_pack import ArmyPackConfig, PackArmyConfig
from tests.render.conftest import FakeLookup

DEMO_ARMY = "demo"

VALID_INDEX = """\
title = "SPF 2025 Tournament"

[[armies]]
army = "geir_arne"
label = "Geir Arne"

[[armies]]
army = "morten"
"""


@pytest.fixture
def armies_dir(tmp_path: Path, *, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Redirect config.paths.armies to a temporary directory."""
    monkeypatch.setattr(config.paths, "armies", tmp_path)
    return tmp_path


def _save(name: str, *, race: str = "goblin", nick: str = "Test") -> None:
    io.save_army(
        ArmyList(race=race, nick=nick, units=[]),  # pyright: ignore[reportArgumentType]
        army_name=name,
    )


# --- The Army Pack Index schema ---------------------------------------------


def test_index_parses_a_valid_document() -> None:
    index = ArmyPackConfig(
        title="SPF 2025 Tournament",
        armies=[
            PackArmyConfig(army="geir_arne", label="Geir Arne"),
            PackArmyConfig(army="morten"),
        ],
    )

    assert index.title == "SPF 2025 Tournament"
    assert [entry.army for entry in index.armies] == ["geir_arne", "morten"]
    assert index.armies[0].label == "Geir Arne"
    assert index.armies[1].label is None


def test_index_requires_a_document_title() -> None:
    with pytest.raises(ValidationError, match="title"):
        ArmyPackConfig(armies=[])  # pyright: ignore[reportCallIssue]


def test_index_rejects_an_unknown_key() -> None:
    with pytest.raises(ValidationError, match="extra"):
        ArmyPackConfig(  # pyright: ignore[reportCallIssue]
            title="Test",
            armies=[],
            unexpected="nope",  # pyright: ignore[reportCallIssue]
        )


def test_index_rejects_an_unknown_key_on_an_entry() -> None:
    with pytest.raises(ValidationError, match="extra"):
        PackArmyConfig(army="geir_arne", nick="nope")  # pyright: ignore[reportCallIssue]


def test_get_army_pack_parses_a_toml_file(tmp_path: Path) -> None:
    path = tmp_path / "pack.toml"
    path.write_text(VALID_INDEX, encoding="utf-8")

    index = io.get_army_pack(path)

    assert index.title == "SPF 2025 Tournament"
    assert [entry.army for entry in index.armies] == ["geir_arne", "morten"]


# --- load_pack_armies: resolution, ordering, failures -----------------------


def test_load_pack_armies_resolves_relative_to_base_dir(armies_dir: Path) -> None:
    _save("geir_arne", nick="Geir Arne's Army")
    _save("morten", nick="Morten's Army")
    index = ArmyPackConfig(
        title="Test",
        armies=[
            PackArmyConfig(army="geir_arne", label="Geir Arne"),
            PackArmyConfig(army="morten"),
        ],
    )

    armies = io.load_pack_armies(index, base_dir=armies_dir)

    assert [label for label, _army in armies] == ["Geir Arne", None]
    assert [army.nick for _label, army in armies] == [
        "Geir Arne's Army",
        "Morten's Army",
    ]


def test_load_pack_armies_preserves_index_order(armies_dir: Path) -> None:
    _save("c", nick="C")
    _save("a", nick="A")
    _save("b", nick="B")
    index = ArmyPackConfig(
        title="Test",
        armies=[PackArmyConfig(army=n) for n in ("c", "a", "b")],
    )

    armies = io.load_pack_armies(index, base_dir=armies_dir)

    assert [army.nick for _label, army in armies] == ["C", "A", "B"]


def test_load_pack_armies_resolves_beside_the_index_not_the_committed_armies_dir(
    tmp_path: Path,
) -> None:
    # `base_dir` is a directory unrelated to `config.paths.armies` — proves
    # resolution follows the Index's own directory (ADR 0018), not the global
    # armies root.
    other = tmp_path / "elsewhere"
    other.mkdir()
    (other / "solo.json").write_text(
        '{"race": "goblin", "nick": "Elsewhere Army", "units": []}'
    )

    index = ArmyPackConfig(title="Test", armies=[PackArmyConfig(army="solo")])
    armies = io.load_pack_armies(index, base_dir=other)

    assert armies[0][1].nick == "Elsewhere Army"


def test_load_pack_armies_missing_army_names_army_and_position(
    armies_dir: Path,
) -> None:
    _save("geir_arne")
    index = ArmyPackConfig(
        title="Test",
        armies=[PackArmyConfig(army="geir_arne"), PackArmyConfig(army="morten")],
    )

    with pytest.raises(FileNotFoundError, match=r"Army 2 \('morten'\)"):
        io.load_pack_armies(index, base_dir=armies_dir)


def test_load_pack_armies_invalid_army_names_army_and_position(
    armies_dir: Path,
) -> None:
    (armies_dir / "bad.json").write_text('{"race": "nope", "nick": "x", "units": []}')
    index = ArmyPackConfig(title="Test", armies=[PackArmyConfig(army="bad")])

    with pytest.raises(ValueError, match=r"Army 1 \('bad'\)"):
        io.load_pack_armies(index, base_dir=armies_dir)


def test_load_pack_armies_invalid_entry_propagates_underlying_reason(
    armies_dir: Path,
) -> None:
    (armies_dir / "bad.json").write_text('{"race": "nope", "nick": "x", "units": []}')
    index = ArmyPackConfig(title="Test", armies=[PackArmyConfig(army="bad")])

    with pytest.raises(ValueError, match="could not be loaded: "):
        io.load_pack_armies(index, base_dir=armies_dir)


# --- build_pack: the view-model (no filesystem) ------------------------------


def _army(*, nick: str = "Test", race: str = "goblin") -> Army:
    return Army(race=race, nick=nick, units=[])  # pyright: ignore[reportArgumentType]


def test_build_pack_preserves_entry_order() -> None:
    armies = [(None, _army(nick="C")), (None, _army(nick="A")), (None, _army(nick="B"))]

    pack = build_pack(armies, title="Test Pack", stem="pack")

    assert [entry.label for entry in pack.entries] == ["C", "A", "B"]
    assert pack.title == "Test Pack"
    assert pack.stem == "pack"


def test_build_pack_label_overrides_the_nick() -> None:
    armies = [("Geir Arne", _army(nick="Showcase Dwarf"))]

    pack = build_pack(armies, title="Test", stem="pack")

    assert pack.entries[0].label == "Geir Arne"


def test_build_pack_absent_label_falls_back_to_nick() -> None:
    armies = [(None, _army(nick="Showcase Dwarf"))]

    pack = build_pack(armies, title="Test", stem="pack")

    assert pack.entries[0].label == "Showcase Dwarf"


def test_build_pack_keeps_two_armies_of_the_same_race_both_in_full() -> None:
    armies = [
        (None, _army(nick="Player A", race="goblin")),
        (None, _army(nick="Player B", race="goblin")),
    ]

    pack = build_pack(armies, title="Test", stem="pack")

    assert [entry.label for entry in pack.entries] == ["Player A", "Player B"]


def test_build_pack_entry_reference_matches_standalone_build_reference() -> None:
    army = _army(nick="Standalone")

    pack = build_pack([(None, army)], title="Test", stem="pack")
    standalone = build_reference(army, stem="pack")

    assert pack.entries[0].reference == standalone


def test_build_pack_passes_the_injected_image_lookup_through() -> None:
    lookup = FakeLookup(None)
    army = _army(nick="Test", race="goblin")

    build_pack([(None, army)], title="Test", stem="pack", image_for=lookup)

    assert ("goblin", "goblin") in lookup.calls


def test_build_pack_is_an_army_pack_of_pack_entries() -> None:
    pack = build_pack([(None, _army())], title="Test", stem="pack")

    assert isinstance(pack, ArmyPack)
    assert isinstance(pack.entries[0], PackEntry)


# --- Templates: army-pack renders through the shared reference-body --------


def _demo_pack(**labels: str | None) -> ArmyPack:
    armies = [(label, io.load_army(DEMO_ARMY)) for label in labels.values()] or [
        (None, io.load_army(DEMO_ARMY))
    ]
    return build_pack(armies, title="Test Pack", stem="pack", image_for=no_image)


def test_army_pack_product_is_registered() -> None:
    assert PRODUCTS["army-pack"] is ARMY_PACK


def test_army_pack_latex_has_one_section_per_army_and_a_toc(tmp_path: Path) -> None:
    pack = build_pack(
        [("Geir Arne", io.load_army(DEMO_ARMY)), ("Morten", io.load_army(DEMO_ARMY))],
        title="Test Pack",
        stem="pack",
        image_for=no_image,
    )

    out = render(
        ARMY_PACK, pack, fmt=get_format("latex"), name="pack", output_root=tmp_path
    )

    text = out.read_text(encoding="utf-8")
    assert text.count(r"\section{Geir Arne}") == 1
    assert text.count(r"\section{Morten}") == 1
    assert r"\tableofcontents" in text
    assert r"\clearpage" in text


def test_army_pack_latex_unit_markup_matches_standalone_army_rules(
    tmp_path: Path,
) -> None:
    # The strongest available check of the §2 invariant: the Pack's rendering
    # of a Unit is byte-identical to the Army Reference's, once the heading
    # command is normalised for the deeper nesting level.
    army = io.load_army(DEMO_ARMY)
    pack = build_pack(
        [(None, army)], title="Test Pack", stem="pack", image_for=no_image
    )
    reference = build_reference(army, stem="demo", image_for=no_image)

    pack_out = render(
        ARMY_PACK, pack, fmt=get_format("latex"), name="pack", output_root=tmp_path
    )
    reference_out = render(
        ARMY_RULES,
        reference,
        fmt=get_format("latex"),
        name="demo",
        output_root=tmp_path,
    )

    pack_text = pack_out.read_text(encoding="utf-8")
    reference_text = reference_out.read_text(encoding="utf-8")
    # Normalise the Pack's one-level-deeper sectioning back to the standalone
    # commands before comparing the unit/model/equipment markup itself. A
    # single regex pass (longest command first) avoids `\subsection` and
    # `\subsubsection` clobbering each other under sequential `str.replace`.
    shift_back = {
        r"\subsubsection": r"\subsection",
        r"\subsection": r"\section",
        r"\paragraph": r"\subsubsection",
    }
    normalised = re.sub(
        r"\\subsubsection|\\subsection|\\paragraph",
        lambda m: shift_back[m.group()],
        pack_text,
    )
    for line in reference_text.splitlines():
        if line.startswith((r"\section{", r"\subsection{", r"\subsubsection{")):
            assert line in normalised


def test_army_pack_markdown_has_one_heading_per_army_and_toc_anchors(
    tmp_path: Path,
) -> None:
    pack = build_pack(
        [("Geir Arne", io.load_army(DEMO_ARMY)), ("Morten", io.load_army(DEMO_ARMY))],
        title="Test Pack",
        stem="pack",
        image_for=no_image,
    )

    out = render(
        ARMY_PACK, pack, fmt=get_format("markdown"), name="pack", output_root=tmp_path
    )

    text = out.read_text(encoding="utf-8")
    assert "## Geir Arne" in text
    assert "## Morten" in text
    assert '<a id="geir-arne"></a>' in text
    assert '<a id="morten"></a>' in text
    assert "[Geir Arne](#geir-arne)" in text
    assert "[Morten](#morten)" in text
    # Units render one level below the per-army `##` heading.
    assert "### " in text


def test_army_pack_html_is_a_document(tmp_path: Path) -> None:
    pack = _demo_pack(a="Geir Arne")

    out = render(
        ARMY_PACK, pack, fmt=get_format("html"), name="pack", output_root=tmp_path
    )

    text = out.read_text(encoding="utf-8")
    assert "<!DOCTYPE html>" in text
    assert "Geir Arne" in text
