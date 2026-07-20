"""Test-suite-wide setup.

Pytest imports this before any test module, and therefore before
`spf.console` constructs its Rich Consoles — which is what makes the
environment pinning below effective. A Console reads its colour and width
settings once, at construction, so none of this works as a fixture.
"""

import os

# Rich emits colour and bold when FORCE_COLOR is set, and those escapes land in
# `capsys` output — where a test asserting on layout sees `'\x1b[32m4.1'`
# instead of `'4.1'`. Some terminals, CI runners and agent harnesses set it.
# These tests assert on text, not styling, so the suite runs uncoloured.
for _var in ("FORCE_COLOR", "COLORTERM"):
    os.environ.pop(_var, None)
os.environ["TERM"] = "dumb"

# Rich otherwise takes its width from the invoking terminal, so anything that
# wraps — a Brief, a long error — depends on the size of the window the suite
# happens to be run from. Pin it, or `COLUMNS=60` fails three tests.
os.environ["COLUMNS"] = "100"
