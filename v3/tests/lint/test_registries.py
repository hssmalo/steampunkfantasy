"""Tests for the registry linter.

`lint_registry` takes an already-loaded `Registry`, so these build tiny ones by
hand: what is under test is which findings the walk produces, not what is on
disk.
"""

from spf.lint import registries
from spf.registry import Registry
from spf.schemas import rules as r
from spf.schemas.config import LintConfig

CONVENTIONS = LintConfig(function_words=["of", "with", "in"])

NAMESPACES = {
    "special": r.NamespaceConfig(name="Specials", file="special.toml", table="special"),
    "token": r.NamespaceConfig(name="Tokens", file="tokens.toml", table="tokens"),
}


def _registry(records: dict[str, dict[str, r.RuleRecord]]) -> Registry:
    """Build a registry over the two namespaces these tests address."""
    return Registry(records=records, namespaces=NAMESPACES)


def _special(name: str) -> r.SpecialRuleConfig:
    """Build a written Special record: completeness is not under test here."""
    return r.SpecialRuleConfig(name=name, slots=["unit"], effect="Something happens")


def test_clean_registry_is_silent() -> None:
    """Records whose key is the slug of their name produce no findings."""
    records: dict[str, r.RuleRecord] = {
        "cunning_deflection": _special("Cunning Deflection")
    }
    registry = _registry({"special": records})

    assert registries.lint_registry(registry, CONVENTIONS) == []


def test_finding_locates_the_record() -> None:
    """A finding carries the file, namespace, key and rule that name it."""
    registry = _registry({"special": {"reroll": _special("Ork Reroll")}})

    (finding,) = registries.lint_registry(registry, CONVENTIONS)

    assert finding.file == "special.toml"
    assert finding.namespace == "special"
    assert finding.key == "reroll"
    assert finding.rule == "key-name"


def test_every_namespace_is_walked() -> None:
    """A namespace is linted whatever file its records were read from."""
    registry = _registry(
        {
            "special": {"fear": _special("Fear")},
            "token": {"aim": r.TokenRuleConfig(name="aim", effect="Take aim")},
        }
    )

    findings = registries.lint_registry(registry, CONVENTIONS)

    assert [(finding.namespace, finding.rule) for finding in findings] == [
        ("token", "title-case")
    ]


def test_trailing_space_in_a_name_is_a_finding() -> None:
    """A name differing from its key by whitespace alone is still a mismatch."""
    registry = _registry(
        {"token": {"aim": r.TokenRuleConfig(name="Aim ", effect="Take aim")}}
    )

    assert [f.rule for f in registries.lint_registry(registry, CONVENTIONS)] == [
        "trimmed"
    ]
