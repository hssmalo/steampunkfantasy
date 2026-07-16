"""The shared rendering subsystem for SteamPunkFantasy.

Turns a resolved data object (the source) into a file in one of several Formats,
driven by data records rather than per-product or per-format code. The single
seam is `render`; `Format` and `Product` are the record types
product issues plug into.
"""

from spf.render.formats import Format
from spf.render.pipeline import render
from spf.render.products import Product

__all__ = ["Format", "Product", "render"]
