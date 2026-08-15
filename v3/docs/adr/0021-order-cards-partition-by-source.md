# Order Cards are transposed per Order Source, not per Unit

An Order Card back names the Equipment that granted its orders (issue #78), so
that a player can pull one Equipment's cards out of a deck and field the Unit
without it. That is impossible under ADR 0007's card shaping: it transposes the
*merged* orders by option index, and because Speeds have different base row
counts, one index is a base row at one Speed and an Equipment's gained row at
another. Darkelf Infantry with Hide produces two such mixed cards — cards that
name Hide but carry base `slow` orders, and so cannot be removed.

**Decision: the option-index transposition is applied once per Order Source
rather than once per Unit.** An Order Source is the base Unit or one
order-modifying Equipment. Base rows transpose among base rows only — so the
base Card Set of any Unit is exactly what ADR 0007 already produced for a Unit
with no order-modifying Equipment — and each Equipment transposes its own gained
rows into its own Card Set, naming itself on the back.

ADR 0007's transposition *rule* is unchanged, and its merged-orders decision
still stands: `Unit.orders()` remains the merged view the Markdown family and
future Products consume. It is now the fold of a new `Unit.orders_by_source()`,
which is the single merge algorithm both views are derived from. Only ADR 0007's
"one card per (Unit, order-type, option-index)" shaping is superseded.

**Why this is sound:** ADR 0007 already records that `orders_gained` is strictly
additive — "a new row or a new Speed, never an override". Additive means the
sources are independent, so a deck is the *sum* of its source Card Sets and a
loadout is the base set plus one set per Equipment carried. If additivity is ever
revisited, this design goes with it.

## The sharing invariant

A Card Set is shared between Units only when **every card in it applies to every
Unit sharing it.** Four identical un-nicked Ork Infantry still collapse to one
set (ADR 0007, ADR 0019) because every card applies to all four. Two Darkelf
Infantry differing only by Hide do not, and never did — their merged rows differ,
so `build_deck`'s collapse key already separates them. That key is unchanged by
this ADR.

This means the two Units' base cards are textually identical and printed twice.
That is intended: interchangeable cards are exactly what lets a player deal two
complete decks and hold no rule in their head during play. Deduplicating them
would make building the second deck physically impossible.

## Consequences

- A gained row identical to a base row is still dropped, so an Equipment whose
  gained rows are entirely redundant contributes **no cards at all** and appears
  nowhere in the deck. This is correct — the base cards already carry those
  orders — but it hides a data defect, so a linter rule is tracked separately
  (issue #96).
- Default (free) and upgrade Equipment are treated identically. ADR-0020 makes a
  default's orders conditional too — any upgrade discards all defaults — so "play
  without it" is a real operation for both.
- Two Equipment on one Unit get one Card Set each, never a combined set. No
  committed army does this today; it is defined so the deck stays decomposable
  when one does.
- Two Equipment sharing a display name (darkelf `hide` and `hide_free`) are one
  Order Source, unioning their rows. Taking the first would silently drop rows if
  the two keys ever diverge.
- Card Sets are not deduplicated against each other across sources: two Equipment
  granting the same row each keep their copy, since either may be absent from a
  loadout. The *merged* view still drops the duplicate, so `Unit.orders()` is
  unaffected.
- Only the LaTeX family changes. The Markdown card family renders flat per-Unit
  tables from `Unit.orders()` and has no card back; its output is byte-identical.
