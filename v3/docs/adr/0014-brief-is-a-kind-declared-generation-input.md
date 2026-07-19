# The Brief is a Kind-declared generation input

ADR 0011 made `spf assets list` answer "which Targets have an Asset?". It could
not answer the question a curator asks next — "which Targets *could* have one?"
Of 101 Targets, **39 have no description at all**, and three races (darkelf,
dwarf, gnome) are essentially unbriefed entirely. A red ✗ on those rows means
*blocked*, not *queued*, and the listing rendered the two identically:

```console
$ spf assets list dwarf --kind image
Dwarf
  Image
  - dwarf                    Dwarf                    ✗ no brief
  - dwarf_infantry           Dwarf Infantry           ✗ no brief 2 candidates
```

So more than a third of the worklist was noise: generating for any of those
rows fails, and nothing on screen said so before the GPU time was spent.

## The Brief is a thing, and the Kind declares it

**Decision: a `Kind.brief` field naming the authored text that Kind generates
its Candidates from.** For an Image that is the Target's `description`; Lore
and Model will declare their own when they register.

This is the same argument `Kind.targets` won in ADR 0011. Which text a kind
generates from is exactly the sort of per-kind fact the registry already holds,
so the listing code — and `--missing`, and the generate guard — never change
when a Kind lands. `Target` carries the resolved Brief, so nothing downstream
of `targets()` knows which field it came from.

The term is **Brief**, not *prompt*: `assets.image.prompt` is already the
preamble *file*, "Negative Prompt" is already a glossary term, and the composed
positive prompt is a third thing. The Brief is an *ingredient* of the Prompt.
Nor *seed* — `--seed` is the RNG seed.

Rejected: *Prerequisite* (names a status, not a thing, and is unwieldy as a
flag); *Source* (collides with `Service.generate(source=…)`, which is the
composed prompt, not the Brief).

## A callable, not a field name

**Decision: `brief` is an extractor, `Callable[[Described], str]`, rather than
the *name* of a field to read.**

This is the paragraph that matters most to a later reader, because a field name
is obviously simpler and this looks like over-engineering. It is not: when this
was written, **Lore's Brief shape was unknown**. Lore plausibly generates from
the whole `RaceConfig` — units, equipment and all — rather than from one string
field, and `brief_field: str` cannot express that. The callable is the escape
hatch that keeps Lore from being boxed in by a decision made before anyone knew
what Lore needed.

`Kind` is a frozen dataclass holding a callable, so it is no longer trivially
`repr`-comparable in a test failure. Accepted.

Rejected: `brief_field: str` (see above). Rejected: a presence-only `bool` —
it answers the column's question but kills `--briefs`, which needs the text.

## Required, with no default

**Decision: `brief` has no default, so every Kind must declare it.**

ADR 0011 made the same call for `Kind.targets`, and here the failure mode is
sharper. A default of `attrgetter("description")` would not error on a Lore
Kind that forgot to set it — it would silently generate Lore from the race's
one-line blurb instead of its real Brief, and the output would look plausible.
A default also *assumes* the single-field shape that the callable exists to
avoid assuming.

The cost is 10 construction sites updated in one commit, 9 of them in tests.

## Normalization happens at `targets()`, not at display

**Decision: `targets()` collapses newlines and runs of whitespace to single
spaces and strips both ends, so `Target.brief` is always one clean paragraph.**

Briefs are authored as multi-line TOML strings. Normalizing at display would
leave the Service receiving the ragged original while the screen showed the
tidy version — two different strings under one name. Normalizing at resolution
means the text shown by `--briefs` *is* the text sent to the Service, which is
the entire point of proofreading it there.

## The seam holds

**Decision: `survey.py` is unchanged; the CLI reads `row.target.brief`.**

ADR 0011 split these two on whether they touch disk: `targets()` is pure TOML,
`survey()` reads the filesystem. A Brief is a TOML fact, so it stays on the
pure side and rides into the listing on the `Target` that `Coverage` already
holds. Lifting a `has_brief` onto `Coverage` would have put a TOML question on
the filesystem side of that split for no gain.

## Consequences

- **Candidates generated before this change from a multi-line Brief will not
  reproduce byte-identically from the same `--seed`.** The normalized Brief is
  a different string, so the composed prompt differs and the Service returns
  different images. This is accepted deliberately, and is called out here
  because a reader will otherwise reasonably assume a *listing* change could
  not affect generation.
- **A fully-briefed race renders almost as it did before.** The marker is
  asymmetric — only Brief-less rows carry it — so briefed rows gain no word.
  They do gain the marker's fixed-width slot, which shifts the candidate count
  right by its width; that slot is what keeps the count aligned between marked
  and unmarked rows.
- **`--briefs` prints for every row**, unlike `--candidates`, which is gated on
  a non-empty list. Proofreading wants the briefed rows most of all.
- **A Brief is printed with markup disabled.** It is arbitrary authored prose,
  and a `[` in it would otherwise parse as a Rich tag and swallow the line.
- **The 39 gaps are now visible and will be filled over time**, so tests must
  not reach for a race that happens to be unbriefed today — they force the
  state through a Kind's own extractor instead.

Out of scope: the `--missing` interaction, where a Brief-less Target aborts the
whole batch (filed as issue #61); any `spf` command that *writes* Briefs; and
Lore's and Model's actual Brief extractors, which land with those Kinds.
