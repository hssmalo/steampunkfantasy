# Renderings reference committed Assets by absolute path

ADR 0006 settled that generated Assets are committed under `assets/` and
curated by hand. The Army Reference is the first Rendering to *use* them, which
forces a question the generation side never had to answer: what does the
rendered document say where the art goes?

## An absolute path into the committed store

**Decision: the view-model carries an absolute `Path` to the committed Asset,
and both template families emit it verbatim.** Nothing is copied, nothing is
inlined, nothing is generated at render time.

An absolute path is the one form that works unchanged in both families. LaTeX
compiles in a temporary directory (`latex_to_pdf`), but `\includegraphics`
resolves against the filesystem rather than the compiler's CWD, so no
`\graphicspath` and no staging is needed. HTML opened from disk resolves
`src="/home/…/art.png"` as `file:///home/…/art.png`.

Rejected:

- **A path relative to `output/`.** It breaks under LaTeX's temporary
  directory, and it is not even knowable when the template runs: the output
  directory is decided by `render()` afterwards, and `--out` can override it.
- **Copying the art into `output/`.** It breaks the render seam's "one
  template, one file out" invariant and duplicates committed bytes on every
  render.
- **Data-URI embedding.** A committed image is ~2.5 MB; inlining the
  eleven a mid-sized army needs yields a ~37 MB HTML file. It would also change
  `md_to_html`, a derivation shared by every Product, to serve one Product.

## Missing art is silence, not a placeholder

**Decision: the field is `Path | None`, and a `None` emits nothing at all.**

Coverage is sparse and uneven — most races have no race-level image and no race
has art for every unit — so missing art is the common case, not the exception.
A placeholder box would therefore dominate the document. Reporting what is
missing is already the Survey's job (ADR 0011), and a rendered army list is the
wrong place to duplicate it.

## The lookup is injected, not reached for

**Decision: `build_reference` takes an `image_for: ImageLookup` keyword,
defaulting to `committed_image`.** `spf.assets.asset_for` is the single public
lookup behind it, shared with the Survey.

Injection is what makes the view-model testable without a filesystem, and it is
also how `--no-images` is implemented: the flag passes `no_image`, a lookup that
finds nothing, so the templates need no opt-out conditional of their own.

## Consequences

- **The intermediate `.md` and `.tex` are not portable off this machine.** They
  name paths inside this checkout. That is acceptable: `output/` is gitignored
  throwaway, and the two artifacts anyone actually shares — the PDF, and HTML
  opened locally — embed or resolve the art fine.
- **PDFs are heavy.** LaTeX embeds each PNG at full resolution regardless of the
  displayed width, so a twelve-Unit army lands in the tens of megabytes.
  Fixing that means render-time downscaling plus a cache, which is a larger
  change than this one and is deliberately deferred.
- **Layout is the template family's business.** The view-model carries a path
  and nothing about size or placement, so Markdown's lead image and LaTeX's
  side-by-side minipages can differ without the two negotiating.
- `--no-images` lives on the shared `RenderOpts` but currently affects
  `army-rules` only; it starts working for `cards` when that Product embeds
  Assets.
