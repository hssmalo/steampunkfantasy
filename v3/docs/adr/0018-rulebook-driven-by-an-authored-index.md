# The Rulebook is driven by an authored index, not by the contents of `rules/`

ADR 0005 named the Rulebook as a Product "built from the `rules/*.toml`
configs". Building it forced the question that phrasing hides: *which* files, in
*what order*, and how does the pipeline know what shape each one has?

"Every file in `rules/`" answers none of that. It has no order, it silently
promotes a scratch file into a published chapter, and it cannot express the one
thing a rulebook most needs — an editorial decision about what the rulebook
*is*. It also does not survive contact with the data: `rules/` today holds four
TOML files of which only three have a schema and a loader.

## An ordered index that names a kind per section

**Decision: the Rulebook is an authored index file, `rules/rulebook.toml`,
listing in order the Sections it contains. Each Section names its source, the
title it appears under, and a **Section Kind**.**

A Kind is the shape of a Section's source. It binds to exactly two things: one
parser, registered in `spf.render.rulebook`, and one template partial per
family, found by name at `templates/<family>/general-rules/<kind>.<ext>.jinja`.
Nothing about a partial is registered — the convention *is* the binding, which
keeps `main.<ext>.jinja` dumb, per ADR 0005: it loops over Sections, emits the
heading, and includes.

The index lives in `rules/` and not in `configs/spf.toml` because it is game
data — an editorial statement about the game — not developer configuration. It
is TOML because every other authored data file is, so it loads through the
existing configaroo + `StrictModel` path and needs no new dependency.

The registry deliberately copies the Product and Format registries: a frozen
record in a module-level dict, a `register_*`, and a `get_*` that fails with
"Unknown kind 'x'; known kinds: …". Three registries with one shape is cheaper
to learn than three with three.

**A bad index fails the build**, naming the Section's 1-based position as a
human would count it down the file. A Rulebook that silently drops a chapter is
worse than one that refuses to build: the missing chapter is invisible in the
output, and the reader it fails is a player at a table.

## Alternatives rejected

**Infer the Kind from the filename** (`special.toml` → the specials shape). It
makes the filename load-bearing: renaming a data file would silently change how
it renders, and two files could never share a shape — which is exactly what the
`markdown` Kind exists to allow, since every future free-text section uses it.

**Render any table generically, from column declarations in the index.** This
throws away the Pydantic schemas that already describe these files precisely,
and with them every per-shape nicety — a damage table and a token list are not
the same document even though both are "essentially a table".

## Consequences

- Adding a rules file to the Rulebook is a **data edit** (a new `[[sections]]`
  entry). Adding a *new shape* is that plus a Kind registration and two
  partials. Neither touches `build_rulebook` or `main.<ext>.jinja`.
- The rules format can keep moving without the pipeline moving with it, which
  is the point while the rules are still in development.
- `assaultretreat.toml` stays out of the Rulebook until it has a schema and a
  loader. The index makes that omission explicit rather than accidental.
- The index is validated in CI by `spf rules rulebook`, wired into
  `just validate`: resolving the index *is* validating it.
- Section titles come from the index, so a Markdown source's H1 is dropped and
  its remaining headings nest beneath the index's title.
