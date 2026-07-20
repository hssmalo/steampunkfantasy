"""Tests for the pure name-linting predicates.

Table-driven over plain strings: no fixtures, no disk, no Race schema. The
rules are string predicates precisely so these tests stay this cheap.
"""

import pytest

from spf.lint import rules
from spf.schemas.config import LintConfig

CONVENTIONS = LintConfig(
    aliases={"darkelf": "dark_elf"},
    optional_key_prefixes=["greater_"],
    optional_key_suffixes=["_free"],
    function_words=["of", "with", "in"],
)


@pytest.mark.parametrize(
    ("name", "expected"),
    [
        ("Elf Bow", "elf_bow"),
        ("Ballista Tractor, Mark I", "ballista_tractor_mark_i"),
        ("Mortar 1.1B", "mortar_1_1b"),
        ("Frost 88", "frost_88"),
        ("Long_Range Musket", "long_range_musket"),
        ("  Padded  ", "padded"),
    ],
)
def test_slugify(name: str, expected: str) -> None:
    """Names lowercase, and runs of non-alphanumerics collapse to one '_'."""
    assert rules.slugify(name) == expected


@pytest.mark.parametrize(
    ("name", "expected"),
    [
        ("SteamPowerArmor", "steampowerarmor"),
        ("MechaHydra", "mechahydra"),
        ("BioEngineered Ork", "bioengineered_ork"),
        ("TeslaBurstLaser", "teslaburstlaser"),
        ("PentaGun", "pentagun"),
    ],
)
def test_slugify_does_not_split_camel_case(name: str, expected: str) -> None:
    """CamelCase is the game's naming aesthetic, not a word boundary.

    `SteamPowerArmor` is one word, so it slugs to `steampowerarmor` and
    *never* to `steam_power_armor`. Splitting on case would flag the whole
    CamelCase population of the data as broken.
    """
    assert rules.slugify(name) == expected


@pytest.mark.parametrize(
    ("key", "name"),
    [
        ("elf_bow", "Elf Bow"),
        ("frost_88", "Frost 88"),
        ("elite_steampowerarmor", "Elite SteamPowerArmor"),
        ("bow_with_rocket_arrows", "Bow with Rocket Arrows"),
    ],
)
def test_key_name_accepts_agreement(key: str, name: str) -> None:
    """A key that slugifies from its own name is clean."""
    assert rules.check_key_name(key, name, CONVENTIONS) is None


@pytest.mark.parametrize(
    ("key", "name"),
    [
        ("sauropod_riders", "Sauropod Rider"),
        ("polar_bear_riders", "Dire Polar Bear Riders"),
        ("frost88", "Frost 88"),
        ("confusiator", "Confusiator Tank"),
    ],
)
def test_key_name_rejects_disagreement(key: str, name: str) -> None:
    """Number and content disagreements both fall out of slug comparison."""
    message = rules.check_key_name(key, name, CONVENTIONS)

    assert message is not None
    assert key in message
    assert name in message


@pytest.mark.parametrize(
    ("key", "name"),
    [
        ("darkelf_infantry", "Dark Elf Infantry"),
        ("elite_darkelf_infantry", "Elite Dark Elf Infantry"),
        ("roboprosthetic_darkelf", "Roboprosthetic Dark Elf"),
    ],
)
def test_alias_expands_the_key(key: str, name: str) -> None:
    """An alias rewrites the key, including mid-key, before comparing."""
    assert rules.check_key_name(key, name, CONVENTIONS) is None


@pytest.mark.parametrize(
    ("key", "name"),
    [
        ("darkelf_infantry", "Darkelf Infantry"),
        ("darkelf_elite_infantry", "DarkElf Elite Infantry"),
        ("elite_darkelf_infantry", "Elite Darkelf Infantry"),
    ],
)
def test_alias_is_unidirectional(key: str, name: str) -> None:
    """The alias rewrites the key only; the name must match the expansion.

    This is the load-bearing direction. `darkelf` requires the name to say
    "Dark Elf" -- "Darkelf" and "DarkElf" are both rejected. A bidirectional
    alias would silently accept all three spellings, which is the exact
    defect class the linter exists to catch.
    """
    assert rules.check_key_name(key, name, CONVENTIONS) is not None


@pytest.mark.parametrize(
    ("key", "name"),
    [
        ("bow_free", "Bow"),
        ("elf_bow_free", "Elf Bow Free"),
        ("greater_healing", "Healing"),
        ("greater_healing", "Greater Healing"),
    ],
)
def test_optional_affixes_are_accepted_either_way(key: str, name: str) -> None:
    """A key may carry `_free` or `greater_` that its name omits."""
    assert rules.check_key_name(key, name, CONVENTIONS) is None


@pytest.mark.parametrize(
    "name", ["Pegasus_rider", "Deflection_field", "Assault_Musket"]
)
def test_no_underscore_rejects_leaked_keys(name: str) -> None:
    """An underscore in a display name is a key string that leaked."""
    assert rules.check_no_underscore(name) is not None


def test_no_underscore_accepts_clean_name() -> None:
    """A name without underscores passes."""
    assert rules.check_no_underscore("Pegasus Rider") is None


@pytest.mark.parametrize(
    "name",
    [
        "Elite Elf Scout",
        "Musket with Springloaded Axe",
        "Trench Coat of Resistance",
        "Ballista Tractor, Mark III",
        "Frost 88",
        "Mortar 1.1B",
        "SteamPowerArmor Engineer",
        "AT Rifle",
        "Queen XY",
        "In Formation",
    ],
)
def test_title_case_accepts(name: str) -> None:
    """CamelCase, acronyms and digits pass; only lowercase words are flagged.

    "In Formation" shows a function word is *not* lowercased in first
    position -- it is only mid-name that `in` must stay lowercase.
    """
    assert rules.check_title_case(name, CONVENTIONS.function_words) is None


@pytest.mark.parametrize(
    "name",
    ["Elite Elf scout", "Goblin bow", "dw42", "Helicopter mounted Green Gas Launcher"],
)
def test_title_case_rejects_lowercase_words(name: str) -> None:
    """Every word must start uppercase unless it is a function word."""
    assert rules.check_title_case(name, CONVENTIONS.function_words) is not None


@pytest.mark.parametrize(
    "name",
    [
        "Musket With Springloaded Axe",
        "Trench Coat Of Resistance",
        "Bow With Rocket Arrows",
    ],
)
def test_title_case_requires_lowercase_function_words(name: str) -> None:
    """Function words are mandatory-lowercase, not merely permitted to be.

    Permitting both spellings is what let `Musket With Springloaded Axe` and
    `Bow with Rocket Arrows` coexist in the data.
    """
    assert rules.check_title_case(name, CONVENTIONS.function_words) is not None


@pytest.mark.parametrize("key", ["ballista_tractor_markI", "ballista_tractor_MarkIII"])
def test_key_lowercase_rejects(key: str) -> None:
    """Keys carrying uppercase are flagged."""
    assert rules.check_key_lowercase(key) is not None


def test_key_lowercase_accepts() -> None:
    """An all-lowercase key passes."""
    assert rules.check_key_lowercase("ballista_tractor_mark_iii") is None


def test_capitalized_rejects_lowercase_race_name() -> None:
    """A Race's display name must be capitalized."""
    assert rules.check_capitalized("gnome") is not None


def test_capitalized_accepts() -> None:
    """A capitalized Race name passes."""
    assert rules.check_capitalized("Gnome") is None
