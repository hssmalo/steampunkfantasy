"""Tests for the Order Card product: Unit.orders(), build_deck, and CLI."""

import shutil
from pathlib import Path

import pytest

from spf.armies.army import Army
from spf.armies.model import Model
from spf.armies.unit import Unit
from spf.config import config
from spf.frontends.cli.render import RenderOpts, _safe_stem, render_cards
from spf.render.cards import build_deck
from spf.schemas import type_aliases as t
from spf.schemas.race import (
    AssaultConfig,
    EquipmentConfig,
    ModelConfig,
    OrdersConfig,
    ShakenConfig,
    UnitConfig,
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


def _model(*, equipment: tuple[EquipmentConfig, ...] = ()) -> Model:
    config = ModelConfig(
        race="elf",
        name="Soldier",
        equipment_limit=[],  # pyright: ignore[reportArgumentType]
        equipment=[],
        type=["Infantry"],
        assault=_ASSAULT,
        cost=None,
    )
    return Model(
        name="Soldier",
        config=config,
        default_equipment=(),
        upgrade_equipment=equipment,
    )


def _unit(
    *,
    orders: OrdersConfig,
    models: tuple[Model, ...] | None = None,
    name: str = "Squad",
    size: t.Size = "Small",
    shaken: ShakenConfig | None = None,
) -> Unit:
    config = UnitConfig(
        race="elf",
        name=name,  # pyright: ignore[reportArgumentType]
        models=["Soldier"],
        size=size,
        shaken=shaken or ShakenConfig(speed="slow", movement_order=["-", "-", "flee"]),
        orders=orders,
        damage_tables={"Regular": ["Fine", "Dead"]},
    )
    return Unit(name=name, config=config, models=models or (_model(),))


def _equip(orders_gained: OrdersConfig, *, name: str = "SMG") -> EquipmentConfig:
    return EquipmentConfig(
        race="elf",  # pyright: ignore[reportArgumentType]
        name=name,
        requires=[],
        orders_gained=orders_gained,
    )


# --- Unit.orders() merge ----------------------------------------------------


def test_orders_base_only_returns_base_rows() -> None:
    unit = _unit(
        orders=OrdersConfig(
            movement={"still": [["A", "B"]], "slow": [["C", "D"]]},
            fire={"still": [["Fire"]]},
        )
    )

    merged = unit.orders()

    assert merged.movement == {"still": [["A", "B"]], "slow": [["C", "D"]]}
    assert merged.fire == {"still": [["Fire"]]}


def test_orders_equipment_appends_rows_after_base_rows() -> None:
    smg = _equip(OrdersConfig(fire={"still": [["Fire", "Fire"]]}))
    unit = _unit(
        orders=OrdersConfig(fire={"still": [["-"]]}),
        models=(_model(equipment=(smg,)),),
    )

    merged = unit.orders()

    assert merged.fire == {"still": [["-"], ["Fire", "Fire"]]}


def test_orders_equipment_introduces_new_speed() -> None:
    hide = _equip(OrdersConfig(movement={"crawl": [["360°", "F", "F"]]}), name="Hide")
    unit = _unit(
        orders=OrdersConfig(movement={"still": [["A"]]}),
        models=(_model(equipment=(hide,)),),
    )

    merged = unit.orders()

    assert merged.movement == {"still": [["A"]], "crawl": [["360°", "F", "F"]]}


def test_orders_duplicate_rows_across_models_collapse() -> None:
    smg_a = _equip(OrdersConfig(fire={"still": [["Fire", "Fire"]]}), name="SMG-A")
    smg_b = _equip(OrdersConfig(fire={"still": [["Fire", "Fire"]]}), name="SMG-B")
    unit = _unit(
        orders=OrdersConfig(fire={"still": [["-"]]}),
        models=(_model(equipment=(smg_a,)), _model(equipment=(smg_b,))),
    )

    merged = unit.orders()

    assert merged.fire == {"still": [["-"], ["Fire", "Fire"]]}


def test_orders_speeds_follow_canonical_order() -> None:
    unit = _unit(
        orders=OrdersConfig(
            movement={"fast": [["F"]], "still": [["S"]], "slow": [["L"]]}
        )
    )

    merged = unit.orders()

    assert merged.movement is not None
    assert list(merged.movement) == ["still", "slow", "fast"]


# --- build_deck: flat rows for the Markdown family --------------------------


def _army(*units: Unit, nick: str = "Test") -> Army:
    return Army(race="elf", nick=nick, units=units)


def test_build_deck_flat_rows_one_entry_per_option() -> None:
    unit = _unit(
        orders=OrdersConfig(
            movement={"still": [["A", "B"], ["C", "D"]], "slow": [["E", "F"]]},
            fire={"still": [["Fire"]]},
        )
    )

    deck = build_deck(_army(unit), stem="test")

    assert deck.stem == "test"
    (unit_orders,) = deck.units
    assert unit_orders.name == "Squad"
    assert unit_orders.movement_rows == (
        ("still", ("A", "B")),
        ("still", ("C", "D")),
        ("slow", ("E", "F")),
    )
    assert unit_orders.fire_rows == (("still", ("Fire",)),)


# --- build_deck: card transposition -----------------------------------------


def test_build_deck_transposes_cards_by_option_index() -> None:
    unit = _unit(
        orders=OrdersConfig(
            movement={
                "still": [["S0"], ["S1"]],
                "slow": [["L0"], ["L1"]],
            },
            fire={"still": [["F0"]]},
        )
    )

    deck = build_deck(_army(unit), stem="test")

    movement = [c for c in deck.cards if c.kind == "Movement"]
    fire = [c for c in deck.cards if c.kind == "Fire"]
    assert [c.rows for c in movement] == [
        (("still", ("S0",)), ("slow", ("L0",))),
        (("still", ("S1",)), ("slow", ("L1",))),
    ]
    assert [c.rows for c in fire] == [(("still", ("F0",)),)]
    assert all(c.unit_name == "Squad" for c in deck.cards)


def test_build_deck_uneven_option_counts_drop_speed_from_later_cards() -> None:
    unit = _unit(
        orders=OrdersConfig(
            movement={
                "still": [["S0"], ["S1"]],
                "slow": [["L0"]],
            }
        )
    )

    deck = build_deck(_army(unit), stem="test")

    assert [c.rows for c in deck.cards] == [
        (("still", ("S0",)), ("slow", ("L0",))),
        (("still", ("S1",)),),
    ]


# --- build_deck: dedup and shaken -------------------------------------------


def test_build_deck_collapses_identical_units() -> None:
    orders = OrdersConfig(movement={"still": [["A"]]})
    unit_a = _unit(orders=orders, name="Infantry")
    unit_b = _unit(orders=orders, name="Infantry")

    deck = build_deck(_army(unit_a, unit_b), stem="test")

    assert len(deck.units) == 1
    assert [c.rows for c in deck.cards] == [(("still", ("A",)),)]


def test_build_deck_keeps_distinct_units() -> None:
    unit_a = _unit(orders=OrdersConfig(movement={"still": [["A"]]}), name="Infantry")
    unit_b = _unit(orders=OrdersConfig(movement={"still": [["B"]]}), name="Archer")

    deck = build_deck(_army(unit_a, unit_b), stem="test")

    assert len(deck.units) == 2
    assert len(deck.cards) == 2


def test_build_deck_carries_shaken_to_units_not_cards() -> None:
    unit = _unit(
        orders=OrdersConfig(movement={"still": [["A"]]}),
        shaken=ShakenConfig(
            speed="slow", movement_order=["-", "-", "flee"], fire_order="No weapons"
        ),
    )

    deck = build_deck(_army(unit), stem="test")

    (unit_orders,) = deck.units
    assert unit_orders.shaken_movement == ("slow", "-", "-", "flee")
    assert unit_orders.shaken_fire == "No weapons"
    # Shaken is not an order option, so it never becomes a card.
    assert all("flee" not in str(card.rows) for card in deck.cards)


# --- _safe_stem -------------------------------------------------------------


def test_safe_stem_keeps_safe_characters() -> None:
    assert _safe_stem("elf-warband-2025") == "elf-warband-2025"


def test_safe_stem_slugifies_unsafe_characters() -> None:
    assert _safe_stem("Geir Arne's army") == "Geir-Arne-s-army"


def test_safe_stem_collapses_runs_and_strips_ends() -> None:
    assert _safe_stem("2025/geir_arne") == "2025-geir-arne"
    assert _safe_stem("  spaced  ") == "spaced"


# --- CLI: render cards end-to-end (drives the real templates) ---------------

DEMO_ARMY = "demo"


def test_render_cards_markdown_has_tables_and_shaken(tmp_path: Path) -> None:
    out = tmp_path / "demo.md"
    render_cards(DEMO_ARMY, opts=RenderOpts(format="markdown", out=out))

    text = out.read_text(encoding="utf-8")
    assert "## Goblin Infantry" in text
    assert "### Movement" in text
    assert "### Fire" in text
    assert "| shaken: " in text


def test_render_cards_html_is_a_table(tmp_path: Path) -> None:
    out = tmp_path / "demo.html"
    render_cards(DEMO_ARMY, opts=RenderOpts(format="html", out=out))

    assert "<table>" in out.read_text(encoding="utf-8")


def test_render_cards_latex_uses_flacards_cards(tmp_path: Path) -> None:
    out = tmp_path / "demo.tex"
    render_cards(DEMO_ARMY, opts=RenderOpts(format="latex", out=out))

    text = out.read_text(encoding="utf-8")
    assert "flacards" in text
    assert r"\card" in text
    # Real order glyphs are LaTeX-escaped, not raw.
    assert r"\textdegree" in text


@pytest.mark.skipif(shutil.which(ENGINE) is None, reason=f"{ENGINE} not installed")
def test_render_cards_pdf_compiles(tmp_path: Path) -> None:
    out = tmp_path / "demo.pdf"
    render_cards(DEMO_ARMY, opts=RenderOpts(format="pdf", out=out))

    assert out.stat().st_size > 0


def test_render_cards_missing_army_exits_nonzero(tmp_path: Path) -> None:
    out = tmp_path / "missing.md"
    with pytest.raises(SystemExit) as excinfo:
        render_cards("no-such-army", opts=RenderOpts(format="markdown", out=out))

    assert excinfo.value.code == 1
    assert not out.exists()
