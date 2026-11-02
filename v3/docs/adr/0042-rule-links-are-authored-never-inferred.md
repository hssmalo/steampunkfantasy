# Rule Links are authored, never inferred

A **Rule Link** comes from a typed Arg in a filled **Signature** or in Instance
prose, or from `{label:<namespace>.<id>}` written in prose. The Ref is validated
at load. An authored link is an edge in the Rules Reference walk, from text a
document actually prints, so it can't dead-end.

## Why not match names

12 names are shared across records, and `Poison`, `Fire` and `Acid` each have
three. A word match finds "fire" 158 times in Instance prose, nearly all the verb
or "fire order" (only 4 are "fire damage"). Inferred links would be confidently
wrong.

## Why a required label

Prose rarely matches the display name ("poison token"), and `{version.id}` already
means something else, so a bare `{token.poison}` would read ambiguously.

## Why structured text rather than Markdown strings

Sending every field through `md_to_latex` would start treating `*` and `_` in
`latex_escape` fields as formatting, changing existing output. Structured text
also keeps instances that print alike but point at different Refs apart, and gives
console and lint a plain form from a single parser.

## Allowed fields

The list is exhaustive, and any other field holding link syntax is a lint finding:

- Records: `effect`, `remove`, `example`, Variant and Version prose.
- Instances: `text`, `preamble`, Case text.
- Damage table rows and `notes`.
- `note` on Unit, Model, Equipment, Assault and Range.

So flavor text, working notes, `explanation`, `description`, `lore`, `tip`, names,
signatures and to-hit numbers take no link. Rulebook `.md` sources don't either, and
are checked by file. A field can be added later without changing the syntax.

## Which links are edges

The walk follows a link only from text the document prints. An entry prints a
Record's `effect` and `remove`, so those are edges. It does not print `example`,
Version prose or the Variant pool, so a link there is validated, and the Rulebook
prints its label, but it adds no entry. A Variant counts as drawn by an Instance.
A prose edge does not also print on the `See also` line.

## Where the gate runs

A bad Ref or malformed link is a Load finding
([ADR-0036](0036-lint-owns-both-gates.md)). Notes and damage tables are checked in
the same `RaceConfig` gate as Special instances, which already holds the registry.
Lint owns the softer findings: link syntax in a field that takes none, and a label
whose brackets would break the Markdown link.

## Amends

- The glossary's "never a name mentioned in prose": what makes a Ref structural is
  that it is declared and validated.
- [ADR-0041](0041-the-rules-reference-walks-every-level.md): the walk also seeds from
  the Rule Links in printed prose, and follows them from a Record's `effect` and
  `remove`, as well as following `places` and `see_also`.
