"""Tests for the CLI's "Did you mean ...?" suggestion helper."""

import pytest

from spf.frontends.cli.suggest import _MAX_SUGGESTIONS, resolve_or_raise, suggest

OPTIONS = [
    "Ork Reroll",
    "Recoil",
    "Cunning Assault",
    "Cunning Deflection",
    "Cunning Assault Defense",
    "To Hit",
    "To Hit (2)",
    "To Hit (3)",
    "Sniper",
    "Take Cover",
]


def test_suggest_matches_a_substring() -> None:
    assert suggest("Reroll", OPTIONS) == ["Ork Reroll"]


def test_suggest_returns_a_whole_family_shortest_first() -> None:
    assert suggest("To Hit", OPTIONS) == ["To Hit", "To Hit (2)", "To Hit (3)"]


def test_suggest_returns_every_substring_match() -> None:
    assert set(suggest("Cunning", OPTIONS)) == {
        "Cunning Assault",
        "Cunning Deflection",
        "Cunning Assault Defense",
    }


def test_suggest_falls_back_to_fuzzy_matching() -> None:
    assert suggest("Snipr", OPTIONS) == ["Sniper"]


def test_suggest_is_empty_for_nonsense() -> None:
    assert suggest("zzz", OPTIONS) == []


def test_suggest_does_not_mix_fuzzy_into_substring_matches() -> None:
    # "Recoil" is a close fuzzy match for "Reroll" but not a substring one, so
    # the substring pass must shut the fuzzy pass out entirely.
    assert "Recoil" not in suggest("Reroll", OPTIONS)


def test_suggest_ignores_case_and_extra_whitespace() -> None:
    assert suggest("take   cover", OPTIONS) == ["Take Cover"]


def test_resolve_returns_an_exact_match_unchanged() -> None:
    assert resolve_or_raise("Ork Reroll", OPTIONS, noun="special", see="spf x") == (
        "Ork Reroll"
    )


def test_resolve_canonicalises_a_unique_case_insensitive_match() -> None:
    assert resolve_or_raise("take cover", OPTIONS, noun="special", see="spf x") == (
        "Take Cover"
    )


def test_resolve_raises_with_a_single_suggestion() -> None:
    with pytest.raises(ValueError, match=r"^Unknown special ") as excinfo:
        resolve_or_raise("Reroll", OPTIONS, noun="special", see="spf x")
    assert str(excinfo.value) == 'Unknown special "Reroll". Did you mean "Ork Reroll"?'


def test_resolve_raises_with_several_suggestions() -> None:
    with pytest.raises(ValueError, match=r"^Unknown special ") as excinfo:
        resolve_or_raise("Cunning", OPTIONS, noun="special", see="spf x")
    assert str(excinfo.value) == (
        'Unknown special "Cunning". Did you mean "Cunning Assault", '
        '"Cunning Deflection", or "Cunning Assault Defense"?'
    )


def test_resolve_points_at_the_listing_command_when_it_has_no_guess() -> None:
    with pytest.raises(ValueError, match=r"^Unknown special ") as excinfo:
        resolve_or_raise("zzz", OPTIONS, noun="special", see="spf rules specials")
    assert str(excinfo.value) == (
        "Unknown special \"zzz\". Run 'spf rules specials' to see all special rules."
    )


def test_suggest_normalizes_the_fuzzy_pass_too() -> None:
    # "SNIPR" is a substring of nothing, so it falls to the fuzzy pass — which
    # must fold case there as well, not only in the substring pass.
    assert suggest("SNIPR", OPTIONS) == ["Sniper"]


def test_resolve_does_not_dump_the_vocabulary_for_a_vague_value() -> None:
    # A one-letter value is a substring of nearly everything; listing all of it
    # is the wall of text the suggestions exist to replace.
    crowded = [f"Fire Order {n}" for n in range(_MAX_SUGGESTIONS + 1)]
    with pytest.raises(ValueError, match=r"^Unknown special ") as excinfo:
        resolve_or_raise("e", crowded, noun="special", see="spf rules specials")
    assert "Did you mean" not in str(excinfo.value)
    assert "spf rules specials" in str(excinfo.value)


def test_resolve_still_offers_a_whole_family() -> None:
    with pytest.raises(ValueError, match=r"^Unknown special ") as excinfo:
        resolve_or_raise("cunning", OPTIONS, noun="special", see="spf rules specials")
    assert "Did you mean" in str(excinfo.value)


def test_suggest_breaks_fuzzy_ties_the_way_substring_matches_break_them() -> None:
    # "tohit" reaches the fuzzy pass, where "To Hit (2)" and "To Hit (3)" score
    # identically — they must still come out shortest-then-alphabetical.
    assert suggest("tohit", OPTIONS) == ["To Hit", "To Hit (2)", "To Hit (3)"]
