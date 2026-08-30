# A Special instance is either prose-shaped or case-shaped

An **Instance** of a Special takes one of two shapes. *Prose-shaped* is what it
has always been: the rule's **Signature** filled in with the Instance's **Args**,
followed by free `text` about the occurrence. *Case-shaped* is new: a `preamble`
of prose scoping a list of `cases`, each supplying its own Args and a scrap of
prose saying when those values apply.

```toml
[[equipment.tail_gatling_gun.range.specials.area]]
preamble = "If not using aim, fire once at all enemy models within range and within front arc"

[[equipment.tail_gatling_gun.range.specials.area.cases]]
args.N = 5
text = "at normal range"

[[equipment.tail_gatling_gun.range.specials.area.cases]]
args.N = 6
text = "at long range"
```

The two shapes are mutually exclusive: `text` and `cases` on one Instance is a
load-time error. Every Instance written before this ADR is prose-shaped and
stays valid untouched, which is what lets the corpus migrate a few weapons at a
time instead of all at once.

## Why the values are nested rather than flat

The rejected alternative — the one the issue itself sketched — is a flat list
where a preamble is a *sibling* Instance printed before the value-bearing ones.
It is simpler, and it cannot say what Dwarf Steamblower says. That weapon
carries **two** condition groups, each scoping its own three thresholds:

> If fired from a unit with 1-2 alive models: Area(4+) at point blank, Area(5+)
> at range=2, Area(6+) at range=3 or 4. If fired from a unit with 3-4 alive
> models: Area(2+) at point blank, Area(4+) at range=2, Area(5+) at range=3 or 4.

In a flat list nothing says which preamble governs which values; the reader
recovers it from the order, and a `replace` further down the **Source Chain**
can silently break that order. Nesting makes the scope structural. Steamblower
is the forcing example for the whole shape — if anything here looks arbitrary,
check it against Steamblower first.

## Why `preamble` rather than `condition`

Only some of the real prose is conditional ("If not using aim"). Most of it is
an instruction: "Choose one hex", "Target enemies in all hexes within front
arc". The field's contract is positional — prose printed before the values it
scopes — so it is named for the position it holds rather than for a meaning two
thirds of its uses do not have.

## Why a Preamble with no Cases is an error

Prose that scopes the Cases of **one** Instance is a **Preamble**. Prose that
scopes **several** Instances, or holds regardless of the rule, goes up a level
to the carrier's `note`, which already exists and already renders. Steamblower
shows both in one weapon: "Choose one hex which all models in this unit fire at"
governs both condition groups, so it is a `note`, while each "If fired from a
unit with…" governs only its own three thresholds, so each is a Preamble.

Rejecting a Case-less Preamble is what keeps that distinction from eroding. The
alternative — a Preamble that renders alone — would give one sentence three
possible homes, and prose with three homes is how the vocabulary drift ADR-0024
was written to end got started in the first place.

## Args are inherited by each Case

An Instance's own Args are merged into every Case, which may override or add to
them. A Ref-valued Variable that is constant across the Cases is then written
once rather than repeated into each — repetition being exactly what this
repository keeps discovering has drifted. Validation runs on the merged Args,
once per Case, and a broken Case names its 1-based position, because the Cases
of one Instance are otherwise indistinguishable in an error message.

## What is not deduplicated

Instances that read alike are printed once: the Source Chain legitimately
delivers the same Resistance three times without anyone writing it three times.
Cases are not deduplicated. They are hand-written in one array in one file, so
two Cases that read alike are a typo, and a typo should stay visible.

## Cost

The `area` rule now has ~20 Instances still prose-shaped alongside five migrated
ones, so its rendered output is inconsistent until the rest follow. Its `N`
Variable is `optional` for exactly that reason; it is tightened to required once
the last prose-shaped `area` Instance is gone.
