# Rendering pipeline: resolved data → two template families → derivations

The `spf/render/` subsystem turns SteamPunkFantasy data into gameplay reference
**Renderings** (Order Cards, Army Reference, Race Overview, Rulebook) in four
Formats (markdown, html, latex, pdf). The decisions:

**Resolved data is the view-model.** Each Product is rendered from a
source-of-truth object passed straight into the templates — the resolved `Army`
for Order Cards and Army Reference, the `RaceConfig` for Race Overview, the
`rules/*.toml` configs for the Rulebook. The *same* data goes to every Format's
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
