"""Apply the name rules to the rule registries under `rules/`.

The registries *are* the vocabulary (ADR 0024): every record has a key that
Race data writes and a display name the reader sees, so they earn the same
key-name discipline Races already get. A soft gate on top of a hard one — a
registry that fails schema validation never reaches here, because loading it
is what raises (ADR 0016).
"""

from dataclasses import dataclass

from spf.lint import names, prose
from spf.registry import Registry
from spf.schemas.config import LintConfig


@dataclass(frozen=True)
class RegistryFinding:
    """One rule violation, located precisely enough to go and fix it."""

    file: str
    namespace: str
    key: str
    rule: str
    message: str


def lint_registry(registry: Registry, conventions: LintConfig) -> list[RegistryFinding]:
    """Return every finding across every namespace the registry declares.

    The namespace, not the file, is the unit of the walk: two namespaces may
    share a file, and it is the namespace a reader has in hand when reading a
    ref. The file comes along only so the finding names something to open.
    """
    return [
        RegistryFinding(
            file=registry.namespaces[namespace].file,
            namespace=namespace,
            key=key,
            rule=rule,
            message=message,
        )
        for namespace, records in registry.records.items()
        for key, record in records.items()
        for rule, message in names.check_name(key, record.name, conventions)
    ] + lint_registry_prose(registry)


def lint_registry_prose(registry: Registry) -> list[RegistryFinding]:
    """Apply the prose rules to every sentence field a record declares.

    A record's `effect` is the rule as the player reads it -- the most-read
    prose in the corpus -- so it is held to what the Race data is held to.
    """
    return [
        RegistryFinding(
            file=registry.namespaces[namespace].file,
            namespace=namespace,
            key=f"{key}.{location}" if location else key,
            rule=rule,
            message=message,
        )
        for namespace, records in registry.records.items()
        for key, record in records.items()
        for location, value in prose.walk_prose(record.model_dump())
        for rule, message in prose.check_prose(value)
    ]
