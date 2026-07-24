# Renderings reference committed Assets in place, never copying them

ADR 0006 settled that generated Assets are committed under `assets/` and
curated by hand. The Army Reference is the first Rendering to *use* them, which
forces a question the generation side never had to answer: what does the
rendered document say where the art goes?

## A path into the committed store, whose form is the family's business

**Decision: the view-model carries an absolute `Path` to the committed Asset;
each template family emits it in whatever form resolves for its own output.**
Nothing is copied, nothing is inlined, nothing is generated at render time.

LaTeX emits the absolute path. It compiles in a temporary directory
(`latex_to_pdf`), so a document-relative path would not resolve, but
`\includegraphics` resolves against the filesystem rather than the compiler's
CWD — no `\graphicspath` and no staging needed.

Markdown emits the path **relative to the written document**, via the
`relative_to` filter and the output directory that `render()` binds alongside
the source. An absolute path was tried first and is wrong for HTML: a
root-absolute `src` resolves against the *authority* of a `file://` URL, so a
document opened across a UNC boundary — `file://wsl.localhost/<distro>/…`, the
normal way to read WSL output from Windows — silently drops the share name and
every image 404s. A relative `src` sidesteps the question by never naming a
root.

That the two families disagree is the point: the view-model says *which* Asset,
and each family decides how to spell it.

Rejected:

- **Copying the art into `output/`.** It breaks the render seam's "one
  template, one file out" invariant and duplicates committed bytes on every
  render.
- **Data-URI embedding.** A committed image is ~2.5 MB; inlining the
  eleven a mid-sized army needs yields a ~37 MB HTML file. It would also change
  `md_to_html`, a derivation shared by every Product, to serve one Product. It
  remains the option to reach for if genuinely portable HTML is ever wanted —
  it is the only form that survives being emailed.

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

- **Neither the `.md`/`.html` nor the `.tex` is portable off this machine.**
  The LaTeX names paths inside this checkout; the Markdown and HTML resolve
  only from where they were written, so moving the `.html` elsewhere breaks its
  images. That is acceptable: `output/` is gitignored throwaway, and the PDF —
  the artifact anyone actually shares — embeds the art outright.
- **`render()` resolves the output path before rendering the template**, not
  after, because a template that references a neighbouring file has to know
  where its own output lands.
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
