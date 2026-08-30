# Extra Damage is versioned over the kinds it applies

Supersedes one section of
[ADR-0024](0024-specials-are-identified-instances-over-a-registry.md): its
*"Consequence: four ids must be renamed"* argument, which held that `fire`,
`minor_acid`, `poison` and `gear_disruption` are eight distinct Specials, one
per kind per slot. Three of those four kinds are not rules at all.

Extra Damage is **one rule per slot**, versioned over the thing it applies:

```toml
[special.range_extra_damage]
signature = "{version}"

[special.range_extra_damage.variables]
version = { type = "ref", namespaces = ["token", "damage_type"] }
```

Fire, Minor Acid, Acid and Poison are the **kinds of thing Extra Damage
applies**, exactly as damage types are the kinds of thing a Resistance is
against. They already live in the `token` and `damage_type` registries, which
own that vocabulary; naming them again as Specials states it twice.

**The evidence is the corpus.** Every form in use is one of five kinds crossed
with one of two slots — a product, not ten independent rules. All eight
anticipated rules ADR-0024 created had **zero instances**; nothing ever wrote
one, in either slot. And a ref's arguments travel with the ref, so
`version = "token.poison"` pulls `token.poison`'s own `N` into scope and
`{version}` renders `Poison[6]` — the strength prints where the token declares
it, and required-ness is computed per instance rather than per rule.

**What ADR-0024 got right and this keeps:** the assault/range split. The assault
forms count hits and the range forms are flat, so there are two rules, not one
with an optional slot. The range signature is then a single `{version}` with no
optional handling at all.

**Gear Disruption stays a rule of its own, in both slots.** It places no damage:
it is "only if the target is a drone, roll a die, at `N+` place a shaken token" —
a gate and a die roll. Making it a version would require `token.shaken` to grow a
threshold it has no business owning; a shaken token is a shaken token whatever
placed it.

**Rejected: one `extra_damage` with `slots = ["assault", "range"]` and an
optional ratio.** It needs a two-clause effect covering both slots, and merges
two mechanics ADR-0024 correctly separated.

**Rejected: `M = 1` on the six ratio-less Fire instances.** The rule text they
came from says "all enemy units hit at least once get a fire token" — one token,
not one per hit. `M = 1` asserts the second.

**Rejected: mapping the kinds onto `damage_type` alone.** `damage_type` has no
`minor_acid` — acid's `see_also` covers both markers — and gear disruption is
not harm at all. The kinds live mostly in `token`; `damage_type` carries psychic.
`special.immunity` already precedents a multi-namespace ref.

## Three additions to the rules schema

Each is general, and each is what the corpus needed rather than what Extra
Damage needed:

- **`optional = true` on a variable config.** A declared variable an instance may
  leave out. The six ratio-less Fire instances are the reason: the ratio is
  genuinely absent, not one.
- **`type = "formula"`, a new `ScalarType`.** A value not known at authoring
  time — "Poison[X] where X is the power of the poison gas" — accepted as any
  non-empty string and rendered verbatim. It answers the open question `heal`'s
  and `repair`'s `todo` already asked; migrating their instances is separate
  work.
- **Signature elision.** A `[…]` group whose placeholders are all unfilled is
  dropped rather than printed literally, so a ratio-less Fire renders `Fire` and
  not `Fire[1 for {M}]`. This serves any unfilled variable, nested ones included.

## What the model still cannot say

Two shapes in the corpus have no expression here and stay as prose on the
instance, deliberately rather than by oversight:

- **Range-banded escalation.** `acid_breath` (elf, ogre, darkelf) and
  `acid_cannon` escalate by distance: "acid at point blank, minor acid
  otherwise". A version ref names one kind and cannot name a band.
- **"Choose one".** `goblin_bow_battery` offers a choice of three kinds for all
  shots. Three instances assert all three, so each carries the choice as text.

Both are open questions for the game designer, not defects to work around.
