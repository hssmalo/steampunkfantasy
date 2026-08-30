# The Rules Reference promotes see_also by namespace

A **Rules Reference** lists the rule Records an Army's Specials reach. Which
records those are is a graph walk over the two edge kinds
[ADR-0024](0024-specials-are-identified-instances-over-a-registry.md) gave a
record — `places` and `see_also` — and the two are walked differently:

- **`places` is followed unbounded**, with a visited-set, from *every* entry —
  promoted ones included. A rule's mechanical consequence is part of the rule:
  a Special that places a Poison token is not explained without the token, and
  neither is an Acid token that sets the unit on fire.
- **`see_also` is followed exactly one hop, and only from the core** — the
  rules the Army's own Specials reach. It is an editorial pointer, never
  load-bearing, so following it transitively wanders off into the corpus.
  Keeping it off the promoted records is what bounds the walk.
- **A one-hop `see_also` target is promoted to a full entry when it lands in
  `token`, `hex` or `damage_type`**, and is a cross-reference line either way:
  a target that is an entry keeps its line, linked, because a Stub whose
  `see_also` is the only thing explaining it would otherwise print a heading
  and nothing else.

Cycles are legal and exist — `assault_poison` and `range_poison` point at each
other — which is why the walk carries a visited-set rather than a depth bound.

## Why promote a token but not a special

A token or a hex is a **physical thing on the table** a player has to resolve
mid-game. Another Special is editorial cross-reference: the reader is being told
where to read more, not what to do now.

Without the promotion the issue's own headline case fails. `hex.fog` and
`token.terror` reach the abomination *only* by `see_also`, so its Rules
Reference would name Fog and Terror on the Unit lines and print no rule text for
either.

## Promotion is by namespace, not by fixing the data first

`special.fog → hex.fog` and `special.terror → token.terror` are mechanical
`places` relationships authored as `see_also`. Recoding them is real work and is
tracked separately.

It is not a prerequisite, because there are **17 `places` edges in the whole
repo against 128 `see_also` edges**: waiting on that authoring would block the
Rules Reference indefinitely. And the two render identically — once an edge is
recoded from `see_also` to `places`, the target arrives through the unbounded
`places` walk instead of the promotion, as the same full entry. Nothing here has
to change when that lands.

## The measurements

Entry counts per showcase Army, for the walk as chosen and for the two
alternatives:

| Army | seeds | `places` only | chosen | every 1-hop `see_also` | `see_also` unbounded |
| --- | --- | --- | --- | --- | --- |
| abomination | 27 | 29 | 36 | 45 | 50 |
| darkelf_dragon_flight | 18 | 19 | 25 | 32 | 39 |
| darkelf_mechahydra | 23 | 25 | 33 | 44 | 48 |
| darkelf_spider_swarm | 16 | 18 | 20 | 33 | 45 |
| dwarf | 19 | 21 | 29 | 35 | 39 |
| elf | 17 | 18 | 20 | 29 | 42 |
| gnome_air_wing | 22 | 23 | 31 | 39 | 48 |
| gnome_ballista_battery | 14 | 15 | 16 | 21 | 37 |
| goblin | 22 | 23 | 30 | 39 | 45 |
| ogre_hydra | 23 | 26 | 32 | 40 | 45 |
| ork_warband | 13 | 14 | 20 | 27 | 33 |

`places` adds 0–3 records over the seeds; that is the whole cost of following it
without a bound.

## Rejected: promote every depth-1 `see_also`

Costs dwarf 29 → 35 and spider swarm 20 → 33. What it hands dwarf is
`special.burst`, `special.heal`, `special.range_gear_disruption`,
`special.assault_gear_disruption`, `special.cunning_assault_defense` and
`ability.superb_shot` — rules the Army does not field, printed in full beside
the ones it does.

## Rejected: fix the data first, promote nothing

Correct in principle, and still tracked as its own work. Rejected as a
*prerequisite* only, for the 17-edge reason above.

## Rejected: follow `see_also` unbounded

Costs dwarf 29 → 39 and gnome_ballista_battery 16 → 37 — more than doubling the
smallest Army's list. Editorial pointers chain, so one hop from a rule the Army
fields lands on `ability.superb_shot`, and the next reaches `token.bleed`,
`token.crippled_crew` and `special.limited_ammo`.

## Consequence: one entry per Record, not per Instance

Instances of one Identifier disagree — abomination fields Terror at d6, d8 *and*
d12 — so an entry prints the Record's **general** text with its `{N}`
placeholders intact. The filled signature already prints on the Unit line, so
the concrete numbers live with the Unit and the general rule lives in the Rules
Reference. That also matches the Rulebook's own rendering, so a player reads the
same words in both documents.
