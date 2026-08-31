"""Tests for the Army Pack product: index, loader, view-model, CLI."""

import re
import shutil
from pathlib import Path

import pytest
from pydantic import ValidationError

from spf.armies import io
from spf.armies.army import Army
from spf.armies.build import ArmyList
from spf.config import config
from spf.frontends.cli.render import ARMY_PACK, ARMY_RULES, RenderOpts, render_army_pack
from spf.render import render
from spf.render.army_pack import ArmyPack, PackEntry, build_pack
from spf.render.army_rules import build_reference
from spf.render.formats import get_format
from spf.render.images import no_image
from spf.render.products import PRODUCTS
from spf.schemas.army_pack import ArmyPackConfig, PackArmyConfig
from tests.conftest import unwrapped
from tests.render.conftest import FakeLookup

DEMO_ARMY = "demo"
ENGINE = config.render.latex.engine

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


def test_build_pack_label_is_combined_with_the_nick() -> None:
    armies = [("Geir Arne", _army(nick="Showcase Dwarf"))]

    pack = build_pack(armies, title="Test", stem="pack")

    assert pack.entries[0].label == "Geir Arne: Showcase Dwarf"


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
    assert text.count(r"\section{Geir Arne: The Iron Claws}") == 1
    assert text.count(r"\section{Morten: The Iron Claws}") == 1
    assert r"\tableofcontents" in text
    assert r"\clearpage" in text


def test_army_pack_latex_unit_markup_matches_standalone_army_rules(
    tmp_path: Path,
) -> None:
    # The strongest available check that the Pack and the standalone Army
    # Reference share one body template: the Pack's rendering of a Unit is
    # byte-identical to the Army Reference's, once the heading command is
    # normalized for the deeper nesting level.
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
    # Normalize the Pack's one-level-deeper sectioning back to the standalone
    # commands before comparing the unit/model/equipment markup itself. A
    # single regex pass (longest command first) avoids `\subsection` and
    # `\subsubsection` clobbering each other under sequential `str.replace`.
    shift_back = {
        r"\subsubsection": r"\subsection",
        r"\subsection": r"\section",
        r"\paragraph": r"\subsubsection",
    }
    normalized = re.sub(
        r"\\subsubsection|\\subsection|\\paragraph",
        lambda m: shift_back[m.group()],
        pack_text,
    )
    for line in reference_text.splitlines():
        if line.startswith((r"\section{", r"\subsection{", r"\subsubsection{")):
            assert line in normalized


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
    assert "## Geir Arne: The Iron Claws" in text
    assert "## Morten: The Iron Claws" in text
    assert '<a id="geir-arne-the-iron-claws"></a>' in text
    assert '<a id="morten-the-iron-claws"></a>' in text
    assert "[Geir Arne: The Iron Claws](#geir-arne-the-iron-claws)" in text
    assert "[Morten: The Iron Claws](#morten-the-iron-claws)" in text
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


# --- Images: ADR 0017 relative paths, at the Army Pack's own output depth --


def test_army_pack_markdown_image_paths_are_relative_to_its_own_output_dir(
    tmp_path: Path,
) -> None:
    # `output/army-pack/` sits at the same depth as `output/army-rules/`, so a
    # committed Asset resolves the same way relative to either.
    art = tmp_path / "assets" / "art.png"
    army = io.load_army(DEMO_ARMY)
    lookup = FakeLookup(art)
    pack = build_pack(
        [("Geir Arne", army)], title="Test Pack", stem="pack", image_for=lookup
    )

    out = render(
        ARMY_PACK, pack, fmt=get_format("markdown"), name="pack", output_root=tmp_path
    )

    text = out.read_text(encoding="utf-8")
    assert "](../assets/art.png)" in text


def test_army_pack_no_images_omits_committed_art(tmp_path: Path) -> None:
    army = io.load_army(DEMO_ARMY)
    lookup = FakeLookup(tmp_path / "assets" / "art.png")
    with_art = build_pack(
        [("Geir Arne", army)], title="Test Pack", stem="pack", image_for=lookup
    )
    without_art = build_pack(
        [("Geir Arne", army)], title="Test Pack", stem="pack", image_for=no_image
    )

    with_out = render(
        ARMY_PACK,
        with_art,
        fmt=get_format("markdown"),
        name="with-art",
        output_root=tmp_path,
    )
    without_out = render(
        ARMY_PACK,
        without_art,
        fmt=get_format("markdown"),
        name="without-art",
        output_root=tmp_path,
    )

    assert "![" in with_out.read_text(encoding="utf-8")
    assert "![" not in without_out.read_text(encoding="utf-8")


# --- The CLI ------------------------------------------------------------


def _write_pack_dir(tmp_path: Path) -> Path:
    """Write a pack directory with two Army JSON files and an Index."""
    pack_dir = tmp_path / "2025"
    pack_dir.mkdir()
    (pack_dir / "geir_arne.json").write_text(
        '{"race": "goblin", "nick": "Geir Arne\'s Army", "units": []}'
    )
    (pack_dir / "morten.json").write_text(
        '{"race": "goblin", "nick": "Morten\'s Army", "units": []}'
    )
    (pack_dir / "pack.toml").write_text(
        'title = "SPF 2025 Tournament"\n\n'
        '[[armies]]\narmy = "geir_arne"\nlabel = "Geir Arne"\n\n'
        '[[armies]]\narmy = "morten"\n',
        encoding="utf-8",
    )
    return pack_dir / "pack.toml"


def test_cli_index_mode_writes_the_pack(tmp_path: Path) -> None:
    index = _write_pack_dir(tmp_path)
    out = tmp_path / "out" / "pack.md"

    render_army_pack(index=index, opts=RenderOpts(format="markdown", out=out))

    text = out.read_text(encoding="utf-8")
    assert "# SPF 2025 Tournament" in text
    assert "## Geir Arne: Geir Arne's Army" in text
    assert "## Morten's Army" in text


def test_cli_ad_hoc_mode_uses_army_nicks_and_default_title(tmp_path: Path) -> None:
    out = tmp_path / "pack.md"

    render_army_pack(DEMO_ARMY, opts=RenderOpts(format="markdown", out=out))

    text = out.read_text(encoding="utf-8")
    assert "# Army Pack" in text
    assert "## The Iron Claws" in text  # demo Army's Nick: ad-hoc mode gives no Label


def test_cli_stem_defaults_to_the_index_parent_directory_name(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    index = _write_pack_dir(tmp_path)
    monkeypatch.setattr(config.paths, "output", tmp_path / "output")

    render_army_pack(index=index, opts=RenderOpts(format="markdown"))

    assert (tmp_path / "output" / "army-pack" / "2025.md").exists()


def test_cli_stem_from_a_bare_relative_index_uses_the_resolved_directory(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # A bare relative `--index pack.toml` has a `.parent` of `.`, whose `.name`
    # is empty — the stem must come from the *resolved* directory, not fall
    # through to a hidden `output/army-pack/.md`.
    index_path = _write_pack_dir(tmp_path)
    monkeypatch.setattr(config.paths, "output", tmp_path / "output")
    monkeypatch.chdir(index_path.parent)

    render_army_pack(index=Path("pack.toml"), opts=RenderOpts(format="markdown"))

    assert (tmp_path / "output" / "army-pack" / "2025.md").exists()
    assert not (tmp_path / "output" / "army-pack" / ".md").exists()


def test_cli_stem_defaults_to_army_pack_in_ad_hoc_mode(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(config.paths, "output", tmp_path / "output")

    render_army_pack(DEMO_ARMY, opts=RenderOpts(format="markdown"))

    assert (tmp_path / "output" / "army-pack" / "army-pack.md").exists()


def test_cli_rejects_both_index_and_army_names(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    index = _write_pack_dir(tmp_path)

    with pytest.raises(SystemExit) as excinfo:
        render_army_pack(DEMO_ARMY, index=index)

    assert excinfo.value.code == 1
    assert "exactly one of" in unwrapped(capsys.readouterr().err)


def test_cli_rejects_neither_index_nor_army_names(
    capsys: pytest.CaptureFixture[str],
) -> None:
    with pytest.raises(SystemExit) as excinfo:
        render_army_pack()

    assert excinfo.value.code == 1
    assert "exactly one of" in unwrapped(capsys.readouterr().err)


def test_cli_reports_a_missing_index_on_stderr(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    with pytest.raises(SystemExit) as excinfo:
        render_army_pack(index=tmp_path / "absent.toml")

    assert excinfo.value.code == 1
    assert "Error:" in unwrapped(capsys.readouterr().err)


def test_cli_reports_a_missing_army_in_the_index_on_stderr(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    pack_dir = tmp_path / "2025"
    pack_dir.mkdir()
    (pack_dir / "pack.toml").write_text(
        'title = "Test"\n\n[[armies]]\narmy = "nope"\n', encoding="utf-8"
    )

    with pytest.raises(SystemExit) as excinfo:
        render_army_pack(index=pack_dir / "pack.toml")

    assert excinfo.value.code == 1
    err = unwrapped(capsys.readouterr().err)
    assert "Army 1" in err
    assert "'nope'" in err


def test_cli_reports_an_unknown_ad_hoc_army_on_stderr(
    capsys: pytest.CaptureFixture[str],
) -> None:
    with pytest.raises(SystemExit) as excinfo:
        render_army_pack("no-such-army")

    assert excinfo.value.code == 1
    assert "Error:" in unwrapped(capsys.readouterr().err)


def test_army_pack_product_registered_under_cli(tmp_path: Path) -> None:
    index = _write_pack_dir(tmp_path)
    out = tmp_path / "pack.md"

    render_army_pack(index=index, opts=RenderOpts(format="markdown", out=out))

    assert out.exists()


@pytest.mark.skipif(shutil.which(ENGINE) is None, reason=f"{ENGINE} not installed")
def test_render_army_pack_pdf_compiles(tmp_path: Path) -> None:
    index = _write_pack_dir(tmp_path)
    out = tmp_path / "pack.pdf"

    render_army_pack(index=index, opts=RenderOpts(format="pdf", out=out))

    assert out.stat().st_size > 0


# --- The Rules Reference sits inside each Army's entry (ADR 0029) -----------


def _two_army_pack(*, rules: bool = True) -> ArmyPack:
    return build_pack(
        [("Geir Arne", io.load_army(DEMO_ARMY)), ("Morten", io.load_army(DEMO_ARMY))],
        title="Test Pack",
        stem="pack",
        image_for=no_image,
        rules=rules,
    )


def test_each_army_in_a_pack_gets_its_own_rules_reference() -> None:
    # Nothing is shared or deduplicated across Armies: a player's own pages
    # have to be complete on their own.
    pack = _two_army_pack()

    assert all(entry.reference.rules is not None for entry in pack.entries)


def test_two_armies_fielding_one_rule_do_not_share_an_anchor() -> None:
    # A Pack is one document with one id space, so an unprefixed anchor would
    # emit the same id twice and land every link in the first Army.
    pack = _two_army_pack()

    first, second = (entry.reference.rules for entry in pack.entries)
    assert first is not None
    assert second is not None
    assert set(first.anchors.values()).isdisjoint(second.anchors.values())


def test_no_rules_leaves_the_pack_without_one() -> None:
    pack = _two_army_pack(rules=False)

    assert all(entry.reference.rules is None for entry in pack.entries)


def test_army_pack_markdown_prints_a_rules_reference_per_army(tmp_path: Path) -> None:
    pack = _two_army_pack()

    out = render(
        ARMY_PACK, pack, fmt=get_format("markdown"), name="pack", output_root=tmp_path
    )

    text = out.read_text(encoding="utf-8")
    assert text.count("### Rules Reference") == 2
    # Every emitted anchor is unique, which is what keeps the links honest.
    ids = re.findall(r'<a id="([^"]+)"></a>', text)
    assert len(ids) == len(set(ids))


def test_army_pack_markdown_omits_the_rules_reference_with_no_rules(
    tmp_path: Path,
) -> None:
    pack = _two_army_pack(rules=False)

    out = render(
        ARMY_PACK, pack, fmt=get_format("markdown"), name="pack", output_root=tmp_path
    )

    text = out.read_text(encoding="utf-8")
    assert "Rules Reference" not in text
    assert "](#rule-" not in text


def test_cli_accepts_no_rules(tmp_path: Path) -> None:
    index = _write_pack_dir(tmp_path)
    out = tmp_path / "pack.md"

    render_army_pack(
        index=index, opts=RenderOpts(format="markdown", out=out, no_rules=True)
    )

    assert "Rules Reference" not in out.read_text(encoding="utf-8")
