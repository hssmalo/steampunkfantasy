# Merged orders on the resolved model; card shaping in the render layer

The Order Card Product (issue #18) is the first consumer of two things that were
modelled but never used: equipment `orders_gained`, and any presentation of a
Unit's orders. Two decisions settle how orders reach a card.

**A Unit's orders are merged on the resolved model.** `Unit.orders()` returns a
single `OrdersConfig` that unions the Unit's base `orders` with the
`orders_gained` of every effective equipment across its Models. The merge is
per-order-type (`fire`/`movement`) and per-Speed: for each Speed appearing in the
base **or** any equipment, the base rows come first, then each equipment's gained
rows for that Speed, dropping exact-duplicate rows. A Speed the base Unit lacks
(e.g. `crawl` from Hide) appears; extra options (an SMG's `Fire`) append under
their Speed. This lives on the model — beside `Unit.cost()` and `Model.assault()`
— because it is intrinsic to the resolved force and other Products (Army
Reference) will want the same merged view. It needs no `race_config`: each Model
already embeds its effective equipment.

**Card shaping lives in the render layer, not the model.** Turning merged orders
into cards is a *presentation* transposition — one card per (Unit, order-type,
option-index), rows being that option across all Speeds; identical Units collapse
to one card set. That logic is card-specific and belongs to the Product, so it
lives in `spf/render/cards.py` as a view-model builder (`build_deck(army) ->
OrderCardDeck`). The deck is what is passed to `render()` as its `source`, keeping
templates dumb per ADR 0005. The same deck carries both shapes the two families
need: a flat per-Unit orders view for the Markdown table, and the transposed card
list for the LaTeX 9-per-page grid.

**Why:** We rejected having `orders_gained` *replace* base orders per Speed (it
loses base options the Unit still has) and rejected showing base and gained in
separate blocks (busier, harder to use at the table). Append-union keeps every
committable order in one place. We rejected computing card structure on the core
`Army` model: it would push print-layout concerns (option-index transposition,
dedup, 9-per-page framing) into the domain model, which should not know how a
card looks.

## Consequences

- Data authors can rely on `orders_gained` being **additive** — a new row or a
  new Speed, never an override. Changing this later would silently alter every
  card, so it is recorded here.
- `Unit.orders()` is a stable seam other Products can reuse; the card view-model
  is not — it is private to the Order Card Product.
- The Markdown and LaTeX families diverge (flat table vs. option-cards) exactly
  as ADR 0005 anticipated; they consume different attributes of the same deck.
- Shaken orders (`ShakenConfig`) are **not** part of `Unit.orders()`; they are a
  separate fixed order and are rendered only as a trailing `shaken` row in the
  Markdown tables, with no LaTeX card.
