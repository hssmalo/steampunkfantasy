# The Site Index names Races as well as Army Packs

ADR 0028 made the Site Index the site's authored statement of what it
publishes, and every entry in it was an Army Pack. The site therefore published
armies people fielded and the rules those armies play by, and nothing about the
catalogue those armies were built from — a reader could see a Showcase Elf list
but not what an Elf can field. The Race Overview exists (ADR 0031); it just had
no way onto the site.

Publishing it means a second kind of thing enters the index, and the Site Index
and the Landing Page both have to answer for that.

## Decision

**The Site Index gains an optional `[races]` table — one heading and an ordered
`publish` list of Race Names — and the site renders a Race Overview, in both
Site Formats, for every Race it names. The Landing Page grows a Races section
between the Rulebook and the first Army Pack.**

```toml
[races]
heading = "Races"
publish = ["abomination", "darkelf", ...]
```

### Why `[races]` is not shaped like `[[packs]]`

The symmetry with `[[packs]]` is a false friend. A pack entry carries its own
heading because **a pack is a section**: three packs are three headings and
three tables. Races are **one section over a list** — eight per-race headings
would be absurd — so they are one table with one heading and a list inside it.

The shapes diverge because the Landing Page shapes diverge, not because the
authored-index family broke. Both are still ordered, authored, and unsorted;
both still say "publish exactly this". The inner key is `publish` rather than
`races` because `races.races` stutters and `publish` names the editorial verb
the whole index is about.

### Why all eight Races

ADR 0028 had to argue its way out of an editorial exclusion: a live tournament
roster is a claim about who is fielding what, and the build should not make it
unilaterally. A catalogue makes no such claim. A Race Overview says what the
Race can field, which is true whether or not anyone published it, so there is
no editorial reason to hold one back — and a partial race list would read as an
accident rather than as a decision. The list is still authored, so a ninth Race
appears on the site when a human adds a line, not when a file lands in `races/`.

### Absent block versus empty `publish`

| Site Index | Landing Page |
|---|---|
| no `[races]` block | no Races section at all |
| `[races]` with `publish = []` | the heading, and a header-row-only table |

The distinction carries meaning and is deliberate: no block says "this site
does not publish Races"; an empty `publish` says "it does, and right now there
are none" — a visible statement that something is missing rather than a silent
one. The heading always comes from the index; a default heading in `site.py`
would put an editorial string in code, which is what ADR 0028 rejected.

### The Landing Page seam

`render_landing_page` used to sniff what it was given: a page with no group
became a labeled line, a page with one became a row in a table built out of
Army Products. Adding Races to that renderer means a branch — and the next kind
of section means another.

Instead the renderer stopped knowing what a pack is. It takes an ordered list
of generic sections (a heading, a header row, rows of link cells, trailing
lines) and renders exactly that. Three small builders — `loose_section`,
`pack_section`, `race_section` — turn rendered pages into sections and hold all
the knowledge of what a Rulebook, a pack, or a Race looks like. *What the site
contains* is `render_site`'s business; *what a reference page looks like in
HTML* is the Landing Page's. A fourth kind of section is a fourth builder.

Section order became explicit with it: Rulebook, then Races, then packs —
rules, then what a player can field, then what players did field. It used to
fall out of an ungrouped/grouped split, which is the same sniffing wearing a
different hat.

## Alternatives rejected

**`[[races]]` with a heading each.** Consistent with `[[packs]]` on the page of
TOML and nowhere else: it invites eight headings over eight one-row tables, or
else eight headings that must all be written identically and are silently
ignored bar the first.

**A `race-overview` column inside the pack tables.** Races are not Armies, and
a Race appears in several packs or none. The column would be empty for most
rows and duplicated across the rest.

**Publishing every `races/*.toml` by scan.** The scan-versus-index argument of
ADR 0018 and ADR 0028, one level up: a Race half-written for next season
becomes a published catalogue the moment the file exists. A scan also has no
order and nowhere to put the heading.

**Tagging sections with a kind and dispatching in the renderer.** The sniffing
again, made explicit. Every future kind of section is then an edit to
`render_landing_page`, which is the thing this change was for.

**A section class hierarchy, each kind rendering itself.** Distributes the HTML
across a class per kind, so the page's layout is no longer readable in one
place, and grows a class for what is a heading and a table.

## Consequences

- The site build grows sixteen renders — eight Races in two Formats, half of
  them through pdflatex. ADR 0028 already named serial render count as the
  thing that will eventually need parallelising; this brings that day closer
  without changing the answer.
- A Race the Site Index names but disk lacks fails the whole build, exactly as
  a missing pack does. The named Races are loaded up front, beside the packs,
  so the build fails before anything renders rather than midway through.
- `publish` is typed as a Race Name, so a typo in the index is a schema error
  naming the Races there are rather than a row that quietly never appears.
- Race Overviews publish with their Rules Reference, like every other Product
  on the site: a catalogue naming rules a reader cannot look up is a worse
  page than a longer one.
- Nothing in `just check` loads `armies/site.toml`, so a bad entry still
  surfaces first in the deploy. That gap predates this change and is untouched
  by it.
