"""Every rendered document carries the version of `spf` that produced it.

Driven through a CLI render command, so this exercises the wiring that hands
the version to the templates. Where each template puts the stamp is a layout
decision and is not asserted here; the version stamp is shared infrastructure,
so one document per Format covers the wiring.
"""

from pathlib import Path

import pytest

from spf.frontends.cli.render import RenderOpts, render_army_rules

DEMO_ARMY = "demo"


@pytest.mark.parametrize(("fmt", "suffix"), [("latex", "tex"), ("markdown", "md")])
def test_rendered_document_stamps_the_version(
    tmp_path: Path, pinned_version: str, fmt: str, suffix: str
) -> None:
    out = tmp_path / f"out.{suffix}"
    render_army_rules(DEMO_ARMY, opts=RenderOpts(format=fmt, out=out, no_images=True))

    assert f"v{pinned_version}" in out.read_text(encoding="utf-8")
