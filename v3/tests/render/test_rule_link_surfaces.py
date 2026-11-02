"""No surface prints a Rule Link's raw syntax (ADR 0042).

A link authored anywhere it is allowed reaches a lot of places, and a surface
that forgets to reduce it prints `{label:namespace.id}` to a player. So each
surface here reads one synthetic Race or Rulebook.

The documents render through the production templates, a deliberate exemption
from `docs/agents/testing.md`. The only assertion on their output is that the raw
Ref is absent, so no edit to a template's content can fail one of these unless it
leaks the syntax. Each test first shows that what its surface reads carries a
link, because without one the absence would prove nothing.
"""

from collections.abc import Callable
from pathlib import Path

import pytest

from spf.armies.io import load_army, print_army, print_army_rules
from spf.frontends.cli.race import show_race
from spf.frontends.cli.render import (
    RenderOpts,
    render_army_pack,
    render_army_rules,
    render_general_rules,
    render_race_overview,
)
from spf.frontends.cli.special import list_specials, show_special
from spf.races import get_race
from spf.schemas import rules as r
from spf.schemas.race import RaceConfig
from tests.conftest import (
    InstallRegistry,
    army_json,
    synthetic_assault,
    synthetic_equipment,
    synthetic_model,
    synthetic_race,
    synthetic_registry,
    synthetic_special,
    synthetic_unit,
    write_army_json,
    write_race_toml,
)

LINK = "{it:damage_type.poison}"
RAW = ":damage"
"""What survives of the syntax in any output: LaTeX escapes the braces around it
and the underscore after it, and Rich may wrap the line at either end."""

REGISTRY = synthetic_registry(
    specials={
        "linked": synthetic_special(
            name="Linked",
            effect=f"Effect {LINK}.",
            example=f"Example {LINK}.",
            variants={"pooled": f"Variant {LINK}."},
            versions={"damage_type.poison": {"effect": f"Version {LINK}."}},
        ),
    },
    records={
        "token": {
            "marked": r.TokenRuleConfig(
                name="Marked",
                effect=f"Effect {LINK}.",
                remove=f"Remove {LINK}.",
                example=f"Example {LINK}.",
            ),
        },
    },
)


def _race() -> RaceConfig:
    """Build a Race with a Rule Link in every field that may hold one."""
    specials = {
        "linked": [
            {"text": f"Text {LINK}."},
            {"variant": "pooled"},
            {"preamble": f"Preamble {LINK}.", "cases": [{"text": f"Case {LINK}."}]},
        ]
    }
    return synthetic_race(
        units={
            "squad": synthetic_unit(
                note=f"Note {LINK}.",
                specials=specials,
                damage_tables={
                    "Regular": {"rows": [f"1: Row {LINK}"], "notes": [f"Note {LINK}."]}
                },
            )
        },
        models={
            "soldier": synthetic_model(
                note=f"Note {LINK}.",
                assault=synthetic_assault(note=f"Note {LINK}."),
                equipment=["knife", "gun"],
            )
        },
        equipment={
            "knife": synthetic_equipment(
                name="Knife",
                cost=None,
                upgrade_all=None,
                note=f"Note {LINK}.",
                assault={"note": f"Note {LINK}."},
            ),
            "gun": synthetic_equipment(
                name="Gun",
                cost=None,
                upgrade_all=None,
                range={
                    "range": "6",
                    "angle": [1, 0, 0, 0],
                    "damage": "d4",
                    "ap": 0,
                    "note": f"Note {LINK}.",
                },
            ),
        },
    )


def _rulebook_index(directory: Path) -> Path:
    """Write a Rulebook whose Records author Rule Links, returning its Index."""
    (directory / "tokens.toml").write_text(
        'explanation = "Tokens."\n[tokens.marked]\nname = "Marked"\n'
        f'effect = "Effect {LINK}."\nremove = "Remove {LINK}."\n'
        f'example = "Example {LINK}."\n'
    )
    (directory / "hexes.toml").write_text(
        'explanation = "Hexes."\n[hexes.marked]\nname = "Marked"\n'
        f'effect = "Effect {LINK}."\nremove = "Remove {LINK}."\n'
        f'example = "Example {LINK}."\n'
    )
    (directory / "special.toml").write_text(
        '[special.linked]\nname = "Linked"\nslots = ["unit"]\n'
        f'effect = "Effect {LINK}."\nexample = "Example {LINK}."\n'
        f'[special.linked.variants]\npooled = "Variant {LINK}."\n'
        '[special.linked.versions."damage_type.poison"]\n'
        f'effect = "Version {LINK}."\n'
    )
    (directory / "modifiers.toml").write_text(
        "".join(
            f'[{table}.one]\nname = "One"\nto_hit = "+1"\neffect = "Short {LINK}."\n'
            for table in ("speed", "distance", "angle", "size", "ability")
        )
    )
    index = directory / "rulebook.toml"
    sections = {
        "tokens": "tokens.toml",
        "hexes": "hexes.toml",
        "specials": "special.toml",
        "to_hit": "modifiers.toml",
    }
    index.write_text(
        'title = "Rulebook"\n'
        + "".join(
            f'[[sections]]\nkind = "{kind}"\nsource = "{source}"\ntitle = "{kind}"\n'
            for kind, source in sections.items()
        )
    )
    return index


@pytest.fixture
def corpus(
    install_registry: InstallRegistry,
    races_dir: Path,
    armies_dir: Path,
) -> None:
    """Install the synthetic Registry, Race and Army the surfaces read."""
    install_registry(REGISTRY)
    race = _race()
    write_race_toml(races_dir, race)
    write_army_json(armies_dir, "linked", army_json(race))


_RACE_NAME = "goblin"


def _prose_the_army_reads() -> str:
    """Return the Unit note every Army surface reads from the loaded Army."""
    return load_army("linked").units[0].config.note


def _prose_the_race_reads() -> str:
    """Return a Unit note from the loaded Race."""
    return get_race(_RACE_NAME).units["squad"].note


def _prose_the_registry_reads() -> str | None:
    """Return the Special's effect from the installed Registry."""
    return REGISTRY.specials["linked"].effect


_PRODUCTS: dict[str, tuple[Callable[[RenderOpts], None], Callable[[], object]]] = {
    "army-rules": (
        lambda opts: render_army_rules("linked", opts=opts),
        _prose_the_army_reads,
    ),
    "army-pack": (
        lambda opts: render_army_pack("linked", opts=opts),
        _prose_the_army_reads,
    ),
    "race-overview": (
        lambda opts: render_race_overview(_RACE_NAME, opts=opts),
        _prose_the_race_reads,
    ),
}


@pytest.mark.usefixtures("corpus")
def test_the_race_carries_a_link_in_every_field_that_allows_one() -> None:
    race = _race()
    squad, soldier = race.units["squad"], race.models["soldier"]
    knife, gun = race.equipment["knife"], race.equipment["gun"]
    table = squad.damage_tables["Regular"]
    assert knife.assault is not None
    assert gun.range is not None
    instances = squad.specials["linked"]

    prose = [
        squad.note,
        table.rows[0].effect,
        table.notes[0],
        soldier.note,
        soldier.assault.note,
        knife.note,
        knife.assault.note,
        gun.range.note,
        instances[0].text,
        instances[2].preamble,
        instances[2].cases[0].text,
        REGISTRY.specials["linked"].variants["pooled"],
    ]

    assert all(LINK in (text or "") for text in prose)


@pytest.mark.usefixtures("corpus")
@pytest.mark.parametrize("product", _PRODUCTS)
@pytest.mark.parametrize("output_format", ["markdown", "latex"])
@pytest.mark.parametrize("no_rules", [False, True], ids=["rules", "no-rules"])
def test_no_document_prints_raw_link_syntax(
    tmp_path: Path, product: str, output_format: str, *, no_rules: bool
) -> None:
    render, carrier = _PRODUCTS[product]
    assert LINK in str(carrier())
    out = tmp_path / "document"

    render(RenderOpts(format=output_format, out=out, no_rules=no_rules))

    assert RAW not in out.read_text()


@pytest.mark.usefixtures("corpus")
@pytest.mark.parametrize("output_format", ["markdown", "latex"])
def test_the_rulebook_prints_no_raw_link_syntax(
    tmp_path: Path, output_format: str
) -> None:
    out = tmp_path / "rulebook"
    index = _rulebook_index(tmp_path)
    assert LINK in (tmp_path / "tokens.toml").read_text()

    render_general_rules(index=index, opts=RenderOpts(format=output_format, out=out))

    assert RAW not in out.read_text()


_CONSOLE: dict[str, tuple[Callable[[], None], Callable[[], object]]] = {
    "army-rules": (
        lambda: print_army_rules(load_army("linked")),
        _prose_the_army_reads,
    ),
    "army": (lambda: print_army(load_army("linked")), _prose_the_army_reads),
    "race-show": (lambda: show_race(_RACE_NAME), _prose_the_race_reads),
    "race-show-section": (
        lambda: show_race(_RACE_NAME, "units"),
        _prose_the_race_reads,
    ),
    "special-show": (lambda: show_special("linked"), _prose_the_registry_reads),
    "special-list": (list_specials, _prose_the_registry_reads),
}


@pytest.mark.usefixtures("corpus")
@pytest.mark.parametrize("surface", _CONSOLE)
def test_the_console_prints_no_raw_link_syntax(
    capsys: pytest.CaptureFixture[str], surface: str
) -> None:
    show, carrier = _CONSOLE[surface]
    assert LINK in str(carrier())

    show()

    assert RAW not in capsys.readouterr().out
