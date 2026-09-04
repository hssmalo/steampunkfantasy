"""The order-cell rules, as pure predicates over strings.

An order cell is one box on an Order Card -- `F`, `(L/R)`, `F+(Deploy)`,
`Fire(res)` -- and the corpus holds thousands of them drawn from a vocabulary
of about thirty orders. They are the most-printed strings in the game and the
ones the spell checker cannot read: `typos` skips any token containing a `+`,
so a Dwarf card printed `F+Depoloy` for years while `typos.toml` already
carried that very misspelling as a word to correct.

The vocabulary is authored in `[lint]` config rather than read from
`rules/orders.toml`: that file is still being drafted, and a linter that
depended on it would be holding a draft to a schema.
"""

import re
from collections.abc import Collection, Iterator, Mapping

ORDER_SLOTS = frozenset({"orders", "orders_gained", "movement_order"})
"""Where a Unit, a Model or a piece of Equipment writes its order cells."""

EMPTY_CELLS = frozenset({"", "-"})
"""A box left blank, and a box holding the do-nothing order."""

COMBINER = "+"
"""What joins two orders carried out in one step. A comma is not it."""

_ATOM = re.compile(
    r"^(?P<name>[^(\[]*?)(?P<gap>\s*)"
    r"(?:\((?P<paren>[^)]*)\)|\[(?P<square>[^\]]*)\])?$"
)
_ARGUMENT_SEPARATOR = re.compile(r",(?! )|(?<= ) +")
_INTERNAL_SPACES = re.compile(r"\S  +\S")


def check_cell(cell: str, vocabulary: Collection[str]) -> Iterator[tuple[str, str]]:
    """Yield `(rule, message)` for every order rule `cell` breaks."""
    if cell != cell.strip() or _INTERNAL_SPACES.search(cell) or " + " in cell:
        yield "order-whitespace", f"cell {cell!r} is padded"
        return
    if cell in EMPTY_CELLS:
        return
    if "," in _outside_arguments(cell):
        yield "order-separator", f"cell {cell!r} joins orders with ',' not '+'"
        return
    for atom in cell.split(COMBINER):
        yield from _check_atom(atom, cell, vocabulary)


def _check_atom(
    atom: str, cell: str, vocabulary: Collection[str]
) -> Iterator[tuple[str, str]]:
    """Check one order of a cell: its name, its spacing, its arguments."""
    inner = atom[1:-1] if _is_optional(atom) else atom
    match = _ATOM.match(inner)
    if match is None:
        yield "order-name", f"cell {cell!r} holds unreadable order {atom!r}"
        return
    if match["gap"]:
        yield "order-spacing", f"cell {cell!r} spaces {inner!r} off its arguments"
    if match["name"] not in vocabulary:
        yield "order-name", f"cell {cell!r} holds unknown order {match['name']!r}"
    argument = match["paren"] if match["paren"] is not None else match["square"]
    if argument is not None:
        yield from _check_argument(argument, cell)


def _check_argument(argument: str, cell: str) -> Iterator[tuple[str, str]]:
    """Check one argument list: lowercase throughout, `, ` between entries."""
    if argument != argument.lower():
        yield "order-argument", f"cell {cell!r} has uppercase argument {argument!r}"
    if _ARGUMENT_SEPARATOR.search(argument):
        yield "order-argument", f"cell {cell!r} does not write {argument!r} as ', '"


def _is_optional(atom: str) -> bool:
    """Whether `atom` is an order in parentheses: `(L/R)`, not `Fire(res)`."""
    return atom.startswith("(") and atom.endswith(")") and "(" not in atom[1:-1]


def _outside_arguments(cell: str) -> str:
    """Drop every bracketed group, leaving what joins the orders together.

    A comma inside `A[fast, fly]` separates arguments; a comma outside one is
    a cell written `360°,F` where the cards say `360°+F`.
    """
    return re.sub(r"\([^)]*\)|\[[^\]]*\]", "", cell)


def walk_cells(
    data: object, path: str = "", *, inside: bool = False
) -> Iterator[tuple[str, str]]:
    """Yield `(location, cell)` for every order cell under `data`.

    `inside` says the walk has entered an order slot, so the strings below it
    are cells however deeply the speed tables nest them.
    """
    if isinstance(data, Mapping):
        for key, value in data.items():
            child = f"{path}.{key}" if path else str(key)
            inside_slot = inside or key in ORDER_SLOTS
            yield from walk_cells(value, child, inside=inside_slot)
    elif isinstance(data, list):
        for index, value in enumerate(data):
            yield from walk_cells(value, f"{path}.{index}", inside=inside)
    elif isinstance(data, str) and inside:
        yield path, data
