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

# Rich otherwise takes its width from the invoking terminal, so where a message
# wraps depends on the window the suite happens to be run from. Pinning it makes
# a run reproducible — but it is deliberately *not* what makes these tests pass:
# they are green with this line deleted at every width from 40 to 250, because
# the ones that match on a message compare it `unwrapped`. Keep it that way. A
# test that only passes at 100 is a test that will fail on someone's laptop.
os.environ["COLUMNS"] = "100"


def unwrapped(text: str) -> str:
    """Collapse Rich's line breaks so a message can be matched as one string.

    Rich wraps console output to the terminal width, and the break can land
    inside the very phrase a test is looking for, splitting "does not support
    refinement" across two lines. Where the subject is *that the message
    reached the user*, rather than how it was laid out, assert against this
    instead of the raw capture.
    """
    return " ".join(text.split())
