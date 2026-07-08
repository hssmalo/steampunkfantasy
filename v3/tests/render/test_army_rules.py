"""Tests for the Army Reference product: build_reference() and the CLI."""

import shutil
from pathlib import Path

import pytest

from spf.armies.army import Army
from spf.armies.model import Model
from spf.armies.unit import Unit
from spf.config import config
from spf.frontends.cli.render import RenderOpts, render_army_rules
from spf.render.army_rules import build_reference
from spf.schemas.race import (
    AssaultConfig,
    EquipmentAssaultConfig,
    EquipmentConfig,
    ModelConfig,
    OrdersConfig,
    ShakenConfig,
    Stacker,
    UnitConfig,
)
from spf.schemas.race import (
    EquipmentRangeConfig as RangeConfig,
)

ENGINE = config.render.latex.engine

_ASSAULT = AssaultConfig(
    strength=[1, 0, 0, 0],
    strength_die="4+",
    deflection=[1, 0, 0, 0],
    deflection_die="4+",
    damage="d4",
    ap=0,
)


def _model(
    *,
    name: str = "Soldier",
    equipment: tuple[EquipmentConfig, ...] = (),
    assault: AssaultConfig = _ASSAULT,
    model_special: dict[str, str] | None = None,
) -> Model:
    config = ModelConfig(
        race="elf",
        name=name,  # pyright: ignore[reportArgumentType]
        equipment_limit=[],  # pyright: ignore[reportArgumentType]
        equipment=[],
        type=["Infantry"],
        assault=assault,
        cost=None,
        special=model_special or {},  # pyright: ignore[reportArgumentType]
    )
    return Model(
        name=name,
        config=config,
        default_equipment=(),
        upgrade_equipment=equipment,
    )


def _unit(  # noqa: PLR0913  test fixture covers every UnitConfig field under test
    *,
    models: tuple[Model, ...] | None = None,
    name: str = "Squad",
    size: str = "Small",
    shaken: ShakenConfig | None = None,
    armor: list[int] | None = None,
    unit_special: dict[str, str] | None = None,
) -> Unit:
    resolved_models = models or (_model(),)
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
        special=unit_special or {},  # pyright: ignore[reportArgumentType]
        damage_tables={"Regular": ["Fine", "Dead"]},
    )
    return Unit(name=name, config=config, models=resolved_models)


def _army(*units: Unit, nick: str = "Test", race: str = "elf") -> Army:
    return Army(race=race, nick=nick, units=units)  # pyright: ignore[reportArgumentType]


# --- build_reference: basic Unit/Model shape --------------------------------


def test_build_reference_basic_unit_and_model_fields() -> None:
    unit = _unit(
        armor=[10, 8, 6, 4],
        unit_special={"Take Cover": "[sneak][-2]"},
    )

    reference = build_reference(_army(unit, nick="The Iron Claws"), stem="test")

    assert reference.stem == "test"
    assert reference.nick == "The Iron Claws"
    assert reference.race == "elf"
    (unit_entry,) = reference.units
    assert unit_entry.name == "Squad"
    assert unit_entry.count == 1
    assert unit_entry.size == "Small"
    assert unit_entry.model_summary == ("1x Soldier",)
    assert unit_entry.armor == (10, 8, 6, 4)
    assert unit_entry.points == unit.cost().to_points()
    assert unit_entry.shaken_speed == "slow"
    assert unit_entry.shaken_movement == ("-", "-", "flee")
    assert unit_entry.shaken_fire == "No weapons"
    assert unit_entry.specials == (("Take Cover", "[sneak][-2]"),)
    assert unit_entry.damage_tables == (("Regular", ("Fine", "Dead")),)
    (model_entry,) = unit_entry.models
    assert model_entry.name == "Soldier"
    assert model_entry.equipment_summary == ()


def _equip(
    *,
    name: str = "Rifle",
    range_config: RangeConfig | None = None,
) -> EquipmentConfig:
    return EquipmentConfig(
        race="elf",  # pyright: ignore[reportArgumentType]
        name=name,
        requires=[],
        range=range_config,
    )


def test_build_reference_equipment_summary_counts_rangeless_equipment() -> None:
    rifle = _equip(name="Rifle")
    grenade = _equip(name="Grenade")
    unit = _unit(models=(_model(equipment=(rifle, rifle, grenade)),))

    reference = build_reference(_army(unit), stem="test")

    (unit_entry,) = reference.units
    (model_entry,) = unit_entry.models
    assert model_entry.equipment_summary == ("2x Rifle", "1x Grenade")
    assert model_entry.equipment == ()


def test_build_reference_ranged_equipment_gets_sub_entry() -> None:
    musket = _equip(
        name="Clockwork Musket",
        range_config=RangeConfig(
            range=24,
            angle=[True, False, False, False],
            damage="d6",
            ap=2,
            special={"Sniper": "[+1]"},  # pyright: ignore[reportArgumentType]
        ),
    )
    unit = _unit(models=(_model(equipment=(musket,)),))

    reference = build_reference(_army(unit), stem="test")

    (unit_entry,) = reference.units
    (model_entry,) = unit_entry.models
    assert model_entry.equipment_summary == ("1x Clockwork Musket",)
    (equip_entry,) = model_entry.equipment
    assert equip_entry.name == "Clockwork Musket"
    assert equip_entry.range == 24
    assert equip_entry.angle == (True, False, False, False)
    assert equip_entry.damage == "d6"
    assert equip_entry.ap == 2
    assert equip_entry.specials == (("Sniper", "[+1]"),)


def test_build_reference_rangeless_equipment_gets_no_sub_entry() -> None:
    rifle = _equip(name="Rifle")
    unit = _unit(models=(_model(equipment=(rifle,)),))

    reference = build_reference(_army(unit), stem="test")

    (unit_entry,) = reference.units
    (model_entry,) = unit_entry.models
    assert model_entry.equipment == ()


def test_build_reference_dedups_identical_ranged_equipment_within_a_model() -> None:
    range_config = RangeConfig(
        range=24, angle=[True, False, False, False], damage="d6", ap=2
    )
    musket_a = _equip(name="Musket", range_config=range_config)
    musket_b = _equip(name="Musket", range_config=range_config)
    unit = _unit(models=(_model(equipment=(musket_a, musket_b)),))

    reference = build_reference(_army(unit), stem="test")

    (unit_entry,) = reference.units
    (model_entry,) = unit_entry.models
    assert model_entry.equipment_summary == ("2x Musket",)
    (equip_entry,) = model_entry.equipment
    assert equip_entry.name == "Musket"


# --- build_reference: dedup identical Models within a Unit ------------------


def test_build_reference_collapses_identical_models_within_a_unit() -> None:
    elite = _model(name="Elite Infantry")
    grunt = _model(name="Infantry")
    unit = _unit(models=(elite, grunt, grunt, elite))

    reference = build_reference(_army(unit), stem="test")

    (unit_entry,) = reference.units
    assert unit_entry.model_summary == ("2x Elite Infantry", "2x Infantry")
    assert [m.name for m in unit_entry.models] == ["Elite Infantry", "Infantry"]


def test_build_reference_keeps_distinct_model_upgrades_separate() -> None:
    plain = _model(name="Soldier")
    upgraded = _model(name="Soldier", equipment=(_equip(name="Rifle"),))
    unit = _unit(models=(plain, upgraded))

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
    unit_a = _unit(name="Infantry", size="Small")
    unit_b = _unit(name="Archer", size="Small")

    reference = build_reference(_army(unit_a, unit_b), stem="test")

    assert len(reference.units) == 2
    assert all(u.count == 1 for u in reference.units)


def test_build_reference_army_points_counts_duplicate_units() -> None:
    unit_a = _unit(name="Infantry")
    unit_b = _unit(name="Infantry")

    reference = build_reference(_army(unit_a, unit_b, nick="Test"), stem="test")

    assert reference.points == unit_a.cost().to_points() + unit_b.cost().to_points()


# --- build_reference: resolved assault, not raw config ----------------------


def test_build_reference_model_assault_is_resolved_not_raw() -> None:
    stacking_rifle = _equip(name="Rifle")
    stacking_rifle = stacking_rifle.model_copy(
        update={
            "assault": EquipmentAssaultConfig(
                strength=Stacker(add=[1, 0, 0, 0]),
                damage=Stacker(replace="d8"),
                ap=Stacker(add=1),
                special={"Bonus": "[+1 strength]"},  # pyright: ignore[reportArgumentType]
            )
        }
    )
    model = _model(equipment=(stacking_rifle,))
    unit = _unit(models=(model,))

    reference = build_reference(_army(unit), stem="test")

    (unit_entry,) = reference.units
    (model_entry,) = unit_entry.models
    resolved = model.assault()
    assert model_entry.assault_strength == tuple(resolved.strength)
    assert model_entry.assault_strength == (2, 0, 0, 0)
    assert model_entry.assault_strength_die == resolved.strength_die
    assert model_entry.assault_damage == "d8"
    assert model_entry.assault_ap == 1
    assert model_entry.assault_specials == (("Bonus", "[+1 strength]"),)


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
    assert "Movement" not in text
    assert "Fire Order" in text or "Take Cover" in text  # a unit special
    assert "0-5: Kill 1 model" in text  # a damage-table row


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
