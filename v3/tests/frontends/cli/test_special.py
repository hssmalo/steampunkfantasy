"""Tests for the rows `spf special list` prints.

`special_rows` is a pure function over the Registry, so most of these build
`SpecialRuleConfig` records by hand rather than coupling to `rules/special.toml`.
"""

from spf.frontends.cli.special import special_rows
from spf.registry import Registry
from spf.schemas.rules import SpecialRuleConfig


def _registry(**specials: SpecialRuleConfig) -> Registry:
    return Registry(records={"special": dict(specials)})


def _rule(**kwargs: object) -> SpecialRuleConfig:
    kwargs.setdefault("name", "Rule")
    kwargs.setdefault("slots", ["unit"])
    return SpecialRuleConfig.model_validate(kwargs)


def test_rows_come_back_sorted_by_identifier() -> None:
    registry = _registry(
        zeal=_rule(effect="Zealous."),
        aim=_rule(effect="Aimed."),
        march=_rule(effect="Marching."),
    )

    rows = special_rows(registry)

    assert [row.label for row in rows] == ["aim", "march", "zeal"]
