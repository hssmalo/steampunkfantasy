"""The Product registry.

A :class:`Product` is a kind of Rendering (Order Card, Army Reference, ...). Its
``name`` locates templates as ``<family>/<name>/main.<ext>.jinja`` and names the
output subdirectory. A Product is *not* bound to a single family — the
``(product, family)`` pair locates a template, so the same Product can reach both
HTML (via the markdown family) and PDF (via the latex family).

This foundation ships the record type and the registry mechanism only. **Zero**
concrete Products are registered here; each product issue registers its own.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class Product:
    """A registered kind of Rendering."""

    name: str


PRODUCTS: dict[str, Product] = {}


def register_product(product: Product) -> Product:
    """Register a Product under its name and return it."""
    PRODUCTS[product.name] = product
    return product


def get_product(name: str) -> Product:
    """Look up a registered Product by name."""
    try:
        return PRODUCTS[name]
    except KeyError:
        known = ", ".join(PRODUCTS) or "(none registered)"
        msg = f"Unknown product {name!r}; known products: {known}"
        raise ValueError(msg) from None
