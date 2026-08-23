r"""Scan LaTeX templates for their `\usepackage` / `\documentclass` names.

A *lint over authored data*, mirroring `spf.lint.collect`: the manifest and
the templates are both authored, so this checks one against the other rather
than exercising rendering itself.
"""

import re
import tomllib
from pathlib import Path

_PACKAGE_LINE = re.compile(r"\\(?:usepackage|documentclass)(?:\[[^\]]*\])?\{([^}]*)\}")

# The base LaTeX class, not a manifest dependency.
_IGNORED = {"article"}


def packages_in_text(text: str) -> set[str]:
    r"""Return every package `text`'s `\usepackage`/`\documentclass` lines name.

    A comma-separated `\usepackage{a,b}` list yields both names. Commented-out
    lines (starting with `%`) are skipped.
    """
    names: set[str] = set()
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("%"):
            continue
        match = _PACKAGE_LINE.search(stripped)
        if match is None:
            continue
        names.update(name.strip() for name in match.group(1).split(","))
    return names - _IGNORED


def packages_in_templates(templates_dir: Path) -> set[str]:
    """Union of `packages_in_text` over every `*.tex.jinja` file under a dir."""
    names: set[str] = set()
    for path in templates_dir.rglob("*.tex.jinja"):
        names.update(packages_in_text(path.read_text()))
    return names


def _packages(manifest_path: Path) -> list[dict[str, str]]:
    """Parse a `requirements.toml` manifest's `[[package]]` tables."""
    data = tomllib.loads(manifest_path.read_text())
    return data.get("package", [])


def read_manifest(manifest_path: Path) -> set[str]:
    r"""Return every LaTeX package name the manifest declares.

    A `[[package]]` entry with no `name` — a transitive TL dependency no
    `\usepackage` line names directly — contributes nothing here.
    """
    return {pkg["name"] for pkg in _packages(manifest_path) if "name" in pkg}


def tlmgr_packages(manifest_path: Path) -> list[str]:
    """Return, sorted and deduplicated, the TeX Live packages tlmgr installs.

    A LaTeX package name doesn't always match its TL package: an entry's
    `tlmgr` key overrides it when they differ, defaulting to `name`. Every
    entry has one or the other — `read_manifest` and `_packages` are the
    only callers that ever see a name-less, `tlmgr`-only entry.
    """
    names = {
        pkg["tlmgr"] if "tlmgr" in pkg else pkg["name"]
        for pkg in _packages(manifest_path)
    }
    return sorted(names)


def unlisted_packages(templates_dir: Path, manifest_path: Path) -> list[str]:
    """Return, sorted, every package a template uses but the manifest omits."""
    used = packages_in_templates(templates_dir)
    manifest = read_manifest(manifest_path)
    return sorted(used - manifest)
