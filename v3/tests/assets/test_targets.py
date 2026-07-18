"""The Targets a Kind covers for a Race, resolved from the Race TOML alone."""

from spf.assets import Kind, targets
from tests.assets.conftest import FakeService


def test_race_level_kind_covers_the_race_itself() -> None:
    kind = Kind(
        name="_lore",
        service=FakeService(),
        subdir="_lore",
        extension="txt",
        targets=frozenset({"race"}),
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
    )

    found = targets(kind, "ork")

    assert [target.name for target in found][:3] == [
        "troll",
        "grunt",
        "ork_elite_infantry",
    ]
    assert {target.level for target in found} == {"model"}
