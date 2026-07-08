"""The Image Asset kind: AI-generated race/unit art via Pollinations.

Registers the ``image`` :class:`~spf.assets.Kind`, laid out at
``<race>/images/<name>.png``, backed by :class:`PollinationsService`. The
service turns a composed prompt into ``count`` PNG blobs, deriving one sub-seed
per Candidate from the base ``seed`` so a batch is reproducible.

The provider is the free Pollinations image endpoint. An optional
``SPF_POLLINATIONS_API_KEY`` in the environment lifts anonymous rate limits;
absent, the anonymous path is attempted. Paid providers land in #35, a local
offline backend in #36.
"""

import os
import random
import urllib.parse
import urllib.request
from collections.abc import Sequence

from spf.assets.kinds import Kind, register_kind

_ENDPOINT = "https://gen.pollinations.ai/image"
_WIDTH = 1024
_HEIGHT = 1024
_MODEL = "zimage"
_SEED_BOUND = 2**31


def _build_url(prompt: str, seed: int) -> str:
    """Build the Pollinations image URL for ``prompt`` at ``seed``."""
    quoted = urllib.parse.quote(prompt, safe="")
    query = urllib.parse.urlencode(
        {"width": _WIDTH, "height": _HEIGHT, "seed": seed, "model": _MODEL}
    )
    return f"{_ENDPOINT}/{quoted}?{query}"


def _fetch(url: str) -> bytes:
    """Fetch the raw image bytes at ``url``, adding the API key when set."""
    key = os.environ.get("SPF_POLLINATIONS_API_KEY")
    if key:
        separator = "&" if "?" in url else "?"
        url = f"{url}{separator}key={urllib.parse.quote(key, safe='')}"
    with urllib.request.urlopen(url) as response:  # noqa: S310  https endpoint
        return response.read()


class PollinationsService:
    """A :class:`~spf.assets.Service` that renders images via Pollinations."""

    def generate(
        self, source: str, count: int, *, seed: int | None = None
    ) -> Sequence[bytes]:
        """Render ``count`` images for the ``source`` prompt, one per sub-seed."""
        rng = random.Random(seed)  # noqa: S311  image seeds, not cryptographic
        seeds = [rng.randrange(_SEED_BOUND) for _ in range(count)]
        return [_fetch(_build_url(source, s)) for s in seeds]


IMAGE = register_kind(
    Kind(
        name="image",
        service=PollinationsService(),
        subdir="images",
        extension="png",
    )
)
