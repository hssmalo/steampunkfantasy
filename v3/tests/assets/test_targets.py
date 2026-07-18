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
