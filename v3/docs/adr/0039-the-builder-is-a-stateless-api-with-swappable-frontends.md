# The builder is a stateless API with swappable frontends

The Army builder is a pure function over an Army: `apply(army, action)` returns a
**Builder State** — the resolved Army, its Cost totals and Points, the remaining
room under the chosen Game Format's Budget, and every move available from here,
each annotated with what it costs, whether it fits the Budget, what Default
Equipment it would discard, and what the Model's stats become. There is no
session, no server-held Army, no builder state that outlives a call.

Frontends hold the Army, render a Builder State, and send actions. They add no
rules of their own. A Textual TUI and a Lustre single-page app are both written
against this one contract, and a third could replace either without `spf`
noticing.

## Why the builder holds no state

The hosted builder has nowhere to keep it. A free static host serves files and
never runs code, so on the public site the rules run inside the visitor's
browser under Pyodide — the same `spf` wheel, compiled to WebAssembly. Locally
the rules run in an ordinary CPython process the browser talks to over HTTP.

A stateless function is the only shape both of those can serve without
divergence: the local frontend calls it over the network, the hosted one calls
it in-process, and neither the UI nor the rules change between them. A
server-held session would have made the hosted build a second implementation,
and a second implementation of the rules is the one thing this design exists to
prevent.

It also costs nothing to adopt. `ArmyList` is already immutable and already
answers `available_models`, `available_equipment` and `army_violations`; the
builder API is an envelope around what the engine does anyway. Undo is a stack of
Armies.

## Why the Budget is an affordance, never a violation

A **Budget** is four independent caps — so much `mp`, `cp`, `xp` and `ip` — named
by a **Game Format**. It is a target a player builds toward, not a rule an Army
obeys. Validity stays exactly what ADR 0036 made it: referential legality
against the catalogue, with no budget or points check anywhere near the loader.

The reason is historical Armies. Costs evolve as the game is balanced, so an
Army that spent its 96/96/96/96 honestly in 2025 can exceed today's Budget
without having changed a line. If the Budget were a validity rule, rebalancing a
Unit would retroactively invalidate armies that were legally built — and
`armies/` is a record of what was fielded, not a set of claims about what is
currently buildable.

So the Builder State reports affordability per move and remaining room per
dimension, and `army_violations` keeps quiet about all of it. **Refusing an
unaffordable purchase is a frontend policy**, applied when adding and never when
loading: an over-Budget Army opens in the builder intact, shows red gauges, and
can be edited down. Removing a Unit from it may make that Unit unaddable again.
That asymmetry is intended — the historical Army stays what it was, and building
forward from it means building within today's Budget.

Consequently no Army records the Budget it was built against. A Game Format is a
configured preset chosen at build time, and the Army stays a statement of what
the force is rather than of what it was measured against.

## Consequences

- The pydantic floor is capped by what Pyodide ships, because `pydantic-core` is
  Rust and cannot be installed from PyPI into WebAssembly. Nothing in `spf` uses
  pydantic beyond `BaseModel`, `ConfigDict`, `Field`, `BeforeValidator`,
  `StringConstraints`, `model_validator` and `ValidationError`, all of which
  predate 2.1 — so the floor drops to accommodate the browser and a future
  dependency wanting a newer pydantic reopens this decision.
- Art reaches the builder as URLs into the published site, never as bytes in the
  payload and never from `raw.githubusercontent.com`, which is not a CDN. The
  TUI ignores those fields; that a frontend may ignore part of the state is
  normal, and the state is specified for the richest frontend rather than the
  plainest.
- Armies the builder saves are ordinary Army JSON in whatever location the
  player names. Adding one to `armies/` is a separate, deliberate act, so a
  half-finished Army can never reach the Site Index.
- Every builder rule is tested through `apply` alone. The frontends are thin
  enough that their tests prove only that they render the state they were given
  and send the action they claim.
