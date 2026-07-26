# Rendering pipeline: resolved data → two template families → derivations

The `spf/render/` subsystem turns SteamPunkFantasy data into gameplay reference
**Renderings** (Order Cards, Army Reference, Race Overview, Rulebook) in four
Formats (markdown, html, latex, pdf). The decisions:

**Resolved data is the view-model.** Each Product is rendered from a
source-of-truth object passed straight into the templates — the resolved `Army`
for Order Cards and Army Reference, the `RaceConfig` for Race Overview, the
`rules/*.toml` configs for the Rulebook (**superseded for the Rulebook by
ADR 0018**: it is built from an authored index naming its sections, not from
the contents of `rules/`). The *same* data goes to every Format's
templates; templates stay dumb (read attributes, iterate) and carry no lookup or
computation logic.

**Two authored template families, HTML/PDF derived.** Only **Markdown** and
**LaTeX** templates are authored (Jinja2, per-family environments — stock
delimiters for Markdown, `\VAR{}`/`\BLOCK{}` for LaTeX to avoid brace clashes).
**HTML derives from the Markdown family** (Markdown → HTML), **PDF derives from
the LaTeX family** (pdflatex, compiled in a scratch dir so only the `.pdf`
survives). A Format is a small registered record (name, extension, template
family, optional post-step); adding a third Format is a drop-in against the same
resolved data.

**Why:** v2 tangled data-prep and LaTeX emission in one 38 KB module, LaTeX-only
and unextendable. Separating a resolved view-model from thin per-family templates
puts each formatting rule in exactly one place and makes a new Format additive.
We rejected a single-source/Pandoc approach (author Markdown, convert to LaTeX):
it fights hard on cards and tables, and the card layout genuinely differs from
the prose layout, so one source cannot serve both well.

## Consequences

- Terminal/Rich output stays **out** of this subsystem — it serves authoring and
  inspection, not gameplay reference, and is not a file Rendering.
- Race Overview passes an *unresolved* `RaceConfig`, so its specials are the
  short override strings, not full rule text. A future `Race.resolve()` is the
  seam to inline them; deferred.
- Multi-Unit and multi-Army aggregation into one Rendering is a future concern;
  the placeholder is concatenating PDFs at the end.
- The Markdown Jinja environment runs with `autoescape=False`, **not** HTML
  autoescape as one might assume. Markdown templates emit Markdown text, not
  HTML — Jinja HTML-escaping would corrupt the raw `.md` (a `&` becomes `&amp;`)
  and does nothing for Markdown-special characters anyway. HTML-escaping is
  deferred to the Markdown→HTML derivation, where `markdown-it-py` escapes text
  correctly. (Source data is designer-authored TOML, so injection risk is low
  regardless.)

## Addendum: `md_to_latex` is not the rejected Pandoc approach

The Rulebook (ADR 0018) introduced `spf.render.md_latex.md_to_latex`, a
Markdown-to-LaTeX converter. Read against the rejection above — "we rejected a
single-source/Pandoc approach (author Markdown, convert to LaTeX)" — that looks
like a reversal. It is not, and the line between them is worth drawing
explicitly.

What was rejected was authoring **templates** in one family and deriving the
other. That still holds: every template is authored per family, Markdown and
LaTeX, and the card layout still differs from the prose layout because it
genuinely should.

The converter serves Markdown that arrives **inside the data**: the free-text
Rulebook Sections, and the prose fields inside the rules TOML. That content has
no per-family authored form and never will — a designer writes one paragraph of
rules text, not a Markdown one and a LaTeX one. Something has to give it a
LaTeX form, and doing it in a filter puts that rule in exactly one place, which
is the same principle the rest of this ADR rests on.

So: **templates are authored per family; Markdown embedded in data is
converted.** The converter's reach is deliberately small — no tables, no
images, no link targets, and raw LaTeX in a Markdown source is escaped rather
than passed through. If it ever grows to where a Markdown source can express a
whole authored layout, that is the boundary being crossed, and this decision
should be revisited rather than stretched.
