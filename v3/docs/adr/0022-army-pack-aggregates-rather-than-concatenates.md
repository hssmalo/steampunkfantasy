# The Army Pack aggregates Army References, rather than concatenating PDFs

ADR 0005 closed with a placeholder: "Multi-Unit and multi-Army aggregation
into one Rendering is a future concern; the placeholder is concatenating PDFs
at the end." Issue #100 is that future concern arriving, and the placeholder
does not survive it.

## Decision

**The Army Pack is a Product whose view-model holds many `ArmyReference`s and
renders through one template to one file. ADR 0005's PDF-concatenation
placeholder is overturned.**

Concatenation fails on four counts, three of them fatal:

- **No global contents list or pagination.** A pack exists so a player can
  find a competitor quickly; stapled PDFs cannot carry page numbers that mean
  anything across the seam.
- **PDF-only.** Concatenation is a PDF operation, so `markdown` and `html`
  would have no Army Pack at all — stranding the hyperlink half of #73.
- **A new dependency** for PDF manipulation, where aggregation needs none.
- Only the fourth count favors it: concatenation would need no template
  change. That is the cost we accept, and it buys something else (below).

Aggregation requires splitting the `army-rules` templates into a thin document
wrapper and a `reference-body` partial included by both Products. This is not
incidental cost — **it is the point**. Issue #73 will add an `--extended`
option inlining the Special, Token, and Hex rules an Army actually uses (a
name and semantic already authored into `rules/rulebook.toml`'s comments).
With one authored body per family, #73 is a change in one place that both
Products inherit. Under concatenation the two Products would have shared
nothing but a PDF stapler, and the pack's layout would drift from the
reference's on the first divergent edit.

The pattern is not new: the Rulebook (ADR 0018) already renders as a thin
`main` wrapping `rules-body` partials. ADR 0005 was written before that
existed, which is why its placeholder reached for the stapler.

## Alternatives rejected

**Widen the `render()` seam to accept many sources.** This changes the
pipeline for Order Cards and the Rulebook, which do not want it, to serve one
Product that can express itself as a registered Product instead.

**Pool the extended rules once per pack** rather than repeating them per Army.
It removes real repetition — "Terror" printed a dozen times in a twelve-army
pack — but it makes each Army's pages incomplete on their own, and handing one
player their pages is the pack's reason to exist. Revisit with evidence, as an
explicit `--pool-rules` option, if the repetition proves worse than the
incompleteness.

**Scan the armies directory instead of authoring an index.** Rejected for the
reasons ADR 0018 already gives: no order, no editorial intent, and a
half-finished army file silently published as a competitor's roster.

## Consequences

- `templates/*/army-rules/main.*` is now a wrapper only. The unit/model
  markup lives in `reference-body.*` and has exactly one copy per family. A
  change to how an Army's rules look is made there, once.
- The Army Pack reaches all four Formats for free, through the existing Format
  registry.
- A pack fails to build if any Army in its Index fails to load or validate,
  naming the Army and its position. A silently missing competitor is worse
  than a build that refuses.
- The remaining half of ADR 0005's placeholder — multi-*Unit* aggregation — is
  untouched and still open.
