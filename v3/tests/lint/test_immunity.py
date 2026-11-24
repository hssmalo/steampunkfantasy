"""Tests for the rule that a Unit with no Bio Model states its poison immunity."""

from spf.lint import immunity
from tests.conftest import synthetic_model, synthetic_unit


def test_a_unit_with_no_bio_model_and_no_immunity_is_reported() -> None:
    """A drone is not alive, so its card must say poison cannot touch it."""
    unit = synthetic_unit(models=["drone"])
    models = {"drone": synthetic_model(type=["Drone", "Mechanical"])}

    message = immunity.check_poison_immunity(unit, models)

    assert message == "no Model is Bio, so the Unit needs Immunity [damage_type.poison]"


def test_a_unit_stating_its_poison_immunity_is_silent() -> None:
    """The Instance the rule asks for is what satisfies it."""
    unit = synthetic_unit(
        models=["drone"],
        specials={"immunity": [{"args": {"feature": "damage_type.poison"}}]},
    )
    models = {"drone": synthetic_model(type=["Drone", "Mechanical"])}

    assert immunity.check_poison_immunity(unit, models) is None


def test_a_unit_of_bio_models_needs_no_immunity() -> None:
    """Poison is meant to reach living Models."""
    unit = synthetic_unit(models=["soldier", "soldier"])
    models = {"soldier": synthetic_model(type=["Bio", "Infantry"])}

    assert immunity.check_poison_immunity(unit, models) is None


def test_a_bio_crew_vehicle_is_not_bio() -> None:
    """The crew is alive but the machine is not, so the tank is immune."""
    unit = synthetic_unit(models=["tank"])
    models = {"tank": synthetic_model(type=["Vehicle", "Mechanical", "Bio Crew"])}

    assert immunity.check_poison_immunity(unit, models) is not None


def test_a_unit_mixing_bio_and_non_bio_models_is_left_to_the_designer() -> None:
    """A Unit-wide immunity would also shield the living Model riding along."""
    unit = synthetic_unit(models=["officer", "drone"])
    models = {
        "officer": synthetic_model(type=["Bio", "Infantry"]),
        "drone": synthetic_model(type=["Drone", "Mechanical"]),
    }

    assert immunity.check_poison_immunity(unit, models) is None
