r"""Scan LaTeX templates for their `\usepackage` / `\documentclass` names.

A *lint over authored data*, mirroring `spf.lint.collect`: the manifest and
the templates are both authored, so this checks one against the other rather
than exercising rendering itself.
"""

import re
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


def read_manifest(manifest_path: Path) -> set[str]:
    """Parse a requirements manifest: one package per line, `#` comments stripped."""
    names: set[str] = set()
    for line in manifest_path.read_text().splitlines():
        name = line.split("#", 1)[0].strip()
        if name:
            names.add(name)
    return names


def unlisted_packages(templates_dir: Path, manifest_path: Path) -> list[str]:
    """Return, sorted, every package a template uses but the manifest omits."""
    used = packages_in_templates(templates_dir)
    manifest = read_manifest(manifest_path)
    return sorted(used - manifest)
