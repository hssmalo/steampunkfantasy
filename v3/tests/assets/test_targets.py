"""The Targets a Kind covers for a Race, resolved from the Race TOML alone."""

import operator
from pathlib import Path

import pytest

from spf.assets import Kind, targets
from spf.config import config
from spf.schemas.race import RaceConfig, RaceMetadata
from tests.assets.conftest import FakeService
from tests.conftest import (
    synthetic_model,
    synthetic_race,
    synthetic_unit,
    write_race_toml,
)

_DESCRIPTION = "A cunning raider, clad in brass plate."
"""The Race's own Brief text, the one a race-level Kind is generated from."""


def _race() -> RaceConfig:
    """Build a Race whose Units and Models are declared out of alphabetical order.

    Coverage follows the order the TOML declares, so a Race whose keys sort
    differently is what makes that assertion mean anything.
    """
    race = synthetic_race(
        units={
            "infantry": synthetic_unit(name="Infantry", models=["grunt"]),
            "troll": synthetic_unit(name="Troll", models=["brute"]),
            "champion": synthetic_unit(name="Champion", models=["grunt"]),
        },
        models={
            "grunt": synthetic_model(name="Grunt"),
            "brute": synthetic_model(name="Brute"),
        },
    )
    described = RaceMetadata(name="Goblin", description=_DESCRIPTION)
    return race.model_copy(update={"races": {"goblin": described}})


@pytest.fixture(autouse=True)
def _race_on_disk(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Resolve every Target in this module against a Race the test wrote."""
    write_race_toml(tmp_path, _race())
    monkeypatch.setattr(config.paths, "races", tmp_path)


def test_race_level_kind_covers_the_race_itself() -> None:
    kind = Kind(
        name="_lore",
        service_factory=lambda: FakeService(),  # noqa: PLW0108
        subdir="_lore",
        extension="txt",
        targets=frozenset({"race"}),
        brief=operator.attrgetter("description"),
    )

    found = targets(kind, "goblin")

    assert [target.name for target in found] == ["goblin"]
    assert found[0].level == "race"
    assert found[0].human_name == "Goblin"


def test_unit_level_kind_covers_the_race_then_its_units(test_kind: Kind) -> None:
    # `test_kind` declares {"race", "unit"}, matching the image Kind. Coverage
    # follows the Race's declaration order, not cost order as `race things`
    # does, and not the alphabetical order these keys would sort into.
    found = targets(test_kind, "goblin")

    assert [target.name for target in found] == [
        "goblin",
        "infantry",
        "troll",
        "champion",
    ]
    assert {target.level for target in found[1:]} == {"unit"}


def test_model_level_kind_covers_the_races_models() -> None:
    # No Kind targets models yet; the field is the hook the Model Kind lands on.
    kind = Kind(
        name="_model",
        service_factory=lambda: FakeService(),  # noqa: PLW0108
        subdir="_model",
        extension="stl",
        targets=frozenset({"model"}),
        brief=operator.attrgetter("description"),
    )

    found = targets(kind, "goblin")

    assert [target.name for target in found] == ["grunt", "brute"]
    assert {target.level for target in found} == {"model"}


def test_kind_declares_which_text_its_targets_are_briefed_from() -> None:
    # The Brief is whatever the Kind says it is, so a Kind that generates from
    # something other than `description` needs no change here (ADR 0014).
    kind = Kind(
        name="_named",
        service_factory=lambda: FakeService(),  # noqa: PLW0108
        subdir="_named",
        extension="txt",
        targets=frozenset({"race"}),
        brief=lambda entry: entry.name.upper(),
    )

    found = targets(kind, "goblin")

    assert found[0].brief == "GOBLIN"


def test_brief_is_whitespace_normalized() -> None:
    # Briefs are authored as multi-line TOML strings, but a Brief is one
    # paragraph of prose: it is normalized here rather than at display, so the
    # text sent to the Service is the text shown (ADR 0014).
    kind = Kind(
        name="_ragged",
        service_factory=lambda: FakeService(),  # noqa: PLW0108
        subdir="_ragged",
        extension="txt",
        targets=frozenset({"race"}),
        brief=lambda _entry: "  A brutal raider,\n  clad in   brass plate.\n",
    )

    found = targets(kind, "goblin")

    assert found[0].brief == "A brutal raider, clad in brass plate."


def test_a_kind_can_compose_its_brief_from_several_fields() -> None:
    # Regression guard for the callable (ADR 0014): a Kind's Brief need not be
    # one field, so `brief` cannot be narrowed to a field name or a bool.
    kind = Kind(
        name="_composed",
        service_factory=lambda: FakeService(),  # noqa: PLW0108
        subdir="_composed",
        extension="txt",
        targets=frozenset({"race"}),
        brief=lambda entry: f"{entry.name}: {entry.description}",
    )

    found = targets(kind, "goblin")

    assert found[0].brief == f"Goblin: {_DESCRIPTION}"
