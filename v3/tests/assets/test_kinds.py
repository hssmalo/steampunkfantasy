"""S1: the Kind record and its registry mechanism."""

import pytest

import spf.assets.image  # noqa: F401  self-registers the "image" kind on import
from spf.assets import Kind, get_kind, register_kind
from spf.assets.kinds import KINDS


def test_concrete_kind_self_registers_on_import() -> None:
    # Importing a concrete kind module registers it globally; the "image" kind
    # (#25) is the first, so the registry is no longer empty once it is loaded.
    assert "image" in KINDS


def test_register_and_look_up(test_kind: Kind) -> None:
    try:
        registered = register_kind(test_kind)
        assert get_kind("_test") is registered
    finally:
        KINDS.pop("_test", None)


def test_unknown_kind_raises_naming_known_kinds(test_kind: Kind) -> None:
    try:
        register_kind(test_kind)
        with pytest.raises(ValueError, match="Unknown kind 'nope'") as excinfo:
            get_kind("nope")
        assert "_test" in str(excinfo.value)
    finally:
        KINDS.pop("_test", None)
