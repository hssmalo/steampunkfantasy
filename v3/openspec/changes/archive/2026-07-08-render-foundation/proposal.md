## Why

The four planned gameplay-reference Products (Order Card, Army Reference, Race
Overview, Rulebook) all need the same rendering machinery: turn a resolved data
object into a file in one of several Formats. v2 tangled data-prep and LaTeX
emission in one 38 KB, LaTeX-only module. Before any Product is built we need the
shared `spf/render/` foundation the four child issues plug into — the seam,
environments, derivations, config, and CLI scaffold. (GitHub #17, child of #16;
architecture settled in ADR 0005.)

## What Changes

- New package `spf/render/` (below the CLI, above `races.py`/`armies/`/`rules.py`)
  exposing one seam: `render(product, source, fmt, *, name, out=None) -> Path` — a
  generic pipeline driven by data records, not per-product/per-format code.
- **Format registry**: `Format(name, extension, family, post_step)`; register all
  four — `markdown`, `html` (markdown family + `md_to_html`), `latex`, `pdf`
  (latex family + `latex_to_pdf`).
- **Product registry**: the `Product` record type + registry mechanism only —
  **zero** concrete Products registered (each child issue adds its own).
- **Two Jinja2 environments**: Markdown (stock delimiters, `autoescape=False`) and
  LaTeX (`\VAR{}`/`\BLOCK{}`, `autoescape=False`, trim/lstrip blocks), built by an
  injectable factory.
- **Two derivations**: `md_to_html` (markdown-it-py → standalone HTML doc) and
  `latex_to_pdf` (compile twice in a temp dir, copy only the `.pdf`).
- **Template layout** `templates/<family>/<product>/main.<ext>.jinja`; legacy
  top-level `templates/*.tex` left untouched.
- **Config**: add `paths.output` (default `{project_path}/output`, gitignored) and
  a `[render.latex].engine` setting (default `pdflatex`).
- **CLI**: an empty `spf render` group + a reusable `--format`/`--out` parameter
  set; product subcommands land in the child issues.
- **Dependencies**: promote `jinja2` and `markdown-it-py` to direct deps.

## Non-goals

- Any actual Product template or its CLI subcommand (the four child issues).
- Terminal/Rich output (authoring/inspection, not a Rendering).
- `Race.resolve()` to inline full special text (Race Overview stays unresolved).
- Multi-Unit / multi-Army aggregation into one Rendering.
- Rich per-product HTML styling.

## Capabilities

### New Capabilities
- `render-foundation`: the shared rendering subsystem — the `render()` seam, the
  Format and Product record types and registries, the two Jinja environments, the
  two derivations (Markdown→HTML, LaTeX→PDF), output-path resolution and write
  behavior, config additions, and the `spf render` CLI scaffold.

### Modified Capabilities

None — no existing spec's requirements change.

## Impact

- **New code**: `src/spf/render/` (`pipeline`, `formats`, `products`,
  `environments`, `derivations`, `__init__`).
- **CLI**: `src/spf/frontends/cli/main.py` gains the `render` group; new
  `cli/render.py` for the `RenderOpts` parameter set.
- **Config**: `configs/spf.toml` + `src/spf/schemas/config.py` (`PathsConfig.output`,
  new `RenderConfig`/`LatexConfig`); `.gitignore` gains `output/`.
- **Dependencies**: `pyproject.toml` — `jinja2`, `markdown-it-py` become direct.
- **System prerequisite**: `pdflatex`/`xelatex` needed only for the `pdf` Format
  (tests `skipif`-gate on it).
- **Templates**: new `templates/markdown/` and `templates/latex/` subtrees; legacy
  `.tex` files untouched.
