# The Site publishes Art at stable URLs

ADR 0017 decided that a Rendering references the committed Image Asset **in
place**, never copying it. ADR 0023 decided that the deployed artifact is
`output/`, built by CI and uploaded whole. The two had never met: `assets/`
lives beside `output/`, not inside it, so every published `.html` carried an
`src` that climbed *above* the site root and 404'd. PDFs were unaffected —
pdflatex embeds the bytes.

No amount of copying fixes that on its own. A path that escapes the artifact
root cannot be made to resolve inside it, so the spelling has to change too.

## The Site publishes art under `/art/<race>/<name>.png`

**Decision: the site build copies every committed Image Asset into
`output/art/<race>/<name>.png`, and site-rendered HTML references it there.**

The namespace is deliberately *not* a mirror of
`assets/<race>/images/<name>.png`. The published bytes are *selected* from the
store rather than served from it, so a store-shaped URL serving different bytes
would be misleading. The `images/` segment exists only to keep Asset Kinds
apart in the store — a distinction the site does not make.

**All of `assets/` is published, unconditionally**, not only what some page
happens to reference. A URL contract conditional on another page's content is
not a contract, and the whole store is comfortably small against what Pages
will hold.

## One URL per image; the bytes behind it may change

**Decision: the Site publishes the best available bytes at a URL that does not
move** — the downscaled **Rendition** when one is committed, the Asset itself
otherwise. Today there are no Renditions, so it is always the Asset.

That is what lets downscaling land later with no coordination: the same URLs
silently begin serving smaller files, and nothing here changes. Originals stay
in `assets/` and are never published.

A missing Rendition is a **fallback, never a render failure**. It must not trip
ADR 0023's whole-site failure policy: there is nothing wrong with a site that
serves full-size art.

Pages serves a short `max-age`, so clients converge on the new bytes on their
own. No cache-busting scheme, and no URL that encodes a version.

## Pages is the CDN, and the origin is configured once

**Decision: no separate CDN. `config.site.base_url` is the single definition of
where the Site lives**, so moving to a custom domain is a config change rather
than a re-render.

Site HTML gets a URL **rooted at the origin**, `/<base path>/art/…`, built from
the same config value. The base path is not decoration: this is a *project*
Pages site, served under `https://hssmalo.github.io/steampunkfantasy/`, so a
URL rooted at the bare origin climbs out of the site exactly as a
document-relative one climbs out of the artifact — the bug this ADR exists to
fix, relocated one level up. An API handing a client the whole URL gets it from
`absolute_art_url`, which puts the origin back in front of the same path.

## The spelling is bound per render, not per template family

ADR 0017's axis is the *template family*: the view-model says **which** Asset,
and LaTeX and Markdown each spell it their own way. This adds a second axis —
the **destination**: the same Markdown template serves a local render and a
Site render, and those need different spellings of the same Asset.

**Decision: `render()` binds an `image_src` filter alongside the output
directory.** The default spells the Asset relative to the written document
(ADR 0017, unchanged); the Site passes the URL it publishes the art at. The
view-model still carries a `Path` and still says only which Asset it means.

Rejected:

- **Spelling the URL into the view-model** — breaks ADR 0017's "the view-model
  says *which* Asset, the family says how".
- **Post-processing the rendered HTML** — parsing generated output to rewrite
  `src` attributes is fragile and invisible from the template.
- **A second set of site templates** — duplication of every layout decision,
  paid forever, to vary one attribute.

## Consequences

- **Site-rendered HTML no longer opens over `file://`.** A root-absolute `src`
  is exactly what ADR 0017 rejected, for the UNC-boundary reason recorded
  there. The blast radius is narrow: only `spf render site` uses this spelling,
  and a plain `spf render army-rules --format html` keeps the relative one and
  keeps working locally. Site output is for the site.
- **The site build copies bytes into `output/` for the first time.** Everything
  else there is rendered in place by `render()`.
- **LaTeX is untouched.** It keeps the absolute filesystem path to the
  full-size original (ADR 0017), and will keep it when Renditions land — a PDF
  is the artifact people print.
- **`.github/workflows/docs.yml` needs no change**: the uploaded artifact is
  still `v3/output`, which now contains `art/`.
- The published URL is a **deployment** detail, not a domain term. `CONTEXT.md`
  gains no new entry for it — a URL is how you reach an Image, not a new kind
  of thing.
