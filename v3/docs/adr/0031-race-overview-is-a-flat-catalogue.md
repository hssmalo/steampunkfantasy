# The Race Overview is a flat catalogue, not a nested one

The **Army Reference** nests: a Unit heading, its Models below, their ranged
Equipment below that. It can, because a fielded Army has already **chosen** a
path — this Unit fields those Models, each carrying that Equipment.

A Race has made no choices. Its records form an **N:M web**: a Model is fielded
in several Units, an Equipment is carried by several Models, and an upgrade
Model replaces another. The **Race Overview** therefore does not nest.

## Decision

**The Race Overview is four independent, flat sections — Units, Models,
Equipment, Spawns — followed by the Rules Reference. Every record appears
exactly once, addressed by a unique anchor, and the relationships between
records are carried by cross-links in both directions.**

Anchors are slugged from the **TOML key**, prefixed by section: `unit-`,
`model-`, `equipment-`, `spawn-`, plus `section-` for the section headings
themselves. The prefix is what resolves the one genuine collision — `dwarf`
uses `dwarf_infantry` as both a Unit key and a Model key — and it resolves it
by construction, rather than by a disambiguating counter that would shift every
link the moment a record is added. The five are disjoint from the Rules
Reference's `rule-` and `rule-alias-` namespaces, so one document holds both id
spaces without either needing a prefix.

## Why not nest

Nesting a web means printing a record once per path that reaches it.

| | worst-case copies of one Equipment | Models in no Unit roster | Equipment on no Model's list |
| --- | ---: | ---: | ---: |
| abomination | 4 | 1 | 9 |
| darkelf | 15 | 6 | 17 |
| dwarf | 6 | 6 | 24 |
| elf | 14 | 4 | 15 |
| gnome | 8 | 4 | 20 |
| goblin | 4 | 1 | 16 |
| ogre | 6 | 6 | 9 |
| ork | 16 | 2 | 20 |

The first column is the repetition: ork would print one Equipment sixteen times.
A reader comparing two weapons would be comparing two copies rather than two
entries, and a designer correcting one would have no single place to look.

The last two columns are worse, and they are what settles it. A nested document
can only print what its walk reaches, so a record on no Unit→Model→Equipment
path is not repeated — it is **absent**. Nearly every Upgrade Equipment in the
repository is in that position — 125 of 126 across the eight races — because
`ModelConfig.equipment` holds a Model's **Default Equipment**, and an Upgrade is
matched to a Model at build time instead, by `requires` against the Model's
Holder slots and Types (see `available_equipment` in `spf.armies.build`). A
nested Race Overview would omit the Upgrade catalogue almost entirely: exactly
the half of the data an army-builder is shopping through.

The same holds a level up for Models. `ogre.healing_drone` is in no Unit's
roster and replaces nothing — it is reachable from no path at all. A flat
catalogue prints it, and its empty cross-links make its isolation visible,
which is how a data question gets noticed rather than buried.

## Consequences

- **Cross-links replace nesting as the navigation.** They run both ways: a Unit
  names its Models and a Model names the Units that field it (`fielded_in`); a
  Model names its Equipment and an Equipment names its carriers
  (`carried_by`); `replaces` prints on both ends, as "upgrades from" and
  "upgraded by"; a Unit reachable only through a **Spawn** says so
  (`spawned_by`). Each inverse is built once from the already-ordered section it
  points into, so a back-link reads in the same order as the section it lands
  in.

- **`carried_by` covers Default Equipment only, so every Upgrade's is empty.**
  That follows directly from the paragraph above: the Default relation is the
  only one written down as a list, and the Upgrade relation is a constraint
  evaluated against a Model's Holder slots. The document still carries both
  halves of what answers the question — each Equipment prints its requirements,
  each Model prints its Holder slots — but the reader intersects them by hand.
  Deriving the Upgrade cross-links from `requires` is the obvious next step and
  is not done here.

- **Nothing is resolved, because nothing is fielded.** A **Stat Modifier**
  prints as the delta it was declared as: a Model's `+3/+2/0/0` armor grant has
  no value until a specific Unit is fielded under it, so a resolved catalogue
  would have to invent one. This is the same fact that retires `Race.resolve()`
  — see the Race Overview addendum to
  [ADR-0005](0005-rendering-pipeline.md).

- **Orders stay unmerged.** A Unit prints its own movement and fire tables; an
  Equipment's `orders_gained` prints on the **Equipment**, labeled as granted.
  `orders_gained` is additive ([ADR-0007](0007-merged-orders-and-card-view-model.md)),
  and the Army's merged view exists only because a fielded Unit has a fixed
  loadout. Merging here would mean merging against every loadout a Unit could
  have.

- **Each section opens with a summary table** linking into its own detail
  entries. The flat shape is what makes this possible — a section is a complete
  list of something — and it is what a reader scanning for a price or a slot
  count actually uses. A summary column carries what tells its records apart,
  so it may print less than the detail entry does: the Models table drops the
  uncapped Independent slot all but a handful of Models offer, and prices a
  record in one cell where the Units table, which is where a list's budget
  goes, keeps a column per currency.

- **The Rules Reference is included and unchanged.** It is seeded from the
  Race's Slots rather than an Army's
  ([ADR-0029](0029-the-rules-reference-promotes-see-also-by-namespace.md) governs
  the walk either way), so a Race Overview explains every rule its catalogue
  names. `--no-rules` drops it and every link into it.

## Rejected: nest, and print a record once at its first occurrence

Keeps the familiar shape and prints nothing twice. Rejected because "first
occurrence" is an ordering artifact: an Equipment would be written out under
whichever Model happens to sort first and appear as a bare name everywhere
else, so the fullest entry moves whenever a Cost changes. It also does nothing
about the absent records, which are the larger problem.

## Rejected: one section per Unit, with its Models and Equipment inlined

This is the Army Reference's shape applied to a catalogue, and it is what the
measurements above cost. It is the right shape for an Army and the wrong one
for a Race; that difference is the whole of this decision.
