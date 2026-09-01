"""The rule registries, and the hard gate over Special instances (ADR 0024).

A Race file names a rule by its identifier, so the identifier *is* the mapping
between the two files and is checked because it is the lookup key rather than a
claim about one. Everything here runs at load time: if a violation means the
resolver cannot produce correct output it is a schema failure, and only an
untidy corpus is left to lint.
"""

import re
from dataclasses import dataclass, field
from functools import cache
from pathlib import Path
from typing import cast

from spf import rules
from spf.config import config
from spf.schemas import rules as r
from spf.schemas.special import SpecialInstance, Specials

SPECIAL = "special"
"""The namespace a Special instance's id is looked up in."""

_REF = re.compile(r"^([a-z][a-z0-9_]*)\.([a-z][a-z0-9_]*)$")

LOADERS = {
    "special.toml": rules.get_specials,
    "tokens.toml": rules.get_tokens,
    "hexes.toml": rules.get_hexes,
    "terrain.toml": rules.get_terrain,
    "modifiers.toml": rules.get_modifiers,
    "namespaces.toml": rules.get_namespaces,
}
"""Every rules file, and the loader that reads it.

Public because `spf lint rules` reads one file at a time, so that a schema
failure names the file it was authored in rather than the whole registry."""


@dataclass(frozen=True)
class Registry:
    """Every namespace's records, keyed the way a ref addresses them.

    `records[namespace][id]` is the whole lookup surface: the namespace is an
    abstract name declared in `rules/namespaces.toml`, never a path into the
    file layout, which is what keeps a table rename out of the Race files.
    """

    records: dict[str, dict[str, r.RuleRecord]]
    namespaces: dict[str, r.NamespaceConfig] = field(default_factory=dict)

    @property
    def specials(self) -> dict[str, r.SpecialRuleConfig]:
        """The Special registry: the ids a Race file may write an instance of."""
        return cast("dict[str, r.SpecialRuleConfig]", self.records.get(SPECIAL, {}))

    def record(self, ref: str) -> r.RuleRecord | None:
        """Resolve a fully qualified reference, or None if it points nowhere."""
        match = _REF.match(ref)
        if match is None:
            return None
        namespace, identifier = match.groups()
        return self.records.get(namespace, {}).get(identifier)

    def display_name(self, ref: str) -> str:
        """Return a record's own name, which is how an identifier is printed.

        The registry is the single definition site for a name (ADR 0024), so a
        Race file spelling `size = "huge"` renders as the `size` registry says.
        A ref pointing nowhere falls back to its identifier rather than
        raising: the load-time gate is what rejects those.
        """
        record = self.record(ref)
        return record.name if record is not None else ref.partition(".")[2] or ref


def load_registry(rules_dir: Path | None = None) -> Registry:
    """Read every registry `rules/namespaces.toml` declares.

    Loading validates every record, so record completeness — exactly-one-of
    the meaning fields and `todo` — is checked here too, and a rules file that
    fails it fails every Race load with it.
    """
    return _load_registry(rules_dir if rules_dir is not None else config.paths.rules)


@cache
def _load_registry(rules_dir: Path) -> Registry:
    """Read and cache the registries under one rules directory."""
    namespaces = rules.get_namespaces(rules_dir / "namespaces.toml").namespaces
    wanted = {namespace.file for namespace in namespaces.values()}
    if unreadable := wanted - set(LOADERS):
        files = ", ".join(sorted(unreadable))
        msg = f"No loader for the rules file(s) a namespace declares: {files}"
        raise ValueError(msg)
    if dangling := {n.group for n in namespaces.values() if n.group} - set(namespaces):
        groups = ", ".join(sorted(dangling))
        msg = f"A namespace renders under an undeclared group: {groups}"
        raise ValueError(msg)
    loaded = {
        file_name: LOADERS[file_name](rules_dir / file_name) for file_name in wanted
    }
    registry = Registry(
        namespaces=namespaces,
        records={
            name: getattr(loaded[namespace.file], namespace.table)
            for name, namespace in namespaces.items()
        },
    )
    _check_version_keys(registry)
    return registry


def _check_version_keys(registry: Registry) -> None:
    """Resolve every version overlay's key, which is a ref like any other.

    An overlay is looked up by the ref an instance's version argument carries,
    so a key resolving to no record is prose no reader will ever see.
    """
    dangling = sorted(
        f"'{identifier}': {version}"
        for identifier, rule in registry.specials.items()
        for version in rule.versions
        if registry.record(version) is None
    )
    if dangling:
        refs = ", ".join(dangling)
        msg = f"A version overlay is keyed by a ref resolving to no record: {refs}"
        raise ValueError(msg)


def check_instances(
    specials: Specials, *, slot: r.Slot, context: str, registry: Registry
) -> list[str]:
    """Check one slot's instances against the registries, listing what is wrong.

    Every check is reported rather than raised, so one load names every broken
    instance instead of the first.
    """
    errors: list[str] = []
    for identifier, instances in specials.items():
        rule = registry.specials.get(identifier)
        if rule is None:
            errors.append(f"{context}: '{identifier}' is not a Special id")
            continue
        if slot not in rule.slots:
            slots = ", ".join(rule.slots)
            errors.append(
                f"{context}: '{identifier}' is not a {slot} Special;"
                f" it declares {slots}"
            )
            continue
        for instance in instances:
            errors += _check_instance(
                instance,
                rule=rule,
                where=f"{context}: '{identifier}'",
                registry=registry,
            )
    return errors


def _check_instance(
    instance: SpecialInstance,
    *,
    rule: r.SpecialRuleConfig,
    where: str,
    registry: Registry,
) -> list[str]:
    """Check one instance's args, once per set of values it supplies.

    A case-shaped instance supplies one set per case, each merged over the
    instance's own args, so a value constant across the cases is written once
    (ADR 0030). A broken case names its 1-based position, because the cases of
    one instance are otherwise indistinguishable in a message.
    """
    errors = _check_variant(instance.variant, rule=rule, where=where)
    if not instance.cases:
        return errors + _check_args_in_scope(
            instance.args, rule=rule, where=where, registry=registry
        )
    for number, case in enumerate(instance.cases, start=1):
        scoped = f"{where}, case {number}"
        errors += _check_variant(case.variant, rule=rule, where=scoped)
        errors += _check_args_in_scope(
            instance.args | case.args, rule=rule, where=scoped, registry=registry
        )
    return errors


def _check_variant(
    variant: str | None, *, rule: r.SpecialRuleConfig, where: str
) -> list[str]:
    """Check that a named variant is one the rule defines (ADR 0032).

    The pool is the rule's own, so the id is a lookup key like any other and a
    miss is a load failure rather than prose the reader silently loses.
    """
    if variant is None or variant in rule.variants:
        return []
    defined = ", ".join(sorted(rule.variants)) or "none"
    return [f"{where}: no variant '{variant}'; the rule defines {defined}"]


def _check_args_in_scope(
    args: dict[str, int | str],
    *,
    rule: r.SpecialRuleConfig,
    where: str,
    registry: Registry,
) -> list[str]:
    """Check one set of args against the variables the rule brings into scope."""
    variables, collisions = _variables(args, rule=rule, registry=registry)
    return [f"{where}: {problem}" for problem in collisions] + [
        f"{where}: {problem}"
        for problem in _check_args(args, variables, registry=registry)
    ]


def _variables(
    args: dict[str, int | str], *, rule: r.SpecialRuleConfig, registry: Registry
) -> tuple[dict[str, r.VariableConfig], list[str]]:
    """Collect the variables an instance's args are checked against.

    The union of the rule's own variables and those of every ref target it
    names — a ref's arguments travel with the ref, which is what collapses the
    hand-spelled "Good shot: +1 to hit" variants into one id. A target's ref
    may name a further target, so this walks until nothing new appears.
    """
    variables = dict(rule.variables)
    errors: list[str] = []
    pending = list(variables.items())
    while pending:
        name, variable = pending.pop()
        value = args.get(name)
        if not isinstance(variable, r.RefVariableConfig) or not isinstance(value, str):
            continue
        target = registry.record(value)
        if target is None:
            continue  # reported when the args themselves are checked
        for lent, lent_variable in target.variables.items():
            if lent in variables:
                errors.append(
                    f"variable '{lent}' of '{value}' collides with one already in"
                    " scope; rename one of the two"
                )
            else:
                variables[lent] = lent_variable
                pending.append((lent, lent_variable))
    return variables, errors


def _check_args(
    args: dict[str, int | str],
    variables: dict[str, r.VariableConfig],
    *,
    registry: Registry,
) -> list[str]:
    """Check the args are exactly the declared variables, each with a legal value."""
    known = ", ".join(sorted(variables)) or "none"
    errors = [
        f"missing argument '{name}'"
        for name in variables.keys() - args.keys()
        if not variables[name].optional
    ]
    errors += [
        f"unknown argument '{name}'; the rule takes {known}"
        for name in args.keys() - variables.keys()
    ]
    for name, variable in variables.items():
        if (value := args.get(name)) is None:
            continue
        problem = (
            _check_ref(value, variable, registry=registry)
            if isinstance(variable, r.RefVariableConfig)
            else _check_scalar(value, variable)
        )
        if problem is not None:
            errors.append(f"argument '{name}': {problem}")
    return errors


def _check_ref(
    value: int | str, variable: r.RefVariableConfig, *, registry: Registry
) -> str | None:
    """Check that a ref resolves, and that it lands in the permitted value set."""
    if not isinstance(value, str) or (match := _REF.match(value)) is None:
        return f"'{value}' is not a reference; write '<namespace>.<id>'"
    namespace, identifier = match.groups()
    if namespace not in variable.namespaces:
        permitted = ", ".join(variable.namespaces)
        return f"'{value}' points into '{namespace}'; permitted: {permitted}"
    if identifier not in registry.records.get(namespace, {}):
        return f"'{value}' resolves to no record"
    if variable.values is not None and value not in variable.values:
        return f"'{value}' not any of {variable.values}"
    return None


def _check_scalar(value: int | str, variable: r.ScalarVariableConfig) -> str | None:
    """Check a scalar arg against the type, bounds and value set it declares."""
    try:
        variable.validate_value(value)  # pyright: ignore[reportArgumentType]
    except ValueError as err:
        return str(err)
    return None
