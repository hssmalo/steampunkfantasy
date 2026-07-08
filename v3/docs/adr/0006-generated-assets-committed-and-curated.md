# Generated assets are committed & curated, in a store separate from Renderings

We're using AI services to add color and atmosphere — Lore (Markdown story),
Images, and 3D Models — generated from the race/unit TOML. Each generated
artifact is an **Asset**: produced by an AI service, **reviewed by a human, then
committed** to a dedicated `assets/<race>/` tree (with `images/` and `models/`
subdirs and a top-level `lore.md`). A shared `spf/assets/` subsystem and a
`spf assets` CLI group own the generate → curate → commit spine; each kind plugs
in its own service.

**Why:** AI generation is non-deterministic and costs money, and a rulebook
image / faction story needs a human quality gate before it becomes canonical. So
Assets are treated as source-of-truth game data (versioned, reviewed), *not* as
throwaway build artifacts. We rejected generating on-demand at render time: it
would put a different, unreviewed image in every build and repeat the API cost.

## Consequences

- Assets are **distinct from Renderings** (ADR 0005): a Rendering is a gitignored
  build artifact regenerated deterministically from data; an Asset is a curated,
  committed input. `render/` only ever *consumes* committed Assets — nothing
  generates an Asset during a render.
- The **Model** asset kind overloads the domain **Model** (a single figure in a
  Unit); a Model asset is the printable mesh of such a figure.
- Two legs are deliberately **out of scope** of the generation subsystem and
  belong to future work: how `render/` embeds Images, and the 3D
  print-on-demand *ordering/fulfillment* flow. `spf assets` stops at a committed
  Asset.
- Which specific AI service backs each kind is deferred to each kind's own
  design session; the spine is service-agnostic.
