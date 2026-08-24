# Migrating to the Special data model

The decision is [ADR-0024](adr/0024-specials-are-identified-instances-over-a-registry.md).
This file is the plan for carrying it out. **It has been executed**; what
follows is the plan as written, kept as the record of what was intended. Where
execution diverged, the commit that diverged says why, and ADR-0024 carries an
amendment to its completeness rule.

The identifier census this plan works from is
[`docs/specials-census.md`](specials-census.md): 97 labels, each with a chosen
identifier, plus the open judgment calls collected in "The sweep" below.

## Shape of the work

Six phases, in dependency order. Phases 1 and 2 are independent of each other and
can run in parallel; everything after phase 3 depends on the race files having
been converted.

The one hard sequencing constraint worth stating up front: **the four `Literal`
lists cannot be deleted until the hard gate exists** (phase 2), because until
then nothing checks that a Special id is real. Deleting them earlier means a
window where a typo in a race file resolves to nothing and prints nothing.

## Phase 0 — preconditions

**0.1 American English locale — done.** `typos.toml` gained `locale = "en-us"`
with `axe` allowlisted, and the repo-wide fallout is fixed (`13ec630`). This had
to precede any `just spell-fix` run, because unguarded it rewrites `axe` → `ax`
through the race data. No later phase needs to carry it.

**0.2 Rules-name drift.** Must land before `spf rules lint` can enter `just
check` green (phase 5), and is cheap enough to do first:

```text
Evation                  → evasion
Ellusive                 → elusive
cunning_assault_defence  → cunning_assault_defense  # typos: ignore
```

The third is the one British-spelled id; the label side spells it `Defense`
already, so this rename closes the gap rather than opening one.

`Hyptnotizing_Gaze` and `Stacing_Limit` need no rename — they are dead keys in
`reference.toml`, which phase 1 deletes. The action is not carrying them
forward.

**0.3 The collision worklist.** A throwaway script listing every case where one
unit receives the same model-granted unit Special from several model slots. This
produces the phase 3 worklist for the seven known units and catches any that have
appeared since. It is a migration artifact, not a permanent facility — do not
add it to `just check`.

## Phase 1 — the registries (`rules/`, no race changes)

Nothing in this phase touches `races/*.toml`, so it can land and be reviewed on
its own.

**1.1 `rules/namespaces.toml`** — new. The namespace registry (name, file, table,
optional `group`), in the declaration order the to-hit table should render in,
plus the `damage_type` registry itself (`regular`, `psychic`, `fire`, `poison`,
`acid` — note `acid` is the one `special.toml`'s hand-maintained list omits).

**1.2 `src/spf/schemas/rules.py`** — the shared record base: `name`, `effect`,
`signature`, `variables`, `flavor`, `example`, `todo`, `see_also`, `places`, one
`@model_validator(mode="after")` for exactly-one-of completeness, and a
`ClassVar` tuple per subclass naming its meaning-bearing fields. Then a thin
subclass per registry with its registry-specific fields. Also here: the `Ref`
type, the `die` type, and union-typed variables.

**1.3 `rules/special.toml`** — flatten to `[special.<id>]`, drop the
`[unit]`/`[model]`/`[assault]`/`[range_]` sectioning, add `slots` to every
record. Rename `short` → `signature`, `explanation` → `effect`, `description` →
`flavor`, `token` → `places`. Move parameters out of names into `signature`.
Split the four colliding ids into `assault_*` / `range_*` pairs.

**1.4 `rules/reference.toml`** — delete. Two pieces of residue must be **moved
verbatim, not summarized**, into the `todo` field of the rule each concerns: the
13 commented-out `potential_references`, and the Norwegian design notes addressed
to the game designer. The endurance-token prose in this file is the *only*
description of endurance tokens in the repo and is needed by 3.4 — rescue it
before deleting.

**1.5 `to_hit.toml` → `rules/modifiers.toml`.** Keeps `ability`, `distance`,
`angle`, `speed`, `size`. Inline `[token]` (4 records) out to `tokens.toml` as
`to_hit`/`to_be_hit` fields on the owning record — fixing the `plus_minus_1` /
`plus_minus_one` disagreement in the process. Rename `unit_ability` → `ability`;
rename the distance-band table → `distance`. Promote `speed` and `size` out of
`type_aliases.py` into registries that own their vocabulary (`crawl` /
`crawling`; `Size` has six values against the table's three).

**1.6 `rules/terrain.toml`** — new registry, its to-hit numbers inlined as
fields. Id set: the seven existing plus `swamp` (used by `darkelf.toml`, with no
record today), with `hide`'s `ruin` canonicalized to `ruins`. Eight new `todo`
stubs, and they are the countdown working as intended, not noise. `terrain.fog`
does **not** come here — fog is hex-owned.

**1.7 `tokens.toml` / `hexes.toml`** — adopt the common core; drop `phases` from
`HexRuleConfig` (0 of 4 hex records use it); add the `endurance` token needed by
3.4. Populate `places` and `see_also`: until these are structural, reference
traversal dies at depth 1, so this is not a later nicety.

**1.8 `src/spf/rules.py`** — `get_to_hit` → `get_modifiers`, plus loaders for the
new files. `parse_to_hit` takes `RulesContext` (its `# noqa: ARG001` goes) but
does **not** wait on ref resolution: refs appear only in effect prose, so the
name / `to_hit` / `to_be_hit` columns render without a resolver.

## Phase 2 — the instance model and the hard gate (code, no data changes yet)

**2.1 The instance schema** — envelope closed at `name` / `text` / `replace` /
`args`, on `StrictModel` so the closure is free. Specials become
`dict[str, list[Instance]]` rather than `dict[Literal, str]`.

**2.2 The resolver and the hard gate.** Eight checks, all at load time, all
already run over the whole corpus by `just validate`:

1. every id resolves to a rule record
2. every id is used in a slot the rule declares
3. every ref resolves and lands in its permitted value set
4. args validate against the union of the rule's variables and every ref
   target's — this is where `N ∈ {4,6,8,10,12}` and the `die` union get checked
   for the first time
5. a rule variable colliding with a ref target's variable is an error
6. cross-slot `replace` is rejected
7. record completeness (from 1.2)
8. envelope closure and the stat-modifier fence — free from `StrictModel`

**2.3 Merge.** Replace `dict |=` in `armies/model.py` (three sites) and
`armies/unit.py` with set-accumulation plus reset-on-`replace`, along the
existing chain: unit config → each model's `unit_special`; model config → each
equipment in order.

**2.4 Stat modifiers.** New `[equipment.<x>.unit]` block and
`EquipmentUnitConfig` with `armor` on the full `Stacker`. Model-declared
unit-stat modifiers, alongside the existing `unit_special`. Multiplicity: model
declarations ×N slots; equipment follows `upgrade_all` (`true` → ×1, `false` →
×N); only `add` multiplies.

## Phase 3 — the race files

Eight files, script-assisted, in one change. The mechanical bulk is a
label-to-instance rewrite driven by the census; what follows is everything the
script cannot decide.

**3.1 The seven `replace = true` units.** `goblin_infantry` (4× Pre-Assault
Retreat), `gnome.assault_bots` (4× Setup), `elf.pachycephalosaurus_riders` (3×),
`elf.pegasus_rider` (2×), `ogre.drone_swarm`, `ogre.repair_drone`,
`ogre.medic_drone` (4× each). Without this the Army Reference gains visible
duplicate lines in seven units — the one regression this migration causes rather
than fixes. Use 0.3's list, not this one, in case the data has drifted.

**3.2 Suffix removal.** Every `(2)` / `(3)` / ` 2` suffix disappears; repeats are
native to the new shape. This includes the `Resistance 2` / `Resistance 3` and
`Officer 2` families.

**3.3 Multi-value labels split into several instances.** `"Resistance" =
"Poison[12], Fire[3], Acid[1]"` is three instances, not one. `"Immunity" = "Acid
and Gear Disruption"` is two, across two namespaces.

**3.4 `Protection` splits.** Armor grants become `armor.add` stat modifiers;
endurance grants become `endurance` Special instances. Dwarf's `Protection 2` is
both in one string and becomes one of each. Needs the `endurance` rule stub and
`tokens.toml` entry from 1.7, seeded with the prose rescued in 1.4.

**3.5 Two slot moves.** `Fear` moves unit → assault. `Pre-Assault Retreat` moves
assault → unit (the rule file's own TODO already said so).

**3.6 `Note` rows.** All 13 become `note` siblings of `specials` on the
containing record. Two of the 13 are not notes and should not migrate as such:
gnome's `helicopter_mounted_experimental_plasma_gun` ("Get -1 to hit in forward
direction") is a to-hit modifier, and the four "No regular damage" rows
(`acid_splash`, `assault_bot_mortar` ×2, `assault_bot_dropper`) are damage-type
statements now expressible against the `damage_type` namespace.

**3.7 One prose-only `Immunity` row.** Darkelf's *"If the officer is the only
alive model, this unit becomes immune to poisons and poison clouds"* has no
feature argument at all. It becomes `args.feature = "hex.poison_cloud"` plus free
`text`. `immunity.feature` stays a **required** variable — this row is a data
fix, not a reason to make refs optional.

**3.8 `Fire` and `Acid` as immunity targets are ambiguous** — `token.fire` or
`damage_type.fire`? Qualification makes the authored answer explicit, but
somebody must choose, per row.

**3.9 Terrain args become refs**, which is what makes `swamp` representable.

**3.10 Changelog.** `races/changelog.md` and `rules/changelog.md` record
*deliberate* game-data changes and the reasoning behind them. A vocabulary
rename of this size is not gameplay-identity change per row, but the slot moves
(3.5), the `Protection` split (3.4) and the four id renames (1.3) are — a player
who fielded a unit needs to know where a rule went. One entry per genuine change
of intent, not one per rewritten line.

## Phase 4 — consumers of the old shape

**4.1 `frontends/cli/special.py` — a real rewrite, not a mechanical edit.** The
four `frozenset`s built via `get_args()` become a registry lookup; the four
`TypeIs` guards become the rule's `slots`; `_SPECIALS` (the "Did you mean…?"
corpus) becomes the registry key set. And because a slot now holds N instances,
`key in u.special` becomes iteration — `_unit_matches` yields N rows per holder
instead of one, which changes the UMAR display's shape, not just its plumbing.

**4.2 `render/army_rules.py`** — grouping N instances of an id under one heading.
This is the concatenation #108 asked for, and it belongs here rather than in the
data layer.

**4.3 `render/rulebook.py`** — `TO_HIT_TITLES` and its stale `"order": "Orders"`
entry are deleted. Group order comes from `namespaces.toml` declaration order,
titles from each namespace's `name`, membership from a query (every record in the
namespace carrying `to_hit`/`to_be_hit`; empty groups drop, which is already the
rule). `hex` declares `group = "terrain"` so fog renders among the terrains.

**4.4 `armies/io.py`** — the specials round-trip. Army JSON keeps its
`{name, upgrades, nick}` shape, so there is no army-file migration.

**4.5 Golden tests.** Expect churn in every rendered output: suffixes gone,
instances grouped, to-hit table regrouped, seven units' duplicate lines
collapsed by `replace` instead of by `dict |=`.

## Phase 5 — lint and the countdown

**5.1 Rename `src/spf/lint/rules.py`.** A module of name predicates and a
directory of game data now share the word, and `spf rules lint` puts both in
scope of one command. Do this before 5.2 rather than after.

**5.2 `spf rules lint` + `just lint-rules`**, placed after `lint-races`. Reuses
`check_key_name`, `check_no_underscore`, `check_title_case` and
`check_key_lowercase` directly — they are pure functions over `(key, name)` with
no schema dependency. A sibling command, not an extension of `spf race lint`, so
a broken `rules/*.toml` fails `validate` and is *skipped* by its own linter
(ADR-0016). Requires 0.2 to be green.

**5.3 `spf rules todos`** — outside `just check`, two sections: unwritten rule
text (`todo` is the sole marker; ~45 at the start, plus terrain's eight) and
unreachable rules. Both are countdowns, not gates.

**5.4 No warning tier.** If a check seems to want one, it belongs in 5.3 or
nowhere — the existing "lint speaks ⇒ build fails" contract stands.

## Phase 6 — delete the `Literal`s

Last, and only once phase 2's hard gate is live. `UnitSpecial`, `ModelSpecial`,
`AssaultSpecial`, `RangeSpecial` come out of `type_aliases.py`; `dict[t.UnitSpecial, str]`
keys in `schemas/race.py` and `armies/` become `str`. The `+N`/`-N` members of the
`Modifier` Literal also go, since those parameters now live in `variables` and
`signature`.

`speed` and `size` become registries in 1.5 rather than disappearing, but their
aliases leave `type_aliases.py` here: validating a Race's `size` against the
registry needs the gate, so 1.5 promotes the vocabulary and this phase deletes
the aliases.

## The sweep

Open judgment calls collected across the effort. None blocks the plan; all must
be decided by whoever executes it, and each is recorded in
[`docs/specials-census.md`](specials-census.md).

**Suspected duplicates** (name-closeness only, unconfirmed): Cunning Deflection
vs Cunning Assault Defense; Multiple Shots vs Burst; Improved Extra Damage vs the
Extra Damage family.

**Naming collisions with concepts this model formalizes:** the assault Specials
`Angle` and `Size` against the unrelated `angle` / `size` modifier registries;
the range Special `Order` against a future `orders` namespace. Fully qualified
refs already separate them, so this is a readability call rather than a
correctness one.

**Orphans:** `unit.hide` looks dead — is it? `unit.insanity_field` is unreachable
by exact label because Horror's `Terror` carries it in prose; the atmospheric
name is the natural home for that.

**Values needing a variable:** `enhanced_accuracy`'s to-hit bonus is fixed at +1
in the rule, but the data needs +1/+3/+5.

**Text-match traps:** "Great Shot: +2 to hit" matches `excellent_shot`'s value,
not `superb_shot`'s, despite what the word "Great" suggests.

**Composition:** `Regeneration` composes `Heal[...]` in every occurrence's prose
but has no rule of its own — formalize as a wrapper, or leave bespoke?

**Casing and spelling** across the to-hit values: 43 distinct free-text variants
were censused; pick one convention.

## Deliberately not in this plan

- **Writing the ~30 missing rule texts.** Game-design authorship. This migration
  produces `todo` stubs and a countdown; the designer fills them in.
- **#73's rendering and filtering** — the job this whole effort exists to make
  boring.
- **Order Cards and `rules/orders_items.md`.** Adding an `orders` namespace is
  one line in `namespaces.toml`; the *target* does not exist, because that file
  is free-form Markdown with no keyed ids. Converting it is its own effort.
  `Chase`, `Transport`, `Fire Order`, `Officer Order`, `Activate` and `Reload`
  all want to point there. (`Hidden` does not — it resolves cleanly to
  `token.hidden`.)
- **What fields a Terrain record declares** — [#128](https://github.com/hssmalo/steampunkfantasy/issues/128).
  Phase 1.6 creates `rules/terrain.toml` with the common core and inlined to-hit
  numbers; destructibility as a structured transition between ids,
  line-of-sight blocking and movement are that issue's.
- **Provenance in output** — whether a Special granted by Equipment is marked as
  such where it is printed.
