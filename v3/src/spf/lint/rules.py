"""The name-consistency rules, as pure predicates over strings.

Every rule takes plain strings and returns the violation message, or `None`
when the input is clean. Nothing here reads disk, loads config, or touches a
Race schema -- a rule is testable with a single `(key, name)` pair.
"""

import re
from collections.abc import Collection

from spf.schemas.config import LintConfig

_NON_ALPHANUMERIC = re.compile(r"[^a-z0-9]+")


def slugify(name: str) -> str:
    """Lowercase `name`, collapse non-alphanumeric runs to '_', strip edges.

    Deliberately does **not** split on case boundaries. The data has a large,
    intentional CamelCase population -- `SteamPowerArmor`, `MechaHydra`,
    `WereWarg`, `PentaGun` -- alongside acronyms like `SMG` and `AT Rifle`.
    That is the game's naming aesthetic, not a defect, so `SteamPowerArmor`
    slugs to `steampowerarmor` and never to `steam_power_armor`.
    """
    return _NON_ALPHANUMERIC.sub("_", name.lower()).strip("_")


def _key_forms(key: str, conventions: LintConfig) -> set[str]:
    """Return the slugs `key` may legitimately be written as.

    Aliases are applied to the key **unidirectionally**: the key is rewritten
    to its canonical spelling and the raw key is *not* kept as an accepted
    form. That is what makes `darkelf_infantry` require the name "Dark Elf
    Infantry" while rejecting "Darkelf Infantry" -- keeping the raw key would
    accept both spellings and hide exactly the defects this rule exists for.
    """
    canonical = key
    for alias, expansion in conventions.aliases.items():
        canonical = canonical.replace(alias, expansion)

    forms = {canonical}
    for prefix in conventions.optional_key_prefixes:
        if canonical.startswith(prefix):
            forms.add(canonical.removeprefix(prefix))
    for suffix in conventions.optional_key_suffixes:
        if canonical.endswith(suffix):
            forms.add(canonical.removesuffix(suffix))
    return forms


def check_key_name(key: str, name: str, conventions: LintConfig) -> str | None:
    """Check that `key` is the slug of `name`, allowing optional affixes.

    Absorbs both number agreement (`sauropod_riders` vs 'Sauropod Rider') and
    content agreement (`polar_bear_riders` vs 'Dire Polar Bear Riders') --
    they are the same comparison.
    """
    if slugify(name) in _key_forms(key, conventions):
        return None
    return f"key {key!r} vs name {name!r}"


def check_no_underscore(name: str) -> str | None:
    """Check that no key string leaked into a display name."""
    if "_" in name:
        return f"name {name!r} contains an underscore"
    return None


def check_title_case(name: str, function_words: Collection[str]) -> str | None:
    """Check that every word starts uppercase, bar mid-name function words.

    Only the first character of each word is examined, so CamelCase and
    acronyms pass untouched, and words opening with a digit ('88', '1.1B')
    are not words this rule has an opinion about.

    Function words are mandatory-lowercase rather than merely permitted to
    be: allowing both spellings is what let 'Musket With Springloaded Axe'
    and 'Bow with Rocket Arrows' coexist. They are exempt in first position,
    where they are still capitalized like any other opening word.
    """
    for index, word in enumerate(name.split()):
        is_function_word = index > 0 and word.lower() in function_words
        if is_function_word and word != word.lower():
            return f"name {name!r} capitalizes the function word {word!r}"
        if not is_function_word and word[:1].islower():
            return f"name {name!r} has lowercase word {word!r}"
    return None


def check_key_lowercase(key: str) -> str | None:
    """Check that `key` carries no uppercase characters."""
    if key != key.lower():
        return f"key {key!r} is not lowercase"
    return None


def check_capitalized(name: str) -> str | None:
    """Check that `name` starts with a capital."""
    if name[:1].islower():
        return f"name {name!r} is not capitalized"
    return None
