## Context

SteamPunkFantasy needs to turn resolved data into gameplay-reference Renderings
(Order Card, Army Reference, Race Overview, Rulebook) in four Formats (markdown,
html, latex, pdf). v2 tangled data-prep and LaTeX emission in one 38 KB,
LaTeX-only module. The architecture is settled in ADR 0005: resolved data is the
view-model, two authored template families (Markdown, LaTeX), HTML derived from
Markdown and PDF from LaTeX, a `Format` as a registered record. This change is the
**foundation only** — no Product templates. It sits below the CLI and above the
data layer (`races.py`/`armies/`/`rules.py`). Vocabulary lives in `CONTEXT.md`;
sources of truth are the resolved `Army` (`spf.armies.army.Army`, frozen
dataclass), the unresolved `RaceConfig`, and the `rules/*.toml` configs.

## Goals / Non-Goals

**Goals:**
- One generic `render()` seam the four product issues build against, with products
  contributing templates only (no Python).
- Data-driven registries (Formats, Products) so a new Format or Product is
  additive.
- Two Jinja environments and two derivations, each formatting rule in exactly one
  place.
- Config, CLI scaffold, and a test strategy that proves the pipeline without any
  Product.

**Non-Goals:**
- Product templates and their CLI subcommands (the four child issues).
- Terminal/Rich output, `Race.resolve()`, multi-Unit/Army aggregation, rich
  per-product HTML styling.

## Decisions

**Generic pipeline over registries, not per-product renderers.**
`render(product, source, fmt, *, name, out=None)` looks up the family environment
(`ENVIRONMENTS[fmt.family]`), loads `<product>/main.<ext>.jinja`, renders the whole
source object into a dumb template, applies `fmt.post_step` if present, and writes
the file. *Alternative rejected:* a `Renderer` subclass per product — it invites
lookup/computation logic back into the renderer, the exact v2 tangle. Registries
are plain module-level dicts populated at import; no entry-point/plugin machinery
for a single-codebase set of four.

**Foundation registers 4 Formats, 0 Products.** Formats are complete and
family-generic, and `--format`'s choices derive from the Format registry. Products
are half-defined without templates, so each child issue owns its `Product(...)`
record end-to-end; foundation ships only the type + registry mechanism, and tests
use a throwaway test-only Product. *Alternative rejected:* pre-registering the four
Product records now — leaves half-defined products in the foundation.

**Product is not bound to a family; missing combos fail lazily.** Order Card needs
both Markdown and LaTeX templates (to reach html and pdf), so the `(product,
family)` pair locates templates. We do not pre-validate the matrix; Jinja's
`TemplateNotFound` surfaces only for the combination actually requested.

**Markdown environment `autoescape=False`** — a deliberate deviation from the
issue's "autoescape for HTML". Markdown templates emit Markdown, not HTML; Jinja
HTML-escaping would corrupt the raw `.md` (`&`→`&amp;`) and does nothing for
Markdown-special chars. HTML-escaping is deferred to `markdown-it-py` at
derivation time. Source data is designer-authored TOML, so injection risk is low.
Recorded in ADR 0005.

**LaTeX environment** uses `\VAR{}`/`\BLOCK{}` delimiters to avoid brace clashes
with LaTeX's own `{}`, plus `trim_blocks`/`lstrip_blocks` for clean output.

**`md_to_html` uses `markdown-it-py`** (already transitive via `rich`; promoted to
direct) with table support, wrapping the fragment in a minimal standalone HTML5
document so the `.html` is double-clickable. *Alternative rejected:*
`python-markdown` — a new dependency for no gain.

**`latex_to_pdf` compiles in a temp dir, twice, `nonstopmode -halt-on-error`,**
copying only the `.pdf` out. Twice is the standard "just works" default (stable
page numbers/refs) and cheap for tiny docs. The engine is
`config.render.latex.engine` (default `pdflatex`), so switching to xelatex/lualatex
later — same flags — is one config line. Missing binary and non-zero exit raise
clear, diagnosable errors (the latter includes the engine log tail).

**Config**: `paths.output` (honoring the issue's `config.paths.output` wording) and
a nested `[render.latex].engine` so `[render.markdown]`/`[render.pdf]` can join
later; `output/` gitignored.

**CLI**: an empty `spf render` group wired like `army`/`race`/`rules`, plus a
reusable `RenderOpts(--format/--out)` parameter set the product subcommands will
accept. No dummy command — the pipeline is proven by tests.

**Injectable roots as the test seam.** `make_environments(templates_root)` and
`render(..., output_root=...)` default to `config.paths.*` but accept overrides, so
tests point at fixture templates and a tmp output dir. Fan-out (Order Card is
per-Unit) lives in product subcommands; `render` renders one source to one file and
takes `name` explicitly rather than sniffing `.nick`/race-name off the source.

## Risks / Trade-offs

- **PDF tests need a LaTeX install** → `@pytest.mark.skipif(shutil.which(engine))`
  so CI without LaTeX passes; env/text-format paths stay fully covered.
- **Foundation ships nothing a user can run end-to-end** (empty CLI group until the
  first product) → acceptable for a foundation; the seam is verified by an
  end-to-end `render()` test over a fixture template.
- **`jinja2`/`markdown-it-py` currently only transitive** (via `streamlit`/`rich`)
  → promote to direct deps so we don't rely on that staying true.
- **Two-pass pdflatex doubles compile time** → negligible for these tiny reference
  docs; buys robustness against stale page numbers.
- **Legacy `templates/*.tex` left in place** → invisible to the new family-rooted
  loaders; product issues cannibalize them to bootstrap, avoiding churn now.
