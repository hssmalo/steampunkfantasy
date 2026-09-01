"""Tests for the Army Reference product: build_reference() and the CLI."""

import re
import shutil
from pathlib import Path

import pytest

from spf.armies import io
from spf.armies.army import Army
from spf.armies.model import Model
from spf.armies.unit import Unit
from spf.config import config
from spf.frontends.cli.render import ARMY_RULES, RenderOpts, render_army_rules
from spf.render import render
from spf.render.army_rules import build_reference
from spf.render.formats import get_format
from spf.render.images import no_image
from spf.render.specials import SpecialLine
from spf.schemas.race import (
    AssaultConfig,
    EquipmentAssaultConfig,
    EquipmentConfig,
    ModelConfig,
    OrdersConfig,
    RaceConfig,
    ShakenConfig,
    Stacker,
    UnitConfig,
    UnitStatModifierConfig,
)
from spf.schemas.race import (
    EquipmentRangeConfig as RangeConfig,
)
from spf.schemas.special import SpecialInstance, Specials
from spf.schemas.type_aliases import ModelType
from tests.conftest import (
    InstallRegistry,
    synthetic_army,
    synthetic_equipment,
    synthetic_race,
    synthetic_registry,
    synthetic_unit,
)
from tests.render.conftest import ART, FakeLookup

ENGINE = config.render.latex.engine

_ASSAULT = AssaultConfig(
    strength=[1, 0, 0, 0],
    strength_die="4+",
    deflection=[1, 0, 0, 0],
    deflection_die="4+",
    damage="d4",
    ap=0,
)


def _model(  # noqa: PLR0913  test fixture covers every ModelConfig field under test
    *,
    name: str = "Soldier",
    equipment: list[EquipmentConfig] | None = None,
    assault: AssaultConfig = _ASSAULT,
    model_specials: Specials | None = None,
    nick: str | None = None,
    types: list[ModelType] | None = None,
    note: str = "",
) -> Model:
    config = ModelConfig(
        race="elf",
        name=name,  # pyright: ignore[reportArgumentType]
        equipment_limit=[],  # pyright: ignore[reportArgumentType]
        equipment=[],
        type=types or ["Infantry"],
        assault=assault,
        cost=None,
        specials=model_specials or {},
        note=note,
    )
    return Model(
        name=name,
        config=config,
        default_equipment=[],
        upgrade_equipment=equipment or [],
        nick=nick,
    )


def _unit(  # noqa: PLR0913  test fixture covers every UnitConfig field under test
    *,
    models: list[Model] | None = None,
    name: str = "Squad",
    size: str = "Small",
    shaken: ShakenConfig | None = None,
    armor: list[int] | None = None,
    unit_specials: Specials | None = None,
    nick: str | None = None,
    note: str = "",
) -> Unit:
    resolved_models = models or [_model()]
    config = UnitConfig(
        race="elf",
        name=name,  # pyright: ignore[reportArgumentType]
        models=[m.name for m in resolved_models],
        size=size,  # pyright: ignore[reportArgumentType]
        shaken=shaken
        or ShakenConfig(
            speed="slow", movement_order=["-", "-", "flee"], fire_order="No weapons"
        ),
        orders=OrdersConfig(),
        armor=armor,
        specials=unit_specials or {},
        note=note,
        damage_tables={  # pyright: ignore[reportArgumentType]
            "Regular": {
                "rows": ["1: Fine", "2: Dead"],
                "notes": ["Stay calm"],
            }
        },
    )
    return Unit(name=name, config=config, models=resolved_models, nick=nick)


def _army(*units: Unit, nick: str = "Test", race: str = "elf") -> Army:
    return Army(race=race, nick=nick, units=list(units))  # pyright: ignore[reportArgumentType]


# --- build_reference: basic Unit/Model shape --------------------------------


def test_build_reference_basic_unit_and_model_fields() -> None:
    unit = _unit(
        armor=[10, 8, 6, 4],
        unit_specials={"evasion": [SpecialInstance(args={"N": 4})]},
    )

    reference = build_reference(_army(unit, nick="The Iron Claws"), stem="test")

    assert reference.stem == "test"
    assert reference.nick == "The Iron Claws"
    assert reference.race == "elf"
    (unit_entry,) = reference.units
    assert unit_entry.name == "Squad"
    assert unit_entry.count == 1
    assert unit_entry.size == "Small"
    assert unit_entry.model_summary == ["1x Soldier"]
    assert unit_entry.types == ["Infantry"]
    assert unit_entry.armor == [10, 8, 6, 4]
    assert unit_entry.points == unit.cost().to_points()
    assert unit_entry.shaken_speed == "slow"
    assert unit_entry.shaken_movement == ["-", "-", "flee"]
    assert unit_entry.shaken_fire == "No weapons"
    assert unit_entry.specials == [
        SpecialLine("Evasion", "[4+]", "rule-special-evasion")
    ]
    assert unit_entry.damage_tables == [
        ("Regular", [("1", "Fine"), ("2", "Dead")], ["Stay calm"]),
    ]
    (model_entry,) = unit_entry.models
    assert model_entry.name == "Soldier"
    assert model_entry.equipment_summary == []


def _equip(
    *,
    name: str = "Rifle",
    range_config: RangeConfig | None = None,
    unit_stats: UnitStatModifierConfig | None = None,
    note: str = "",
) -> EquipmentConfig:
    return EquipmentConfig(
        race="elf",  # pyright: ignore[reportArgumentType]
        name=name,
        requires=[],
        range=range_config,
        unit=unit_stats,
        note=note,
    )


def test_build_reference_equipment_summary_counts_rangeless_equipment() -> None:
    rifle = _equip(name="Rifle")
    grenade = _equip(name="Grenade")
    unit = _unit(models=[_model(equipment=[rifle, rifle, grenade])])

    reference = build_reference(_army(unit), stem="test")

    (unit_entry,) = reference.units
    (model_entry,) = unit_entry.models
    assert model_entry.equipment_summary == ["2x Rifle", "1x Grenade"]
    assert model_entry.equipment == []


def test_build_reference_ranged_equipment_gets_sub_entry() -> None:
    musket = _equip(
        name="Clockwork Musket",
        range_config=RangeConfig(
            range=24,
            angle=[True, False, False, False],
            damage="d6",
            ap=2,
            specials={"sniper": [SpecialInstance(text="Choose the model")]},
        ),
    )
    unit = _unit(models=[_model(equipment=[musket])])

    reference = build_reference(_army(unit), stem="test")

    (unit_entry,) = reference.units
    (model_entry,) = unit_entry.models
    assert model_entry.equipment_summary == ["1x Clockwork Musket"]
    (equip_entry,) = model_entry.equipment
    assert equip_entry.name == "Clockwork Musket"
    assert equip_entry.range == 24
    assert equip_entry.angle == [True, False, False, False]
    assert equip_entry.damage == "d6"
    assert equip_entry.ap == 2
    assert equip_entry.specials == [
        SpecialLine("Sniper", "Choose the model", "rule-special-sniper")
    ]


def test_build_reference_rangeless_equipment_gets_no_sub_entry() -> None:
    rifle = _equip(name="Rifle")
    unit = _unit(models=[_model(equipment=[rifle])])

    reference = build_reference(_army(unit), stem="test")

    (unit_entry,) = reference.units
    (model_entry,) = unit_entry.models
    assert model_entry.equipment == []


def test_build_reference_dedups_identical_ranged_equipment_within_a_model() -> None:
    range_config = RangeConfig(
        range=24, angle=[True, False, False, False], damage="d6", ap=2
    )
    musket_a = _equip(name="Musket", range_config=range_config)
    musket_b = _equip(name="Musket", range_config=range_config)
    unit = _unit(models=[_model(equipment=[musket_a, musket_b])])

    reference = build_reference(_army(unit), stem="test")

    (unit_entry,) = reference.units
    (model_entry,) = unit_entry.models
    assert model_entry.equipment_summary == ["2x Musket"]
    (equip_entry,) = model_entry.equipment
    assert equip_entry.name == "Musket"


# --- build_reference: dedup identical Models within a Unit ------------------


def test_build_reference_collapses_identical_models_within_a_unit() -> None:
    elite = _model(name="Elite Infantry", types=["Infantry", "Elite"])
    grunt = _model(name="Infantry")
    unit = _unit(models=[elite, grunt, grunt, elite])

    reference = build_reference(_army(unit), stem="test")

    (unit_entry,) = reference.units
    assert unit_entry.model_summary == ["2x Elite Infantry", "2x Infantry"]
    assert unit_entry.types == ["Infantry"]
    assert [m.name for m in unit_entry.models] == ["Elite Infantry", "Infantry"]


def test_build_reference_types_is_empty_when_models_share_nothing() -> None:
    walker = _model(name="Trooper", types=["Bio", "Infantry", "Walking"])
    wagon = _model(name="Wagon", types=["Vehicle", "Mechanical", "Tracked"])

    reference = build_reference(_army(_unit(models=[walker, wagon])), stem="test")

    (unit_entry,) = reference.units
    assert unit_entry.types == []


def test_build_reference_keeps_distinct_model_upgrades_separate() -> None:
    plain = _model(name="Soldier")
    upgraded = _model(name="Soldier", equipment=[_equip(name="Rifle")])
    unit = _unit(models=[plain, upgraded])

    reference = build_reference(_army(unit), stem="test")

    (unit_entry,) = reference.units
    assert len(unit_entry.models) == 2


# --- build_reference: dedup identical Units, points -------------------------


def test_build_reference_collapses_identical_units_with_count() -> None:
    unit_a = _unit(name="Infantry")
    unit_b = _unit(name="Infantry")

    reference = build_reference(_army(unit_a, unit_b), stem="test")

    assert len(reference.units) == 1
    (unit_entry,) = reference.units
    assert unit_entry.count == 2
    assert unit_entry.points == unit_a.cost().to_points()


def test_build_reference_keeps_distinct_units_separate() -> None:
    unit_a = _unit(name="Infantry", size="small")
    unit_b = _unit(name="Archer", size="small")

    reference = build_reference(_army(unit_a, unit_b), stem="test")

    assert len(reference.units) == 2
    assert all(u.count == 1 for u in reference.units)


def test_build_reference_army_points_counts_duplicate_units() -> None:
    unit_a = _unit(name="Infantry")
    unit_b = _unit(name="Infantry")

    reference = build_reference(_army(unit_a, unit_b, nick="Test"), stem="test")

    assert reference.points == unit_a.cost().to_points() + unit_b.cost().to_points()


# --- build_reference: Nicks in the entry names and the collapse key ---------


def test_build_reference_unit_nick_replaces_the_catalogue_name() -> None:
    unit = _unit(name="Infantry", nick="Da Lads")

    reference = build_reference(_army(unit), stem="test")

    (unit_entry,) = reference.units
    # A Nick replaces the catalogue name outright — no parenthetical.
    assert unit_entry.name == "Da Lads"


def test_build_reference_model_nick_replaces_the_catalogue_name() -> None:
    unit = _unit(models=[_model(name="Infantry", nick="Grubnak")])

    reference = build_reference(_army(unit), stem="test")

    (unit_entry,) = reference.units
    assert unit_entry.model_summary == ["1x Grubnak"]
    assert [m.name for m in unit_entry.models] == ["Grubnak"]


def test_build_reference_unit_image_still_addressed_by_toml_key() -> None:
    lookup = FakeLookup(ART)

    build_reference(
        _army(_unit(name="infantry", nick="Da Lads")), stem="test", image_for=lookup
    )

    # Nicking never changes how an Asset is addressed.
    assert ("elf", "infantry") in lookup.calls


def test_build_reference_un_nicked_units_still_collapse() -> None:
    units = [_unit(name="Infantry") for _ in range(3)]

    reference = build_reference(_army(*units), stem="test")

    (unit_entry,) = reference.units
    assert unit_entry.count == 3


def test_build_reference_differently_nicked_units_do_not_collapse() -> None:
    units = [_unit(name="Infantry", nick=nick) for nick in ("A", "B", "C")]

    reference = build_reference(_army(*units), stem="test")

    assert [u.name for u in reference.units] == ["A", "B", "C"]
    assert all(u.count == 1 for u in reference.units)


def test_build_reference_same_nicked_units_collapse() -> None:
    units = [_unit(name="Infantry", nick="Boyz") for _ in range(2)]

    reference = build_reference(_army(*units), stem="test")

    (unit_entry,) = reference.units
    assert unit_entry.name == "Boyz"
    assert unit_entry.count == 2


def test_build_reference_nicked_model_splits_from_identical_squadmates() -> None:
    grunt = _model(name="Infantry")
    named = _model(name="Infantry", nick="Grubnak")
    unit = _unit(models=[named, grunt, grunt])

    reference = build_reference(_army(unit), stem="test")

    (unit_entry,) = reference.units
    assert unit_entry.model_summary == ["1x Grubnak", "2x Infantry"]
    assert [m.name for m in unit_entry.models] == ["Grubnak", "Infantry"]


# --- build_reference: resolved assault, not raw config ----------------------


def test_build_reference_model_assault_is_resolved_not_raw() -> None:
    stacking_rifle = _equip(name="Rifle")
    stacking_rifle = stacking_rifle.model_copy(
        update={
            "assault": EquipmentAssaultConfig(
                strength=Stacker(add=[1, 0, 0, 0]),
                damage=Stacker(replace="d8"),
                ap=Stacker(add=1),
                specials={"ork_reroll": [SpecialInstance(args={"N": 3})]},
            )
        }
    )
    model = _model(equipment=[stacking_rifle])
    unit = _unit(models=[model])

    reference = build_reference(_army(unit), stem="test")

    (unit_entry,) = reference.units
    (model_entry,) = unit_entry.models
    resolved = model.assault()
    assert model_entry.assault_strength == list(resolved.strength)
    assert model_entry.assault_strength == [2, 0, 0, 0]
    assert model_entry.assault_strength_die == resolved.strength_die
    assert model_entry.assault_damage == "d8"
    assert model_entry.assault_ap == 1
    assert model_entry.assault_specials == [
        SpecialLine("Ork Reroll", "[3]", "rule-special-ork-reroll")
    ]


# --- Templates: two-column damage table (drives the real templates) --------


def test_army_rules_markdown_renders_two_column_damage_table(tmp_path: Path) -> None:
    reference = build_reference(_army(_unit()), stem="test")

    out = render(
        ARMY_RULES,
        reference,
        fmt=get_format("markdown"),
        name="test",
        output_root=tmp_path,
    )

    text = out.read_text(encoding="utf-8")
    # Rows must be contiguous with the header separator: a blank line here would
    # end the Markdown table and leave the rows as loose text.
    assert "| Roll | Effect |\n| ---- | ------ |\n| 1 | Fine |\n| 2 | Dead |\n" in text
    assert "- Stay calm" in text


def test_army_rules_latex_renders_two_column_damage_table(tmp_path: Path) -> None:
    reference = build_reference(_army(_unit()), stem="test")

    out = render(
        ARMY_RULES,
        reference,
        fmt=get_format("latex"),
        name="test",
        output_root=tmp_path,
    )

    text = out.read_text(encoding="utf-8")
    assert r"\begin{tabular}{ll}" in text
    assert r"1 & Fine \\" in text
    assert r"\item Stay calm" in text


# --- CLI: render army-rules end-to-end (drives the real templates) ---------

DEMO_ARMY = "demo"


def test_render_army_rules_markdown_has_title_and_unit_sections(
    tmp_path: Path,
) -> None:
    out = tmp_path / "demo.md"
    render_army_rules(DEMO_ARMY, opts=RenderOpts(format="markdown", out=out))

    text = out.read_text(encoding="utf-8")
    assert "Iron Claws" in text
    assert "goblin" in text
    assert "## Goblin Infantry" in text
    assert "---" in text
    assert "### " in text  # a Model subsection
    # Orders are not part of an Army Reference; they live on the Order Cards.
    # Checked over the Units alone: the Rules Reference names the Movement
    # phases a token is resolved in, which is not an order.
    units, _, _rules = text.partition("## Rules Reference")
    assert "Movement" not in units
    assert "Fire Order" in text or "Take Cover" in text  # a unit special
    assert "| 0-5 | Kill 1 model |" in text  # a two-column damage-table row


def test_render_army_rules_html_is_a_document(tmp_path: Path) -> None:
    out = tmp_path / "demo.html"
    render_army_rules(DEMO_ARMY, opts=RenderOpts(format="html", out=out))

    text = out.read_text(encoding="utf-8")
    assert "<!DOCTYPE html>" in text
    assert "Iron Claws" in text


def test_render_army_rules_latex_uses_article_with_newpage_per_unit(
    tmp_path: Path,
) -> None:
    out = tmp_path / "demo.tex"
    render_army_rules(DEMO_ARMY, opts=RenderOpts(format="latex", out=out))

    text = out.read_text(encoding="utf-8")
    assert r"\documentclass" in text
    assert "{article}" in text
    assert r"\section{" in text
    assert r"\newpage" in text


@pytest.mark.skipif(shutil.which(ENGINE) is None, reason=f"{ENGINE} not installed")
def test_render_army_rules_pdf_compiles(tmp_path: Path) -> None:
    out = tmp_path / "demo.pdf"
    render_army_rules(DEMO_ARMY, opts=RenderOpts(format="pdf", out=out))

    assert out.stat().st_size > 0


def test_render_army_rules_missing_army_exits_nonzero(tmp_path: Path) -> None:
    out = tmp_path / "missing.md"
    with pytest.raises(SystemExit) as excinfo:
        render_army_rules("no-such-army", opts=RenderOpts(format="markdown", out=out))

    assert excinfo.value.code == 1
    assert not out.exists()


# --- build_reference: Image Assets on the view-model ------------------------


def test_build_reference_populates_images_from_the_injected_lookup() -> None:
    image = Path("/assets/goblin/images/art.png")
    lookup = FakeLookup(image)

    reference = build_reference(
        _army(_unit(name="Squad"), race="goblin"),
        stem="test",
        image_for=lookup,
    )

    assert reference.race_image == image
    assert [unit.image for unit in reference.units] == [image]


def test_build_reference_looks_images_up_by_toml_key_not_display_name() -> None:
    # The Target that addresses an Asset is the TOML key, which `Unit.name`
    # carries; `unit.config.name` is the display name shown in the document.
    lookup = FakeLookup(None)
    unit = _unit(name="Goblin Infantry")
    unit = Unit(name="goblin_infantry", config=unit.config, models=unit.models)

    build_reference(
        _army(unit, race="goblin"),
        stem="test",
        image_for=lookup,
    )

    assert lookup.calls == [("goblin", "goblin"), ("goblin", "goblin_infantry")]


def test_build_reference_leaves_images_none_when_there_is_no_art() -> None:
    reference = build_reference(
        _army(_unit()),
        stem="test",
        image_for=FakeLookup(None),
    )

    assert reference.race_image is None
    assert [unit.image for unit in reference.units] == [None]


# --- Templates: embedded Image Assets (drives the real templates) ----------


def test_army_rules_markdown_embeds_race_and_unit_images(tmp_path: Path) -> None:
    # Relative to the written document, not absolute: a root-absolute path
    # loses the share name when the file is opened across a UNC boundary,
    # such as `file://wsl.localhost/<distro>/...` (ADR 0017).
    art = tmp_path / "assets" / "art.png"
    reference = build_reference(
        _army(_unit(), race="goblin"), stem="test", image_for=FakeLookup(art)
    )

    out = render(
        ARMY_RULES,
        reference,
        fmt=get_format("markdown"),
        name="test",
        output_root=tmp_path,
    )

    text = out.read_text(encoding="utf-8")
    assert "![goblin](../assets/art.png)" in text
    assert "![Squad](../assets/art.png)" in text


def test_army_rules_markdown_emits_no_image_markup_without_art(
    tmp_path: Path,
) -> None:
    reference = build_reference(
        _army(_unit(), race="goblin"), stem="test", image_for=FakeLookup(None)
    )

    out = render(
        ARMY_RULES,
        reference,
        fmt=get_format("markdown"),
        name="test",
        output_root=tmp_path,
    )

    assert "![" not in out.read_text(encoding="utf-8")


def test_army_rules_latex_puts_the_unit_image_beside_the_stat_block(
    tmp_path: Path,
) -> None:
    reference = build_reference(
        _army(_unit(), race="goblin"), stem="test", image_for=FakeLookup(ART)
    )

    out = render(
        ARMY_RULES,
        reference,
        fmt=get_format("latex"),
        name="test",
        output_root=tmp_path,
    )

    text = out.read_text(encoding="utf-8")
    assert r"\usepackage{graphicx}" in text
    # Absolute here: the engine compiles in a temporary directory, so a
    # document-relative path would not resolve.
    # The path is emitted raw: `latex_escape` would turn `_` into `\_` and
    # break `\includegraphics`.
    assert rf"\includegraphics[width=\linewidth]{{{ART}}}" in text
    assert r"\begin{minipage}" in text


def test_army_rules_latex_keeps_the_full_width_stat_block_without_art(
    tmp_path: Path,
) -> None:
    reference = build_reference(
        _army(_unit(), race="goblin"), stem="test", image_for=FakeLookup(None)
    )

    out = render(
        ARMY_RULES,
        reference,
        fmt=get_format("latex"),
        name="test",
        output_root=tmp_path,
    )

    text = out.read_text(encoding="utf-8")
    assert r"\includegraphics" not in text
    assert r"\begin{minipage}" not in text
    assert r"\textbf{Size:}" in text


@pytest.mark.skipif(shutil.which(ENGINE) is None, reason=f"{ENGINE} not installed")
def test_render_army_rules_pdf_compiles_with_an_underscored_image_path(
    tmp_path: Path,
) -> None:
    # The compile happens in a temp directory, so this also pins that an
    # absolute path resolves regardless of the engine's CWD (ADR 0017) — and
    # that an underscore in the filename needs no escaping.
    art = Path(__file__).parent.parent / "fixtures" / "tiny_art.png"
    reference = build_reference(
        _army(_unit(), race="goblin"), stem="test", image_for=FakeLookup(art)
    )

    out = render(
        ARMY_RULES, reference, fmt=get_format("pdf"), name="test", output_root=tmp_path
    )

    assert out.stat().st_size > 0


def test_render_army_rules_no_images_omits_committed_art(tmp_path: Path) -> None:
    # The demo army's race has committed Unit art, so the default render does
    # embed images — `--no-images` is what removes them.
    with_art = tmp_path / "with-art.md"
    render_army_rules(DEMO_ARMY, opts=RenderOpts(format="markdown", out=with_art))
    assert "![" in with_art.read_text(encoding="utf-8")

    out = tmp_path / "no-art.md"
    render_army_rules(
        DEMO_ARMY, opts=RenderOpts(format="markdown", out=out, no_images=True)
    )

    assert "![" not in out.read_text(encoding="utf-8")


# --- Armor grants and notes: what a Special no longer carries ---------------


def test_unit_entry_armor_stacks_an_equipment_grant() -> None:
    shieldwall = _equip(
        name="ShieldWall",
        unit_stats=UnitStatModifierConfig(armor=Stacker(add=[5, 0, 0, 0])),
    )
    unit = _unit(armor=[3, 2, 1, 0], models=[_model(equipment=[shieldwall])])

    reference = build_reference(_army(unit), stem="test")

    (unit_entry,) = reference.units
    assert unit_entry.armor == [8, 2, 1, 0]


def test_unit_entry_armor_rejects_an_unusable_stacker() -> None:
    # Reachable only because the reference reads the stacked value: a data
    # error nothing consumes can never be caught.
    broken = _equip(
        name="ShieldWall",
        unit_stats=UnitStatModifierConfig(armor=Stacker(extend=[5, 0, 0, 0])),
    )
    unit = _unit(armor=[3, 2, 1, 0], models=[_model(equipment=[broken])])

    with pytest.raises(ValueError, match="cannot use 'extend' on unit armor"):
        build_reference(_army(unit), stem="test")


def test_unit_entry_carries_the_unit_note() -> None:
    unit = _unit(note="May not enter buildings")

    reference = build_reference(_army(unit), stem="test")

    (unit_entry,) = reference.units
    assert unit_entry.note == "May not enter buildings"


def test_model_entry_carries_the_model_and_assault_notes() -> None:
    assault = AssaultConfig(
        strength=[1, 0, 0, 0],
        strength_die="4+",
        deflection=[1, 0, 0, 0],
        deflection_die="4+",
        damage="d4",
        ap=0,
        note="Fights on after losing a limb",
    )
    unit = _unit(models=[_model(note="Floats", assault=assault)])

    reference = build_reference(_army(unit), stem="test")

    (model_entry,) = reference.units[0].models
    assert model_entry.note == "Floats"
    assert model_entry.assault_note == "Fights on after losing a limb"


def test_model_entry_carries_the_note_of_a_rangeless_equipment() -> None:
    # An Equipment with no ranged profile gets no sub-entry of its own, so its
    # note is printed against the Model carrying it, labeled by Equipment.
    control = _equip(name="Remote Control", note="Grants no immunity")
    unit = _unit(models=[_model(equipment=[control, control])])

    reference = build_reference(_army(unit), stem="test")

    (model_entry,) = reference.units[0].models
    assert model_entry.equipment_notes == [("Remote Control", "Grants no immunity")]


def test_equipment_entry_carries_the_range_note() -> None:
    rifle = _equip(
        name="Ogre Rifle",
        range_config=RangeConfig(
            range=4,
            angle=[True, False, False, False],
            damage="d6",
            ap=1,
            note="Remember to track ammo.",
        ),
    )
    unit = _unit(models=[_model(equipment=[rifle])])

    reference = build_reference(_army(unit), stem="test")

    (equipment_entry,) = reference.units[0].models[0].equipment
    assert equipment_entry.note == "Remember to track ammo."


def test_render_army_rules_markdown_prints_every_note(tmp_path: Path) -> None:
    rifle = _equip(
        name="Ogre Rifle",
        range_config=RangeConfig(
            range=4,
            angle=[True, False, False, False],
            damage="d6",
            ap=1,
            note="Remember to track ammo.",
        ),
    )
    control = _equip(name="Remote Control", note="Grants no immunity")
    unit = _unit(
        note="May not enter buildings",
        models=[_model(note="Floats", equipment=[rifle, control])],
    )
    reference = build_reference(_army(unit), stem="test", image_for=no_image)

    out = render(
        ARMY_RULES,
        reference,
        fmt=get_format("markdown"),
        name="t",
        output_root=tmp_path,
    )

    text = out.read_text(encoding="utf-8")
    assert "- **Note**: May not enter buildings" in text
    assert "- **Note**: Floats" in text
    assert "- **Note**: Remember to track ammo." in text
    assert "- **Note (Remote Control)**: Grants no immunity" in text


def test_render_army_rules_latex_prints_every_note(tmp_path: Path) -> None:
    unit = _unit(note="May not enter buildings", models=[_model(note="Floats")])
    reference = build_reference(_army(unit), stem="test", image_for=no_image)

    out = render(
        ARMY_RULES, reference, fmt=get_format("latex"), name="t", output_root=tmp_path
    )

    text = out.read_text(encoding="utf-8")
    assert r"\item \textbf{Note}: May not enter buildings" in text
    assert r"\item \textbf{Note}: Floats" in text


# --- Golden output: pins the standalone army-rules output byte-for-byte ----
#
# `main.tex.jinja`/`main.md.jinja` are a thin wrapper around the shared
# `reference-body` partial (also used by the Army Pack); this pins their
# combined output so a future change to either can't silently drift the
# standalone Army Reference. `image_for=no_image` keeps the fixture
# independent of the committed Asset store's contents.

# The version is pinned for this comparison: the documents stamp the version
# that rendered them, which would otherwise drift the goldens every release.
GOLDEN_DIR = Path(__file__).parent.parent / "fixtures" / "golden"


@pytest.mark.parametrize(
    ("fmt_name", "golden_name"),
    [("markdown", "army_rules.md"), ("latex", "army_rules.tex")],
)
@pytest.mark.usefixtures("pinned_version")
def test_army_rules_output_matches_golden_file(
    tmp_path: Path, fmt_name: str, golden_name: str
) -> None:
    reference = build_reference(
        io.load_army(DEMO_ARMY), stem="demo", image_for=no_image
    )

    out = render(
        ARMY_RULES,
        reference,
        fmt=get_format(fmt_name),
        name="demo",
        output_root=tmp_path,
    )

    # `.rstrip`: the committed golden file passes through the end-of-file-fixer
    # pre-commit hook, which trims trailing blank lines the templates emit.
    golden = (GOLDEN_DIR / golden_name).read_text(encoding="utf-8")
    assert out.read_text(encoding="utf-8").rstrip("\n") == golden.rstrip("\n")


# The demo Army fields no Unit whose armor an Equipment raises and no holder
# carrying a `note`, so a second Army covers both — the two things the
# Specials migration moved out of a Special and onto the record itself.
FIXTURE_ARMIES = Path(__file__).parent.parent / "fixtures" / "armies"


@pytest.mark.usefixtures("pinned_version")
def test_army_rules_output_matches_golden_file_with_granted_armor_and_notes(
    tmp_path: Path,
) -> None:
    army = io._load_army_at(
        FIXTURE_ARMIES / "dwarf_shieldwall.json", label="fixture", validate=True
    )
    reference = build_reference(army, stem="shieldwall", image_for=no_image)

    out = render(
        ARMY_RULES,
        reference,
        fmt=get_format("markdown"),
        name="shieldwall",
        output_root=tmp_path,
    )

    golden = (GOLDEN_DIR / "army_rules_dwarf.md").read_text(encoding="utf-8")
    assert out.read_text(encoding="utf-8").rstrip("\n") == golden.rstrip("\n")


# --- `--no-rules` reproduces the document as it was before the Rules Reference
#
# The opt-out's whole contract: with it, nothing about the Rules Reference —
# neither the list nor a link on a Unit line — reaches the page. The goldens
# below are the output as it stood before any of it existed, so a leak of any
# kind fails here rather than in a published document.

SHOWCASE_ARMIES = Path(__file__).parent.parent.parent / "armies" / "showcase"

NO_RULES_GOLDEN_DIR = GOLDEN_DIR / "no_rules"


@pytest.mark.parametrize(
    "army_file", sorted(p.name for p in SHOWCASE_ARMIES.glob("*.json"))
)
@pytest.mark.usefixtures("pinned_version")
def test_no_rules_reproduces_the_showcase_output(
    tmp_path: Path, army_file: str
) -> None:
    stem = Path(army_file).stem
    army = io._load_army_at(SHOWCASE_ARMIES / army_file, label=stem, validate=True)
    reference = build_reference(army, stem=stem, image_for=no_image, rules=False)

    out = render(
        ARMY_RULES,
        reference,
        fmt=get_format("markdown"),
        name=stem,
        output_root=tmp_path,
    )

    golden = (NO_RULES_GOLDEN_DIR / f"{stem}.md").read_text(encoding="utf-8")
    assert _trimmed(out.read_text(encoding="utf-8")) == _trimmed(golden)


def _trimmed(text: str) -> list[str]:
    """Split `text` into lines with trailing whitespace off each.

    A committed golden passes through the trailing-whitespace pre-commit hook,
    which strips the spaces a template emits after an empty field — so the
    trailing space is a property of the fixture, not of the renderer.
    """
    return [line.rstrip() for line in text.rstrip("\n").splitlines()]


# --- The Rules Reference in a standalone Army Reference (ADR 0029) ----------


def test_the_rules_reference_prints_after_all_the_units(tmp_path: Path) -> None:
    out = tmp_path / "demo.md"
    render_army_rules(DEMO_ARMY, opts=RenderOpts(format="markdown", out=out))

    text = out.read_text(encoding="utf-8")
    assert text.count("## Rules Reference") == 1
    # Every Unit heading comes before it: one list per Army, at the end.
    assert text.index("## Rules Reference") > text.rindex("## Goblin Infantry")


def test_a_unit_line_links_into_the_rules_reference(tmp_path: Path) -> None:
    out = tmp_path / "demo.md"
    render_army_rules(DEMO_ARMY, opts=RenderOpts(format="markdown", out=out))

    text = out.read_text(encoding="utf-8")
    linked = re.findall(r"\*\*\[[^]]+\]\(#(rule-[^)]+)\)\*\*", text)
    assert linked
    # A link with no anchor to land on is worse than no link at all.
    for anchor in linked:
        assert f'<a id="{anchor}"></a>' in text


def test_cli_accepts_no_rules(tmp_path: Path) -> None:
    out = tmp_path / "demo.md"
    render_army_rules(
        DEMO_ARMY, opts=RenderOpts(format="markdown", out=out, no_rules=True)
    )

    text = out.read_text(encoding="utf-8")
    assert "Rules Reference" not in text
    assert "](#rule-" not in text


def test_an_army_with_no_specials_prints_no_empty_heading(tmp_path: Path) -> None:
    # An empty list is worse than none: the heading would promise entries the
    # document does not have.
    reference = build_reference(_army(_unit()), stem="bare", image_for=no_image)

    out = render(
        ARMY_RULES,
        reference,
        fmt=get_format("markdown"),
        name="bare",
        output_root=tmp_path,
    )

    assert reference.rules is not None
    assert reference.rules.entries == []
    assert "Rules Reference" not in out.read_text(encoding="utf-8")


# --- Two behaviors the committed corpus has no example of ------------------
#
# The demo Army carries no Equipment that raises its Unit's armor and no
# Equipment carrying a `note`, and the `--no-rules` contract is a property of
# every document rather than of any one Army. Both are built here instead
# (ADR 0033).

_COUNTDOWN = {"countdown": [{"text": "Three rounds."}]}
"""A Special Instance of an id only the installed Registry declares."""


def _synthetic_markdown(
    race: RaceConfig, tmp_path: Path, *, stem: str, rules: bool = True
) -> str:
    """Render a one-Unit Army of `race` as an Army Reference, and read it back."""
    army = synthetic_army(race).resolve(race)
    reference = build_reference(army, stem=stem, image_for=no_image, rules=rules)
    out = render(
        ARMY_RULES,
        reference,
        fmt=get_format("markdown"),
        name=stem,
        output_root=tmp_path,
    )
    return out.read_text(encoding="utf-8")


def test_no_rules_keeps_the_rules_reference_and_its_links_off_the_page(
    tmp_path: Path, install_registry: InstallRegistry
) -> None:
    # The opt-out's whole contract: with it, neither the list nor a link on a
    # Unit line reaches the page -- and without it, both do.
    install_registry(synthetic_registry(specials={"countdown": None}))
    race = synthetic_race(units={"squad": synthetic_unit(specials=_COUNTDOWN)})

    with_rules = _synthetic_markdown(race, tmp_path, stem="rules")
    without_rules = _synthetic_markdown(race, tmp_path, stem="no-rules", rules=False)

    assert "## Rules Reference" in with_rules
    assert "](#rule-special-countdown)" in with_rules
    assert "Rules Reference" not in without_rules
    assert "](#rule-" not in without_rules


def test_an_equipment_upgrade_raises_its_units_armor_and_prints_its_note() -> None:
    shieldwall = synthetic_equipment(
        name="Wheeled ShieldWall",
        unit={"armor": {"add": [5, 0, 0, 0]}},
        note="Rolls with the Unit.",
    )
    race = synthetic_race(
        equipment={
            "knife": synthetic_equipment(name="Knife", cost=None, upgrade_all=None),
            "shieldwall": shieldwall,
        }
    )
    army_list = synthetic_army(race).upgrade_model(
        ("squad", 0),
        model_key=("soldier", 0),
        equipment_name="shieldwall",
        race_config=race,
    )

    reference = build_reference(
        army_list.resolve(race), stem="shieldwall", image_for=no_image
    )

    (unit_entry,) = reference.units
    # The Unit declares no armor of its own: every arc here is the grant.
    assert unit_entry.armor == [5, 0, 0, 0]
    (model_entry,) = unit_entry.models
    assert model_entry.equipment_notes == [
        ("Wheeled ShieldWall", "Rolls with the Unit.")
    ]
