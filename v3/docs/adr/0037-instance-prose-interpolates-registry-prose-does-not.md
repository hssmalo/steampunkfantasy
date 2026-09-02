# Instance prose interpolates; registry prose does not

A placeholder written in an **Instance**'s prose — `{N}`, `{version}`,
`{version.id}` — is filled from that Instance's **Args**, by the same
interpolation that has always filled a **Signature**. The prose a **Variant**
supplies is filled the same way, because a Variant is a spelling of the prose
slot rather than a layer above it (ADR 0032).

```toml
# rules/special.toml
[special.fire_order.variables]
N = { type = "int", min = 2, max = 10, optional = true }

[special.fire_order.variants]
load_n_shots = "May be load up to {N} shots, fire them one at a time"

# races/elf.toml
[[equipment.pentagun.unit_specials.fire_order]]
variant = "load_n_shots"
args.N = 5
```

Before this, `{N}` in a Variant rendered as the four characters `{N}`, which is
what `elf.toml` printed on two weapons.

## The dividing line is whose prose it is

`{N}` already appears in the `effect` of 23 rules and is printed there verbatim,
because a rule's own prose is generic: there is no Instance, so there is nothing
to fill from. Instance prose is about one occurrence, and an occurrence has Args.

So the same braces mean two things in one file, one table apart, and the field
name is what tells them apart:

| prose | belongs to | braces |
|---|---|---|
| `effect`, `flavor`, `example`, a **Version** overlay's `effect` | the rule | printed as written |
| `text`, `preamble`, a **Case**'s `text` — inline or via a Variant | the occurrence | filled from Args |

**Rejected: escaping registry prose as `{{N}}`.** It would make the rule's own
prose harder to write in order to make one sentence of this ADR shorter, and it
would rewrite 23 rules to say what they already say.

## Why the whole slot, not just Variants

ADR 0032 holds that an Instance writing prose longhand and one naming a Variant
"render the identical line", and `special_lines` deduplicates on the rendered
string. Filling `{N}` only inside a Variant would break that: `variant =
"load_n_shots"` and the same sentence typed out would stop collapsing, and
`text` would become the way to smuggle an unfilled placeholder past the gate.

The rule belongs to the slot. `name` is deliberately **not** in the slot: it is a
heading, and ADR 0032 already holds it apart from everything shareable. A number
in a heading is written, not computed.

## An unfilled placeholder is a load error

A Signature tolerates an Arg the Instance never gave — it prints the placeholder
back, and elides the `[...]` group around it, so an optional variable reads as
absent. Prose has no such grammar. Square brackets in prose are square brackets,
and "May be load up to {N} shots" is a sentence the reader cannot use.

So naming a Variant whose prose has a placeholder no Arg fills is a load error,
reported beside the existing check that a named Variant exists (ADR 0032) — the
same reason: prose the reader would otherwise silently lose.

**This makes `optional` and "must be filled" orthogonal**, and that is the
subtlest consequence here. `optional` is a claim about the *variable* — the
Signature may elide its group. Being filled is a claim about *the prose that
names it*. `fire_order.N` stays optional because two of its Variants name no `N`
at all; the Variant that does name it still requires one. A reader who deletes
`optional = true` to "enforce" the requirement breaks the other two Variants and
does not enforce anything.

## Each slot sees the Args in scope where it is written

A **Case** renders with its own Args merged over the Instance's. A `preamble`
scopes *every* Case, so it can see none of their Args:

| slot | Args |
|---|---|
| prose-shaped `text` | the Instance's |
| `preamble` | the Instance's |
| a Case's `text` | the Instance's, then the Case's over them |

A `preamble` naming a placeholder only the Cases supply is a load error, and the
error says so in those words — the author's instinct will be that the value is
right there in the file below.

## One interpolation, shared verbatim

Prose is filled by *the same* function as a Signature, with the same semantics:
a ref-valued Arg renders the target's name followed by the target's own
Signature, and `{version.id}` asks for the raw id.

**Rejected: a reduced substitution for prose** — scalars only, refs to a bare
name, no nested Signature. It was the first proposal and the corpus refuted it.
Group elision is unreachable, because an unfilled placeholder is an error before
rendering. `damage_type` has six records and no Signature, so `{version}`
renders "Fire" under either rule; only `to_hit`'s `{ability}` could differ, and
"Camouflage[swamp]" is arguably the sentence you want. The reduced form bought a
divergence nobody had hit and paid a second code path, a second paragraph here,
and a second meaning for braces — the exact trap the table above exists to close.

The gap it leaves is *a name without the nested Signature*, which has no
spelling. It stays unbuilt until a rule wants it; inventing a third spelling now
would be inventing the problem.

## Consequence: interpolation is not a rendering concern

Three modules now ask questions about one grammar — `registry` checks a
placeholder is fillable, `render` fills it, `lint` asks whether two prose strings
agree once filled. The interpolation and its placeholder pattern therefore live
in a module of their own, which all three import, rather than staying private to
`render` and inverting the dependency that already runs `render` → `registry`.

The lint consequence is the reason `lint` is on that list. `check_longhand` is
exact string equality, so a Variant reading `"...up to {N} shots"` can never
match an Instance that typed `"...up to 5 shots"` — and that Instance's author is
precisely the person who did not know the Variant existed. The pool is
interpolated with the Instance's Args before the comparison, which keeps
`check_longhand` the two-string predicate it is and leaves the near-miss
judgment where ADR 0032 put it: with the maintainer.
