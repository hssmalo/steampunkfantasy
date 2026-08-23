# PROTOTYPE — the shape of a Special instance in a race file

Throwaway. Answers wayfinder ticket
[#112](https://github.com/hssmalo/steampunkfantasy/issues/112), under map
[#111](https://github.com/hssmalo/steampunkfantasy/issues/111). Delete once the
ADR lands.

```
python3 prototypes/special-instance-shape/render.py
```

## What was built

Three candidate TOML shapes over the **same** real excerpts, and a renderer that
resolves all three to one normalised instance model.

| | shape | keying |
|---|---|---|
| A | array of tables | `[[units.x.specials]]`, `id` is a field |
| B | local instance handle | `[units.x.specials.<handle>]`, `id` is a field |
| C | id-keyed arrays | `[[units.x.specials.<id>]]`, the **key** is the id |

C was not in the ticket — it suggested itself while building A and B.

Excerpts cover every hard case the ticket names: repeats within one source
(`elf` `armored_unicorn_rider` Officer ×2), intended replace (`dwarf`
`stabilizer` over a model's `To Hit`), structured args (`Terror`, `Repair`),
free text alongside args (`abomination` `flagship`'s conditional Terror), an
atmospheric name (`Excellent Whip Handling`), and a version ref (`Resistance`
poison/fire/acid).

## Result

All three resolve to the **same 13 instances**. They are equally expressive, so
the choice is ergonomics, not capability.

Source cost for those 13 instances: **A 51 lines, B 51 lines, C 38 lines**.

## Readings

**B loses on `replace`, decisively.** A handle is local by construction, but
every real replace is *cross-source*: `equipment.stabilizer` overwrites a `To
Hit` on a model defined in a different table, often a different file. For
`replace = "<handle>"` to resolve, handles must be globally addressable and
stable — which is the `(2)`/` 2` suffix problem respelled, and adds a **third**
linted namespace (ids, handles, display names) on top of the two the map is
already trying to reduce to one. The ticket suspected this; the prototype
confirms it at the point where you try to write the stabilizer line.

**A is uniform and dull, which is its virtue** — but it puts `id = "..."` on
every instance and abandons the one-line-per-special reading that
`races/*.toml` has today. It is the only shape that guarantees a **total order
over all instances in a slot**, since a TOML array is ordered and a table is
not.

**C keeps the id as the key**, so there is no invented handle and no third
namespace; `replace = true` needs no target because the key *is* the target.
Repeats are native (`officer` twice, `resistance` three times), so the `(2)`
suffix disappears without being replaced by anything. It reads closest to
today's files and costs 25% fewer lines.

**C's cost**: a `[[...]]` header for every singleton special (the common case),
and instances of *different* ids are only ordered within their own id — a table
is semantically unordered. That matters only if the Army Reference wants to
print specials in authored order rather than a canonical one; #73's rendering
should confirm it does not.

## Recommendation

**Shape C**, on the strength of the replace argument and the single namespace.

## Deliberately not decided here

Args are nested under `args.*` in all three shapes so that the comparison
varies one thing only. Whether they should instead be **flat** on the instance
is a separate question — flat is terser but collides with the envelope keys,
since `name`, `text` and `version` are all plausible variable names. That
belongs to #113/#114.
