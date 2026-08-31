# A Variant is shared instance prose, keyed by an id the rule owns

A **Variant** is a named string defined once on a Special in
`rules/special.toml`, which an **Instance** or a **Case** draws into its prose
slot instead of spelling it out.

```toml
# rules/special.toml
[special.ammo.variants.always_treated_as_loaded]
text = "Always treated as loaded"

# races/elf.toml
[[equipment.elf_bow.range.specials.ammo]]
variant = "always_treated_as_loaded"
```

The Race data carried 471 `text` lines over 341 distinct strings: 61 strings
written twice or more, covering 193 lines. Roughly 130 lines of pure
duplication, retyped by hand across eight Race files.

## The drift is the argument

Duplication by itself is only untidy. What forces the issue is that the copies
have already stopped agreeing. `ammo` says the same thing two ways —

> "Always treated as loaded" (29×) and "Always loaded" (3×)

— and `resistance` says one thing four ways:

> "While at least one elite is alive" (4×), "As long as at least one elite model
> is alive" (2×), "As long as 1 elite model is alive" (2×), and "While at least
> one superelite model is alive" (3×)

Nobody decided any of that. Each spelling is a line someone retyped from memory
rather than copied, and every further Race file is another chance to add a
fifth. A shared string cannot drift from itself.

## Why not a Version

`versions` and `variants` sit side by side in one registry and look alike in the
file, and they are not alike.

A **Version** overlay carries `effect` — *the rule's own prose* — and is keyed by
a **Ref**, `damage_type.fire`, because it answers "when this Ref resolves to
*that*, here is my text for it". A Variant carries `text` — *one occurrence's*
prose — and is keyed by a bare id, `always_loaded`, which names nothing outside
the rule that declares it.

Different field, different object, different key. Folding one into the other
would make a single table mean two things, and the reader who has to tell them
apart is a year away from anyone who remembers why.

## Why the pool is rule-local

Of the 61 repeated strings, **zero** cross a rule id. Every duplicate of
`"at point blank"` is on `area`; every duplicate of `"Always treated as loaded"`
is on `ammo`. A global prose pool would buy nothing and would need a
Namespace-like vocabulary to govern who may name what.

## Why the shape decides the role

One `variant` field fills `text` on a prose-shaped Instance, `preamble` on a
case-shaped one, and `text` on a Case. That is not a convention — ADR-0030
already makes `text` and `preamble` mutually exclusive by shape, so the slot a
Variant fills is *fully determined* by the Instance the reader is looking at.

The alternative, a second `preamble_variant` field, doubles the surface for a
distinction the schema already validates, and would never appear on a Case at
all.

The same string may be a preamble in one place and a text in another — `"at
point blank"` and `"at long range"` are each already written in both positions on
`area` — so the pool is bare strings with no role declared.

## Rejected: the sentinel string

The obvious design is `text = "variant:always_loaded"`, and its rejection is not
obvious, so it is worth recording. `CONTEXT.md` holds that

> Every Ref is *structural* — a declared field or a typed Arg, never a name
> mentioned in prose

which is what makes the reference graph traversable. A magic prefix inside a
prose field is a reference no tool can see without knowing to look for it.

It is also not a Ref. ADR-0024 fixes a Ref as `<namespace>.<id>`, two segments,
and `registry.py` enforces that shape; `special.ammo.always_loaded` would claim a
namespace that does not exist.

`text = { variant = … }` was rejected for a different reason: it makes `.text` a
union at every read site, and the Race files contain zero inline tables today.

## Rejected: args on a variant

A Variant carries `text` and nothing else. `"at point blank"` is written with
`args.N = 4` in one place and `N = 2` in another — the shared thing is the prose
alone, and the numbers stay where they are written. Args on a Variant would also
add a third layer to a merge order that is already rule → instance → case.

`name` is excluded for its own reason: an atmospheric name is deliberately
per-Instance, and a shared one would be a different feature wearing this one's
clothes.

## Why the pool lives only in the registry

The registry already owns every other kind of Special prose — `effect`,
`flavor`, `example`, `versions` — so a Variant joins what is there rather than
opening a second home for prose. Thirteen of the repeated strings already span
several Races, so a per-Race pool would force a "which file?" decision on every
new Variant and a *move* the day a second Race adopts one.

The strings confined to one Race today are not race-specific either: "Reroll all
success in assault while crawling" is a general mechanic that only darkelf
currently has crawling for. If Race-local prose ever outgrows the registry, a
per-Race table is purely additive.

## Consequence: two spellings, both valid, forever

An Instance may now write its prose inline or name a Variant, and both render the
identical line — `special_lines` deduplicates on the *rendered* string, so an
Instance naming a Variant and one writing the same sentence longhand collapse
into a single printed line automatically.

That is deliberate. It is what let the corpus migrate 189 sites in one reviewable
commit whose golden output is byte-for-byte unchanged, and it is why writing the
prose longhand is a **lint** finding rather than a load error: a half-migrated
corpus is a tidiness question, not a correctness one.

What *is* a load error is naming a Variant the rule does not define. The id is
the lookup key, so a miss is prose the reader would silently lose.

## What was deliberately not done

Only exact duplicates were collapsed. Deciding that `"Always loaded"` means the
same as `"Always treated as loaded"` is a rules judgment, and belongs to the
maintainer rather than to a mechanical pass — so the two sit side by side in
`spf special show ammo` until someone rules on them. That the tool now shows
them side by side is itself the point.
