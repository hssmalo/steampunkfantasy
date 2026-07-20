"""The Targets a Kind covers for a Race, resolved from the Race TOML alone."""

import operator

from spf.assets import Kind, targets
from tests.assets.conftest import FakeService


def test_race_level_kind_covers_the_race_itself() -> None:
    kind = Kind(
        name="_lore",
        service=FakeService(),
        subdir="_lore",
        extension="txt",
        targets=frozenset({"race"}),
        brief=operator.attrgetter("description"),
    )

    found = targets(kind, "ork")

    assert [target.name for target in found] == ["ork"]
    assert found[0].level == "race"
    assert found[0].human_name == "Ork"


def test_unit_level_kind_covers_the_race_then_its_units(test_kind: Kind) -> None:
    # `test_kind` declares {"race", "unit"}, matching the image Kind. Ork's unit
    # keys, in `races/ork.toml` declaration order — coverage follows the TOML,
    # not cost order as `race things` does.
    found = targets(test_kind, "ork")

    assert [target.name for target in found] == [
        "ork",
        "ork_infantry",
        "troll",
        "champion",
        "warg_rider",
        "speedhead",
        "hammerhead",
        "battlewagon",
        "grunt",
        "ork_werewarg",
        "bioengineered_ork",
        "ork_char_b1",
    ]
    assert {target.level for target in found[1:]} == {"unit"}


def test_model_level_kind_covers_the_races_models() -> None:
    # No Kind targets models yet; the field is the hook the Model Kind lands on.
    kind = Kind(
        name="_model",
        service=FakeService(),
        subdir="_model",
        extension="stl",
        targets=frozenset({"model"}),
        brief=operator.attrgetter("description"),
    )

    found = targets(kind, "ork")

    assert [target.name for target in found][:3] == [
        "troll",
        "grunt",
        "elite_ork_infantry",
    ]
    assert {target.level for target in found} == {"model"}


def test_kind_declares_which_text_its_targets_are_briefed_from() -> None:
    # The Brief is whatever the Kind says it is, so a Kind that generates from
    # something other than `description` needs no change here (ADR 0014).
    kind = Kind(
        name="_named",
        service=FakeService(),
        subdir="_named",
        extension="txt",
        targets=frozenset({"race"}),
        brief=lambda entry: entry.name.upper(),
    )

    found = targets(kind, "ork")

    assert found[0].brief == "ORK"


def test_brief_is_whitespace_normalized() -> None:
    # Briefs are authored as multi-line TOML strings, but a Brief is one
    # paragraph of prose: it is normalized here rather than at display, so the
    # text sent to the Service is the text shown (ADR 0014).
    kind = Kind(
        name="_ragged",
        service=FakeService(),
        subdir="_ragged",
        extension="txt",
        targets=frozenset({"race"}),
        brief=lambda _entry: "  A brutal raider,\n  clad in   brass plate.\n",
    )

    found = targets(kind, "ork")

    assert found[0].brief == "A brutal raider, clad in brass plate."


def test_a_kind_can_compose_its_brief_from_several_fields() -> None:
    # Regression guard for the callable (ADR 0014): a Kind's Brief need not be
    # one field, so `brief` cannot be narrowed to a field name or a bool.
    kind = Kind(
        name="_composed",
        service=FakeService(),
        subdir="_composed",
        extension="txt",
        targets=frozenset({"race"}),
        brief=lambda entry: f"{entry.name}: {entry.description}",
    )

    found = targets(kind, "ork")

    assert found[0].brief.startswith("Ork: ")
    assert len(found[0].brief) > len("Ork: ")
