"""Tests for the Order Card product: Unit.orders(), build_deck, and CLI."""

import shutil
from pathlib import Path

import pytest

from spf.armies.army import Army
from spf.armies.model import Model
from spf.armies.unit import Unit
from spf.config import config
from spf.frontends.cli.render import CARDS, RenderOpts, render_cards, safe_stem
from spf.render import render
from spf.render.cards import OrderCardDeck, build_deck
from spf.render.formats import get_format
from spf.schemas.race import (
    AssaultConfig,
    EquipmentConfig,
    ModelConfig,
    OrdersConfig,
    ShakenConfig,
    UnitConfig,
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


def _model(*, equipment: list[EquipmentConfig] | None = None) -> Model:
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
        default_equipment=[],
        upgrade_equipment=equipment or [],
    )


def _unit(  # noqa: PLR0913  test fixture covers every Unit field under test
    *,
    orders: OrdersConfig,
    models: list[Model] | None = None,
    name: str = "Squad",
    size: str = "small",
    shaken: ShakenConfig | None = None,
    nick: str | None = None,
) -> Unit:
    config = UnitConfig(
        race="elf",
        name=name,  # pyright: ignore[reportArgumentType]
        models=["Soldier"],
        size=size,
        shaken=shaken or ShakenConfig(speed="slow", movement_order=["-", "-", "flee"]),
        orders=orders,
        damage_tables={"Regular": {"rows": ["1: Fine", "2: Dead"]}},  # pyright: ignore[reportArgumentType]
    )
    return Unit(name=name, config=config, models=models or [_model()], nick=nick)


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
        models=[_model(equipment=[smg])],
    )

    merged = unit.orders()

    assert merged.fire == {"still": [["-"], ["Fire", "Fire"]]}


def test_orders_equipment_introduces_new_speed() -> None:
    hide = _equip(OrdersConfig(movement={"crawl": [["360°", "F", "F"]]}), name="Hide")
    unit = _unit(
        orders=OrdersConfig(movement={"still": [["A"]]}),
        models=[_model(equipment=[hide])],
    )

    merged = unit.orders()

    assert merged.movement == {"still": [["A"]], "crawl": [["360°", "F", "F"]]}


def test_orders_duplicate_rows_across_models_collapse() -> None:
    smg_a = _equip(OrdersConfig(fire={"still": [["Fire", "Fire"]]}), name="SMG-A")
    smg_b = _equip(OrdersConfig(fire={"still": [["Fire", "Fire"]]}), name="SMG-B")
    unit = _unit(
        orders=OrdersConfig(fire={"still": [["-"]]}),
        models=[_model(equipment=[smg_a]), _model(equipment=[smg_b])],
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


# --- Unit.orders_by_source() -------------------------------------------------


def test_orders_by_source_base_only_unit_yields_one_source() -> None:
    unit = _unit(orders=OrdersConfig(movement={"still": [["A"]]}))

    (base,) = unit.orders_by_source()

    assert base.source is None
    assert base.orders.movement == {"still": [["A"]]}


def test_orders_by_source_lists_base_then_each_equipment() -> None:
    smg = _equip(OrdersConfig(fire={"still": [["Fire", "Fire"]]}))
    unit = _unit(
        orders=OrdersConfig(fire={"still": [["-"]]}),
        models=[_model(equipment=[smg])],
    )

    base, gained = unit.orders_by_source()

    assert base.source is None
    assert base.orders.fire == {"still": [["-"]]}
    assert gained.source == "SMG"
    assert gained.orders.fire == {"still": [["Fire", "Fire"]]}


def test_orders_by_source_drops_a_gained_row_matching_a_base_row() -> None:
    smg = _equip(OrdersConfig(fire={"still": [["-"], ["Fire"]]}))
    unit = _unit(
        orders=OrdersConfig(fire={"still": [["-"]]}),
        models=[_model(equipment=[smg])],
    )

    _, gained = unit.orders_by_source()

    assert gained.orders.fire == {"still": [["Fire"]]}


def test_orders_by_source_omits_an_equipment_whose_rows_are_all_redundant() -> None:
    smg = _equip(OrdersConfig(fire={"still": [["-"]]}))
    unit = _unit(
        orders=OrdersConfig(fire={"still": [["-"]]}),
        models=[_model(equipment=[smg])],
    )

    sources = unit.orders_by_source()

    assert [s.source for s in sources] == [None]


def test_orders_by_source_keeps_a_row_two_equipment_both_grant() -> None:
    # Sources are independent: either may be absent from a loadout, so each
    # keeps its own copy of a row the other also grants.
    smg_a = _equip(OrdersConfig(fire={"still": [["Fire"]]}), name="SMG-A")
    smg_b = _equip(OrdersConfig(fire={"still": [["Fire"]]}), name="SMG-B")
    unit = _unit(
        orders=OrdersConfig(fire={"still": [["-"]]}),
        models=[_model(equipment=[smg_a]), _model(equipment=[smg_b])],
    )

    _, first, second = unit.orders_by_source()

    assert (first.source, second.source) == ("SMG-A", "SMG-B")
    assert first.orders.fire == {"still": [["Fire"]]}
    assert second.orders.fire == {"still": [["Fire"]]}


def test_orders_by_source_unions_equipment_sharing_a_display_name() -> None:
    # darkelf `hide` and `hide_free` are distinct keys both displayed as "Hide";
    # nothing enforces that their gained rows stay identical.
    hide = _equip(OrdersConfig(movement={"crawl": [["A"]]}), name="Hide")
    hide_free = _equip(OrdersConfig(movement={"crawl": [["A"], ["B"]]}), name="Hide")
    unit = _unit(
        orders=OrdersConfig(movement={"still": [["S"]]}),
        models=[_model(equipment=[hide]), _model(equipment=[hide_free])],
    )

    _, gained = unit.orders_by_source()

    assert gained.source == "Hide"
    assert gained.orders.movement == {"crawl": [["A"], ["B"]]}


def test_orders_by_source_speeds_follow_canonical_order() -> None:
    hide = _equip(
        OrdersConfig(movement={"fast": [["F"]], "still": [["S"]], "slow": [["L"]]}),
        name="Hide",
    )
    unit = _unit(
        orders=OrdersConfig(movement={"crawl": [["C"]]}),
        models=[_model(equipment=[hide])],
    )

    _, gained = unit.orders_by_source()

    assert gained.orders.movement is not None
    assert list(gained.orders.movement) == ["still", "slow", "fast"]


def test_orders_is_the_fold_of_orders_by_source() -> None:
    # The regression bar: folding the sources reproduces the merged view.
    hide = _equip(OrdersConfig(movement={"crawl": [["360°"]]}), name="Hide")
    smg = _equip(OrdersConfig(fire={"still": [["Fire"], ["-"]]}), name="SMG")
    unit = _unit(
        orders=OrdersConfig(movement={"still": [["A"]]}, fire={"still": [["-"]]}),
        models=[_model(equipment=[hide, smg])],
    )

    merged = unit.orders()

    assert merged.movement == {"still": [["A"]], "crawl": [["360°"]]}
    assert merged.fire == {"still": [["-"], ["Fire"]]}


def test_orders_groups_a_repeated_equipment_name_with_its_first_appearance() -> None:
    # Grouping by display name is what makes one Card Set per Order Source, and
    # it is the one way the merged view can differ from the pre-ADR-0021 merge:
    # equipment encountered A, B, A merge as A, A, B rather than A, B, A. No
    # committed army carries two order-modifying equipment at all, let alone a
    # repeated display name among three.
    first = _equip(OrdersConfig(fire={"still": [["A1"]]}), name="Hide")
    other = _equip(OrdersConfig(fire={"still": [["B1"]]}), name="Wings")
    again = _equip(OrdersConfig(fire={"still": [["A2"]]}), name="Hide")
    unit = _unit(
        orders=OrdersConfig(fire={"still": [["-"]]}),
        models=[_model(equipment=[first, other, again])],
    )

    assert [s.source for s in unit.orders_by_source()] == [None, "Hide", "Wings"]
    assert unit.orders().fire == {"still": [["-"], ["A1"], ["A2"], ["B1"]]}


# --- build_deck: flat rows for the Markdown family --------------------------


def _army(*units: Unit, nick: str = "Test", race: str = "elf") -> Army:
    return Army(race=race, nick=nick, units=list(units))  # pyright: ignore[reportArgumentType]


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
    assert unit_orders.movement_rows == [
        ("still", ["A", "B"]),
        ("still", ["C", "D"]),
        ("slow", ["E", "F"]),
    ]
    assert unit_orders.fire_rows == [("still", ["Fire"])]


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
        [("still", ["S0"]), ("slow", ["L0"])],
        [("still", ["S1"]), ("slow", ["L1"])],
    ]
    assert [c.rows for c in fire] == [[("still", ["F0"])]]
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
        [("still", ["S0"]), ("slow", ["L0"])],
        [("still", ["S1"])],
    ]


# --- build_deck: one Card Set per Order Source --------------------------------


def test_build_deck_base_cards_name_no_equipment() -> None:
    unit = _unit(
        orders=OrdersConfig(movement={"still": [["A"]]}, fire={"still": [["F"]]})
    )

    deck = build_deck(_army(unit), stem="test")

    assert all(card.equipment is None for card in deck.cards)


def test_build_deck_equipment_cards_carry_its_display_name() -> None:
    hide = _equip(OrdersConfig(movement={"crawl": [["C"]]}), name="Hide")
    unit = _unit(
        orders=OrdersConfig(movement={"still": [["A"]]}),
        models=[_model(equipment=[hide])],
    )

    deck = build_deck(_army(unit), stem="test")

    assert [(c.equipment, c.rows) for c in deck.cards] == [
        (None, [("still", ["A"])]),
        ("Hide", [("crawl", ["C"])]),
    ]


def test_build_deck_never_mixes_base_and_gained_rows_on_one_card() -> None:
    # F2: base Speeds have different row counts, so an option index that is a
    # base row at one Speed was a gained row at another before ADR 0021.
    hide = _equip(
        OrdersConfig(movement={"still": [["H0"], ["H1"]], "crawl": [["H2"]]}),
        name="Hide",
    )
    unit = _unit(
        orders=OrdersConfig(
            movement={"still": [["S0"]], "slow": [["L0"], ["L1"], ["L2"]]}
        ),
        models=[_model(equipment=[hide])],
    )

    deck = build_deck(_army(unit), stem="test")

    base_cells = {"S0", "L0", "L1", "L2"}
    for card in deck.cards:
        cells = {cell for _, cells in card.rows for cell in cells}
        mixes = bool(cells & base_cells) and bool(cells - base_cells)
        assert not mixes, f"card mixes base and gained rows: {card}"
    # And the base cards are exactly what a Unit without Hide would produce.
    assert [c.rows for c in deck.cards if c.equipment is None] == [
        [("still", ["S0"]), ("slow", ["L0"])],
        [("slow", ["L1"])],
        [("slow", ["L2"])],
    ]


def test_build_deck_orders_cards_base_first_then_each_equipment() -> None:
    hide = _equip(
        OrdersConfig(movement={"crawl": [["C"]]}, fire={"still": [["HF"]]}), name="Hide"
    )
    unit = _unit(
        orders=OrdersConfig(movement={"still": [["A"]]}, fire={"still": [["F"]]}),
        models=[_model(equipment=[hide])],
    )

    deck = build_deck(_army(unit), stem="test")

    assert [(c.equipment, c.kind) for c in deck.cards] == [
        (None, "Movement"),
        (None, "Fire"),
        ("Hide", "Movement"),
        ("Hide", "Fire"),
    ]


def test_build_deck_two_equipment_each_get_their_own_card_set() -> None:
    # No committed army fields two order-modifying equipment on one Unit, so
    # this case is defined by a synthetic fixture (decision 7).
    hide = _equip(OrdersConfig(movement={"crawl": [["C"]]}), name="Hide")
    wings = _equip(OrdersConfig(movement={"fast": [["W"]]}), name="Wings")
    unit = _unit(
        orders=OrdersConfig(movement={"still": [["A"]]}),
        models=[_model(equipment=[hide, wings])],
    )

    deck = build_deck(_army(unit), stem="test")

    assert [c.equipment for c in deck.cards] == [None, "Hide", "Wings"]


def test_build_deck_units_differing_by_equipment_each_get_a_full_base_set() -> None:
    # The sharing invariant: a Card Set is shared only when every card in it
    # applies to every Unit sharing it, so the base cards are printed twice.
    hide = _equip(OrdersConfig(movement={"crawl": [["C"]]}), name="Hide")
    orders = OrdersConfig(movement={"still": [["A"]], "slow": [["B"]]})
    plain = _unit(orders=orders, name="Infantry")
    hidden = _unit(orders=orders, name="Infantry", models=[_model(equipment=[hide])])

    deck = build_deck(_army(plain, hidden), stem="test")

    assert [c.equipment for c in deck.cards] == [None, None, "Hide"]


# --- build_deck: dedup and shaken -------------------------------------------


def test_build_deck_collapses_identical_units() -> None:
    orders = OrdersConfig(movement={"still": [["A"]]})
    unit_a = _unit(orders=orders, name="Infantry")
    unit_b = _unit(orders=orders, name="Infantry")

    deck = build_deck(_army(unit_a, unit_b), stem="test")

    assert len(deck.units) == 1
    assert [c.rows for c in deck.cards] == [[("still", ["A"])]]


def test_build_deck_keeps_distinct_units() -> None:
    unit_a = _unit(orders=OrdersConfig(movement={"still": [["A"]]}), name="Infantry")
    unit_b = _unit(orders=OrdersConfig(movement={"still": [["B"]]}), name="Archer")

    deck = build_deck(_army(unit_a, unit_b), stem="test")

    assert len(deck.units) == 2
    assert len(deck.cards) == 2


def test_build_deck_unit_nick_replaces_the_catalogue_name() -> None:
    unit = _unit(orders=OrdersConfig(movement={"still": [["A"]]}), nick="Da Lads")

    deck = build_deck(_army(unit), stem="test")

    (unit_orders,) = deck.units
    assert unit_orders.name == "Da Lads"
    assert all(card.unit_name == "Da Lads" for card in deck.cards)


def test_build_deck_un_nicked_units_still_collapse() -> None:
    orders = OrdersConfig(movement={"still": [["A"]]})
    units = [_unit(orders=orders, name="Infantry") for _ in range(3)]

    deck = build_deck(_army(*units), stem="test")

    assert len(deck.units) == 1
    assert len(deck.cards) == 1


def test_build_deck_differently_nicked_units_each_get_a_card_set() -> None:
    orders = OrdersConfig(movement={"still": [["A"]]})
    units = [_unit(orders=orders, name="Infantry", nick=n) for n in ("A", "B", "C")]

    deck = build_deck(_army(*units), stem="test")

    assert [u.name for u in deck.units] == ["A", "B", "C"]
    # You nicked them to tell them apart, so each gets its own card.
    assert [c.unit_name for c in deck.cards] == ["A", "B", "C"]


def test_build_deck_same_nicked_units_collapse() -> None:
    orders = OrdersConfig(movement={"still": [["A"]]})
    units = [_unit(orders=orders, name="Infantry", nick="Boyz") for _ in range(2)]

    deck = build_deck(_army(*units), stem="test")

    assert [u.name for u in deck.units] == ["Boyz"]
    assert len(deck.cards) == 1


def test_build_deck_nicked_unit_image_still_addressed_by_toml_key() -> None:
    lookup = FakeLookup(ART)
    unit = _unit(
        orders=OrdersConfig(movement={"still": [["A"]]}),
        name="infantry",
        nick="Da Lads",
    )

    build_deck(_army(unit), stem="test", image_for=lookup)

    assert lookup.calls == [("elf", "infantry")]


def test_build_deck_carries_shaken_to_units_not_cards() -> None:
    unit = _unit(
        orders=OrdersConfig(movement={"still": [["A"]]}),
        shaken=ShakenConfig(
            speed="slow", movement_order=["-", "-", "flee"], fire_order="No weapons"
        ),
    )

    deck = build_deck(_army(unit), stem="test")

    (unit_orders,) = deck.units
    assert unit_orders.shaken_movement == ["slow", "-", "-", "flee"]
    assert unit_orders.shaken_fire == "No weapons"
    # Shaken is not an order option, so it never becomes a card.
    assert all("flee" not in str(card.rows) for card in deck.cards)


# --- build_deck: Image Assets on the view-model -----------------------------


def test_build_deck_populates_images_from_the_injected_lookup() -> None:
    image = Path("/assets/goblin/images/art.png")
    unit = _unit(
        orders=OrdersConfig(movement={"still": [["A"]]}, fire={"still": [["F"]]})
    )

    deck = build_deck(
        _army(unit, race="goblin"), stem="test", image_for=FakeLookup(image)
    )

    assert [u.image for u in deck.units] == [image]
    assert len(deck.cards) == 2  # one Movement card, one Fire card
    assert all(card.image == image for card in deck.cards)


def test_build_deck_looks_images_up_once_per_unit_by_toml_key() -> None:
    # The Target that addresses an Asset is the TOML key, which `Unit.name`
    # carries; `unit.config.name` is the display name printed on the card.
    lookup = FakeLookup(None)
    unit = _unit(
        orders=OrdersConfig(movement={"still": [["A"]]}, fire={"still": [["F"]]}),
        name="Goblin Infantry",
    )
    unit = Unit(name="goblin_infantry", config=unit.config, models=unit.models)

    build_deck(_army(unit, race="goblin"), stem="test", image_for=lookup)

    # One lookup per Unit, not one per card.
    assert lookup.calls == [("goblin", "goblin_infantry")]


def test_build_deck_leaves_images_none_when_there_is_no_art() -> None:
    unit = _unit(orders=OrdersConfig(movement={"still": [["A"]]}))

    deck = build_deck(_army(unit), stem="test", image_for=FakeLookup(None))

    assert [u.image for u in deck.units] == [None]
    assert all(card.image is None for card in deck.cards)


# --- safe_stem -------------------------------------------------------------


def testsafe_stem_keeps_safe_characters() -> None:
    assert safe_stem("elf-warband-2025") == "elf-warband-2025"


def testsafe_stem_slugifies_unsafe_characters() -> None:
    assert safe_stem("Geir Arne's army") == "Geir-Arne-s-army"


def testsafe_stem_collapses_runs_and_strips_ends() -> None:
    assert safe_stem("2025/geir_arne") == "2025-geir-arne"
    assert safe_stem("  spaced  ") == "spaced"


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


# --- Templates: the Unit's art on the card back (drives the real templates) --


def _art_deck(image: Path | None, *, name: str = "Squad") -> OrderCardDeck:
    unit = _unit(
        orders=OrdersConfig(movement={"still": [["A"]]}, fire={"still": [["F"]]}),
        name=name,
    )
    return build_deck(
        _army(unit, race="goblin"), stem="test", image_for=FakeLookup(image)
    )


def test_cards_markdown_embeds_the_unit_image(tmp_path: Path) -> None:
    # Relative to the written document, not absolute: a root-absolute path
    # loses the share name across a UNC boundary (ADR 0017).
    art = tmp_path / "assets" / "art.png"

    out = render(
        CARDS,
        _art_deck(art),
        fmt=get_format("markdown"),
        name="test",
        output_root=tmp_path,
    )

    assert "![Squad](../assets/art.png)" in out.read_text(encoding="utf-8")


def test_cards_markdown_emits_no_image_markup_without_art(tmp_path: Path) -> None:
    out = render(
        CARDS,
        _art_deck(None),
        fmt=get_format("markdown"),
        name="test",
        output_root=tmp_path,
    )

    assert "![" not in out.read_text(encoding="utf-8")


def test_cards_latex_puts_name_art_and_kind_on_the_back(tmp_path: Path) -> None:
    out = render(
        CARDS,
        _art_deck(ART),
        fmt=get_format("latex"),
        name="test",
        output_root=tmp_path,
    )

    text = out.read_text(encoding="utf-8")
    assert r"\usepackage{graphicx}" in text
    assert r"\renewcommand{\bchead}{Squad}" in text
    # A base card names the kind alone — there is no Equipment behind it.
    assert r"\renewcommand{\bcfoot}{Movement}" in text
    assert r"\renewcommand{\bcfoot}{Fire}" in text
    # The path is emitted raw: `latex_escape` would turn `_` into `\_` and
    # break `\includegraphics`.
    assert rf"\includegraphics[width=\cardartwidth]{{{ART.as_posix()}}}" in text


def test_cards_latex_names_the_equipment_under_the_kind_on_its_fronts(
    tmp_path: Path,
) -> None:
    hide = _equip(OrdersConfig(movement={"crawl": [["C"]]}), name="Hide & Seek")
    unit = _unit(
        orders=OrdersConfig(movement={"still": [["A"]]}),
        models=[_model(equipment=[hide])],
    )
    deck = build_deck(
        _army(unit, race="goblin"), stem="test", image_for=FakeLookup(None)
    )

    out = render(
        CARDS, deck, fmt=get_format("latex"), name="test", output_root=tmp_path
    )

    text = out.read_text(encoding="utf-8")
    # The name is LaTeX-escaped, and `\flhead` wraps it within the card box.
    assert r"\renewcommand{\flhead}{Movement\\Hide \& Seek}" in text
    # The base card of the same Unit still names the kind alone, and the back
    # of an equipment card carries no equipment name at all.
    assert r"\renewcommand{\flhead}{Movement}" in text
    assert r"\renewcommand{\bcfoot}{Movement}" in text
    assert not any("Hide" in line for line in text.splitlines() if "bcfoot" in line)


def test_cards_latex_back_falls_back_to_text_without_art(tmp_path: Path) -> None:
    out = render(
        CARDS,
        _art_deck(None),
        fmt=get_format("latex"),
        name="test",
        output_root=tmp_path,
    )

    text = out.read_text(encoding="utf-8")
    assert r"\includegraphics" not in text
    # The name and kind still identify the back of an art-less card.
    assert r"\renewcommand{\bchead}{Squad}" in text
    assert r"\renewcommand{\bcfoot}{Movement}" in text
    # `\cardtext` ends the body with `\\`, so an empty body is a LaTeX error.
    assert r"\strut" in text


@pytest.mark.skipif(shutil.which(ENGINE) is None, reason=f"{ENGINE} not installed")
def test_cards_pdf_compiles_with_a_mixed_deck(tmp_path: Path) -> None:
    # A deck where one Unit has art and one does not is the case that breaks if
    # the art-less back leaves `\cardtext`'s body empty.
    art = Path(__file__).parent.parent / "fixtures" / "tiny_art.png"
    orders = OrdersConfig(movement={"still": [["A"]]}, fire={"still": [["F"]]})
    with_art = _unit(orders=orders, name="Painted")
    # The longest equipment name in any race is 44 characters; `\flhead` must
    # wrap it inside the card box rather than overfull the line.
    longest = _equip(
        OrdersConfig(movement={"crawl": [["C"]]}),
        name="Double Barreled Musket with Springloaded Axe",
    )
    without_art = _unit(
        orders=orders, name="Bare", models=[_model(equipment=[longest])]
    )

    def image_for(_race: str, name: str) -> Path | None:
        return art if name == "Painted" else None

    deck = build_deck(
        _army(with_art, without_art, race="goblin"), stem="test", image_for=image_for
    )

    out = render(CARDS, deck, fmt=get_format("pdf"), name="test", output_root=tmp_path)

    assert out.stat().st_size > 0


def test_render_cards_no_images_omits_committed_art(tmp_path: Path) -> None:
    # The demo army's race has committed Unit art, so the default render does
    # embed images — `--no-images` is what removes them.
    with_art = tmp_path / "with-art.md"
    render_cards(DEMO_ARMY, opts=RenderOpts(format="markdown", out=with_art))
    assert "![" in with_art.read_text(encoding="utf-8")

    out = tmp_path / "no-art.md"
    render_cards(DEMO_ARMY, opts=RenderOpts(format="markdown", out=out, no_images=True))

    assert "![" not in out.read_text(encoding="utf-8")


def test_render_cards_missing_army_exits_nonzero(tmp_path: Path) -> None:
    out = tmp_path / "missing.md"
    with pytest.raises(SystemExit) as excinfo:
        render_cards("no-such-army", opts=RenderOpts(format="markdown", out=out))

    assert excinfo.value.code == 1
    assert not out.exists()


# --- Golden output: pins the Order Card deck, and with it the Speed order ---
#
# Speeds render in the `speed` registry's declaration order, so a reordering of
# `rules/modifiers.toml` silently reshuffles every orders table. The demo Army's
# Goblin Infantry has both a `sneak` and a `slow` movement row, which is what
# makes such a reordering visible here.

GOLDEN_DIR = Path(__file__).parent.parent / "fixtures" / "golden"


def test_merged_orders_place_sneak_after_fast() -> None:
    orders = OrdersConfig(movement={"sneak": [["S"]], "slow": [["L"]], "fast": [["F"]]})

    merged = _unit(orders=orders).orders()

    assert list(merged.movement or {}) == ["slow", "fast", "sneak"]


@pytest.mark.usefixtures("pinned_version")
def test_cards_markdown_output_matches_golden_file(tmp_path: Path) -> None:
    out = tmp_path / "demo.md"

    render_cards(DEMO_ARMY, opts=RenderOpts(format="markdown", out=out, no_images=True))

    golden = (GOLDEN_DIR / "cards.md").read_text(encoding="utf-8")
    assert out.read_text(encoding="utf-8").rstrip("\n") == golden.rstrip("\n")
