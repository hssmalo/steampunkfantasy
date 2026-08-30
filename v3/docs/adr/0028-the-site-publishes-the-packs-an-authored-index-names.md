# The site publishes the packs an authored index names

ADR 0023 put the reference site on GitHub Pages and, in passing, excluded the
tournament packs from it: "publishing a live tournament roster is an editorial
call the build should not make unilaterally." That sentence names the 2025
pack, because in 2025 it was the only tournament pack in the repository. It
reads today as a standing rule about tournament packs as a class, and it is
now the wrong rule for two separate reasons.

**A tournament that is over is history, not a live claim.** The objection was
to the build asserting, mid-event, who is fielding what — a roster that can
still change, published by a machine that does not know it changed. An
archived tournament makes no such claim. The players who want their pack are
the ones who played in it, and the ones who want to read a past tournament's
armies have nowhere else to get them.

**The editorial call now has somewhere to live.** 0023's real objection was
"unilaterally", not "published": the build was picking the site's contents by
itself, because the showcase pack was hardcoded into `render_site`. What the
build publishes is now read from an authored file, so a pack appears on the
site because a human wrote it into an index — the same reasoning ADR 0018
applies to the Rulebook, and the Army Pack Index applies to a roster.

## Decision

**The site publishes exactly the Army Packs the Site Index
(`armies/site.toml`) names, in the order it names them, under the headings it
gives them. ADR 0023's exclusion of tournament packs is superseded: a pack is
excluded by being absent from the Site Index, never by a rule in code.**

The Site Index is the third member of the authored-index family — Rulebook
Index, Army Pack Index, Site Index — and is read the same way: an ordered
list, no directory scan, no sort. Adding next year's tournament is three lines
of TOML.

`armies/demo.json` stays unpublished, and 0023's reason for it is untouched:
it is a fixture, not an Army anyone fielded. It is in no Army Pack, so no
index can name it.

## Alternatives rejected

**Glob `armies/*/pack.toml`.** The site would then publish whatever directory
happens to exist — a half-finished pack for a tournament still being planned
becomes a published roster the moment someone creates the folder. This is the
scan-versus-index argument ADR 0018 already settled one level down, and
publishing is a *more* editorial act than rostering, not a less one. A glob
also has no order and no place to put a heading.

**A list of packs in `site.py`.** It publishes the same three packs today, and
it puts the editorial decision — which is game data, authored by the people
who run the tournaments — in developer config, where changing it is a code
change and a code review. ADR 0018 rejected this shape for the Rulebook for
the same reason.

**Keep the exclusion and publish tournaments by hand.** Whoever wants a pack
must then clone the repository and run `spf`, which is the problem the site
exists to solve.

## Consequences

- The Landing Page is organized by pack: one section per Site Index entry,
  with the pack's Armies as rows and its own Army Pack document below them.
  Adding a pack is a data change, not a layout change.
- The site's render count grows with every archived tournament — twelve
  Armies at four renders each, today. CI runs this serially on merges to
  `master`, where a cached TeX Live install dominates a cold run.
  Parallelising the renders is the escape hatch when that stops being true:
  weighed here, deliberately not built.
- A pack the Site Index names but disk lacks fails the whole build, like any
  other missing source. ADR 0023's whole-site failure policy reaches through
  the new indirection: a site with a silently missing section is exactly the
  partial publish that policy exists to prevent.
- The heading a pack appears under lives in the Site Index, not in the pack's
  own `title`. The title belongs to the Army Pack document's cover, so
  retitling the document does not reflow the site.
