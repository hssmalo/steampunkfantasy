# Specials are identified instances over a registry of rules

A Special is written in a Race file as an **instance**: an occurrence of a rule,
keyed by the rule's **identifier**, carrying typed arguments and optional local
prose. The rule itself lives once, in a **registry** in `rules/`, which owns the
identifier and the display name. Race data never names a rule by its display
name again.

This reverses `CONTEXT.md`'s previous statement that a Special is *"defined in
`rules/special.toml` and referenced by name"*. Referencing by name is what broke:
of 96 labels in the eight Race files, **11** matched a rule name exactly, and 15
rules were reachable from no label at all (#101). The two vocabularies drifted
because nothing checked that they agreed, and nothing could — a display name is
prose, and prose is edited.

**Why one vocabulary rather than a mapping table:** a label→rule mapping keeps
both vocabularies and adds a third artifact to maintain between them. Every
mapping file this repo has tried has rotted: `rules/reference.toml` points at
`special.assault.ork_reroll` when the key is `assault.reroll`, and carries the
ids `Evation`, `Ellusive`, `Hyptnotizing_Gaze` and `Stacing_Limit`. The
identifier *is* the mapping, and it is checked at load time because it is the
lookup key rather than a claim about one.

The decisions below were reached over nine tickets on the wayfinding map (#111);
each section cites the ticket that holds the argument and the options that lost.

## The four `Literal` lists are deleted

`UnitSpecial`, `ModelSpecial`, `AssaultSpecial` and `RangeSpecial` in
`src/spf/schemas/type_aliases.py` — four hand-maintained lists of display labels
— are removed. The rules TOML becomes the registry, and validation moves to load
time (#117).

**This is not a loss of checking; `just check` catches strictly more.** The
`Literal`s validated one thing: that a label was spelled like a label somebody
had already written. They never checked arguments, references, slots, or
completeness, because none of those were expressible. Their replacement — the
hard gate below — checks all four.

**The cost to the game designer is zero.** Specials are authored in TOML, where
pyright was never in the loop. The `Literal`s gave the only person who edits this
data no autocomplete and no error.

**The cost in Python is real and named.** `dict[t.UnitSpecial, str]` keys in
`schemas/race.py` and `armies/` become `str`. More sharply,
`frontends/cli/special.py` builds four `frozenset`s via `get_args()` and four
`TypeIs` guards over them, and those guards drive the entire UMAR display of
`spf special show` — deleting the aliases breaks that command, not merely its
typing. Its replacement is the rule's `slots` field, and `_SPECIALS` (the "Did
you mean…?" corpus) becomes the registry's key set.

**Rejected: generating the `Literal`s from the rules TOML as a build step.** It
reintroduces exactly the drift this decision removes, plus a generated file to
forget to regenerate. **Rejected: keeping the lists and asserting in a test that
they match the registry** — same maintenance, different error message.

## The rule record is flat, keyed by identifier, and declares its slots

`rules/special.toml` becomes one flat table namespace, `[special.<id>]`, with no
`[unit]` / `[model]` / `[assault]` / `[range_]` sectioning. Where a rule is legal
is a field, `slots`, a subset of `unit` / `model` / `assault` / `range` (#113).

**Why:** the sectioning made `Bonus` three unrelated rules that happen to share a
name, and made *(slot, label)* the only sound lookup key. `Bonus`, `Extra
Damage`, `Fog`, `LoS` and `Spawn` genuinely appear in more than one slot; they
are one rule each, declaring where they apply. Rendering derives its groups from
`slots` rather than from the file layout.

**Consequence: four ids must be renamed.** A flat namespace collides on `fire`,
`gear_disruption`, `minor_acid` and `poison`, each present today in both
`[assault]` and `[range_]`. These are **not** one rule in two slots: the assault
forms count hits ("one token per {N} hits") and the range forms are flat ("target
gets a token"), with different variables and different bounds. They are different
rules and get different ids — `assault_poison` / `range_poison`, and likewise for
the other three. Three of the four already carry the distinction in their display
name.

**Rejected: unifying each pair under `slots = ["assault", "range"]`.** It needs
per-slot explanations and per-slot variables, which reintroduces the sectioning
one level further in.

`rules/reference.toml` is **deleted**. Its `references` lists are superseded by
`places` and `see_also` (below), and it had already rotted as described above.
Its two pieces of genuine residue — 13 commented-out `potential_references` and a
set of Norwegian design notes addressed to the game designer — move into the
`todo` field of the rules they concern, **verbatim, not summarized**.

## The rules TOMLs hold registries, and overlays are inlined

A **registry** owns a vocabulary: its id set *is* the legal value set for its
namespace, it is the single definition site for each record's name and text, and
deleting it destroys a concept. An **overlay** looks identical — id → record —
but its keys are references into a registry that already owns them; it adds
fields that matter in one context and cannot introduce an id (#125).

`to_hit.toml` mixed both, and the mixture drifted exactly as unchecked
hand-copied keys do: its `[token]` table is 4/4 overlay and already disagrees
with `tokens.toml` (`plus_minus_1` against `plus_minus_one`), and `[speed]` and
`[size]` overlay vocabularies owned by `type_aliases.py` (`crawl` against
`crawling`; `Size` has six values, the table three).

**Overlays are inlined, not modeled.** `to_hit` and `to_be_hit` become ordinary
optional fields on whichever record owns the id. No third structural kind is
introduced, and the drift class becomes **unrepresentable** rather than merely
detectable.

**Rejected: keeping one central to-hit file because a designer wants the balance
surface whole.** That view is already *rendered* — `spf rules to_hit` and the
Rulebook section both emit the combined table — so it is a rendering need,
already met, and it does not constrain the source layout.

The resulting layout:

| file | registries |
|---|---|
| `rules/special.toml` | `special` |
| `rules/tokens.toml` | `token` |
| `rules/hexes.toml` | `hex` |
| `rules/terrain.toml` *(new)* | `terrain` |
| `rules/modifiers.toml` *(was `to_hit.toml`)* | `ability`, `distance`, `angle`, `speed`, `size` |
| `rules/namespaces.toml` *(new)* | the namespace registry, and `damage_type` |

Two renames inside `modifiers.toml`: `unit_ability` → **`ability`** (`unit_`
adds nothing once the name is namespaced), and the distance bands →
**`distance`**, not `range`, so that `range` stays unambiguously the Special
slot. `speed` and `size` are **promoted out of `type_aliases.py`** into
registries that own their vocabulary, which fixes both mismatches above by
construction rather than by someone noticing.

**Terrain gets its own file** (#126). Its seven records carry only to-hit numbers
today, with no prose anywhere, but it is a board concept with real rules written
down nowhere — buildings destroyed into ruins, forest replaced by rough terrain,
Hide and Camouflage gated on terrain — and its vocabulary is *incomplete*, not
merely rotted: `darkelf.toml` uses `Camouflage = "[swamp][-1]"` and no
`terrain.swamp` record exists. Making it a registry makes that unrepresentable,
at the price of eight new `todo` stubs. That price is the countdown working as
intended. **Rejected: one `rules/board.toml` holding Terrain and Hex Effects
together** — the transience line is sharp enough to be a file boundary, and
ADR-0018 binds one source file per Rulebook Section.

**Fog is one object, owned by `hexes.toml`**: a placed Hex Effect that behaves
like Terrain for to-hit purposes. `reference.toml` had already resolved this —
both `UnitSpecial.Fog` and `ModelSpecial.Fog` declared `references =
["hexes.fog"]`, never `terrain.fog`.

### The common record core

Every registry record carries: **`name`** (required), **`effect`**,
**`signature`**, **`variables`**, **`flavor`**, **`example`**, **`todo`**,
**`see_also`**, **`places`**.

The prose field is **one word, `effect`**. `special.toml`'s `explanation` and
`to_hit.toml`'s `note` both fold into it — on a modifier record, `note` states
*when* the modifier applies ("range = 1", "when unit is in the given speed"),
which is what the record does. `short` becomes `signature` everywhere.

Registry-specific fields: `phases` + `remove` (token), `remove` (hex), `slots`
(special only), `to_hit` / `to_be_hit` (the five modifier registries plus
`terrain`, `token` and `hex`). `remove` stays registry-specific: the general
concept is duration/lifecycle, and two registries are not enough cases to design
it.

**Record shapes stay hand-written pydantic** — a shared base plus a thin subclass
per registry. Namespaces are data-driven (below); record *shapes* are not,
because deleting the `Literal`s already moves all vocabulary validation to
runtime, and moving the schemas too would relocate essentially every static check
in one step. Schema checking is what makes the data safe to write.

### Completeness: at-least-one-of

A record is complete, or an explicit stub, or complete with an open question —
never nothing. Stubs are marked by the **presence of `todo`** together with the
absence of a meaning field, never by the absence of prose alone (#113), and
`todo` carries *what* is missing, so it is a place for design intent rather than
a flag.

> **Amended during the migration.** This section originally read
> *exactly*-one-of: a record was complete or a stub, never both. Carrying the
> migration out showed that rules out the case that turned out to matter most —
> a **written** rule with an open design question against it. `enhanced_accuracy`
> is fully written and its bonus is fixed at +1 while the Race data grants +1,
> +3 and +5; `cunning_assault_defense` may be `cunning_deflection` under another
> name; `hide` and `insanity_field` are written and reachable from no label.
> Under exactly-one-of these can only be TOML comments, which the countdown
> cannot see — so the one mechanism for making design debt *countable* was
> unavailable to exactly the rules whose debt is easiest to forget, because they
> look finished. The cost is that `todo` alone no longer means "stub", so the
> countdown distinguishes the two: unwritten rule text is records with no
> meaning field, open questions are records with both.

The constraint is over **⟨the registry's meaning-bearing fields⟩** and
`todo`, *not* over `effect` and `todo`. `effect` is not the
meaning-bearer on every record: on a modifier record, `to_hit` / `to_be_hit` are.
Keyed on `effect`, the rule would manufacture **28 stubs** for modifier records
nobody considers unfinished, inflating the ~45 real stubs to ~73 and destroying
the countdown it exists to protect — `[distance.long] to_hit = "-2"` is not an
unwritten rule.

**Rejected: requiring `effect` everywhere and writing the 28.** Prose written to
satisfy a validator restates the numbers and is trusted by no one.

Mechanically this is `todo: str | None` plus one shared
`@model_validator(mode="after")` on the base rejecting only the empty record, and a `ClassVar` tuple per subclass
naming its meaning fields — `("effect",)` for `special` / `token` / `hex`,
`("to_hit", "to_be_hit")` for the modifier registries. One line per registry,
beside that registry's own fields.

## The instance: id-keyed arrays of tables

In a Race file, a Special is written as an array of tables keyed by the rule's
identifier (#112):

```toml
[[units.armored_unicorn_rider.specials.resistance]]
args.version = "damage_type.poison"
args.N = 12
```

The envelope is **closed** at four keys: `name` (optional atmospheric display
name), `text` (optional free prose), `replace` (bool, default `false`), and
`args.*`. The id is the table key, not a field.

Three shapes were prototyped over the same real excerpts, all resolving to the
same 13 instances, so the choice was ergonomic rather than one of expressiveness
(branch `prototype/special-instance-shape`).

**Why the key rather than an `id` field** (shape A, array of tables with `id =`):
A is uniform and dull, which is a real virtue, and it was the only shape with a
guaranteed total order over all instances in a slot. But it puts `id = "..."` on
every instance and abandons the one-line-per-special reading `races/*.toml` has
today — a readability cost paid on every line of eight Race files, to buy an
ordering guarantee that is not needed. Checked against the code: `armies/io.py`
and `render/army_rules.py` iterate `.items()` and nothing sorts, `tomllib`
preserves document order, so authored order is what prints under either shape.

**Why not a local instance handle** (shape B, `[units.x.specials.<handle>]`): it
loses on `replace`, decisively. A handle is local by construction, but every real
replace is *cross-source* — `equipment.stabilizer` overwrites a `To Hit` on a
model defined in another table, usually another file. For `replace = "<handle>"`
to resolve, handles would have to be globally addressable and stable: the
`(2)` / ` 2` suffix problem respelled, plus a **third** linted namespace on top
of the two this model reduces to one.

The chosen shape makes repeats **native** — `officer` twice, `resistance` three
times — so the `(2)` / `(3)` / ` 2` suffixes that exist purely to force stacking
disappear without being replaced by anything. It also costs 25% less file: 38
non-comment lines against 51 for both alternatives, for the same instances.

### Args are nested under `args.*`

Flat args are terser and match the names `signature` interpolates, so this was a
real trade (#119). It lost on **who controls the arg namespace**.

An instance's validated arg set is the union of the rule's declared variables
*and* the variables of every resolved ref target (below). So the set of names
that can legally appear on an instance is not fixed by the rule the instance
names — it grows whenever anyone adds a variable to any registry record in any
file. Under flat args, `name` / `text` / `replace` would not be three words
reserved once; they would be a permanent constraint on a vocabulary edited from
elsewhere, and a violation would surface as a silently-shadowed envelope key in a
Race file whose author never touched the declaration.

Nesting makes that whole class of collision **unrepresentable** rather than
linted. Measured cost across the eight Race files: 768 instances, 404 carrying at
least one arg, ~563 arg tokens — a five-character prefix on ~53% of instance
lines and **zero** extra lines. A width cost, not a size cost.

**Rejected: a sigil-marked envelope** (`_name`, `_text`, `_replace`) — it buys
terseness and permanent separation, at the price of a sigil convention appearing
nowhere else in this repo's TOML. **Rejected: a single-arg shorthand**
(`args = 6` against a rule's sole declared variable, which would cover 285 of the
404 arg-carrying instances) — under the union rule a rule's arg set can grow from
*another file*, so a shorthand valid today can be invalidated by an edit nobody
made to that Race file. It also quietly reintroduces positional arguments.

### `note` is not part of the Special vocabulary

`Note` is retired as a Special id. It becomes a **sibling of `specials` on the
containing record** — `units.horror.note`, `equipment.assault_bot_mortar.range.note`
— not a fifth envelope key.

All 13 `Note` entries in `races/*.toml` sit in a specials table as siblings of
real Specials, never attached to one; the abomination row is about *two* Specials
at once, so there is no instance that could host it. The envelope already has
`text` for per-instance prose, so a per-instance `note` would be a second prose
field with no rule for choosing between them.

## References are typed, namespace-qualified, and structural

A **ref** is written `<namespace>.<id>`, always fully qualified, lowercase, the
namespace singular and a single segment: `token.poison`, `hex.poison_cloud`,
`special.range_poison`, `ability.good_shot`, `terrain.forest`,
`damage_type.psychic` (#114).

It is **one value type with one syntax**, used identically wherever a reference
appears: as an argument on an instance, as an entry in a record's `places` or
`see_also`, and as the target of a version overlay. One `Ref`, one resolver, one
check.

And it is **not special-only**. Every mechanism here — `variables`, refs,
`signature`, `places` / `see_also`, the version overlay — is shared machinery
available to every registry record. `hexes.toml` already carries a `variables`
table on `poison_cloud`, so this generalizes what the data was reaching for.

### The namespace is an abstract name, declared once

Namespaces are declared in `rules/namespaces.toml`, which maps each to its
location. The namespace is **not** a path into the file layout.

**Why:** the dotted path form (`to_hit.unit_ability.good_shot`) is
self-documenting and open for free, but it makes a rules file's internal table
layout load-bearing in eight Race files — renaming a table would rewrite the army
data. The registry decouples them, keeps every ref two segments long, and makes
adding an `orders` namespace later a **one-line** change.

### The namespace is the value set

A ref variable declares which namespace(s) it draws from, and every member of
those namespaces is legal. An explicit `values = [...]` subset is available,
mirroring `int`'s, but it is the exception — because the hand-maintained list is
what rots. Evidence: `special.toml`'s `unit.resistance` declares
`values = ["regular", "psychic", "fire", "poison"]` and **omits `acid`**, which
has version prose four lines above it.

**Rejected: constraint-by-tag** (`token.poison` declaring
`tags = ["damage_type"]`, the variable asking for the tag). It earns its keep
only once subsets start crossing namespaces, which nothing currently requires.

### A ref may accept several namespaces

`immunity.feature` forces this: its real values span three namespaces — `Minor
Acid` / `Fire` / `Acid` are tokens, `Gear Disruption` is a **special**, and
`Poison Clouds` is a **hex**. Splitting `immunity` into `immunity_token` /
`immunity_hex` / `immunity_special` would fragment a rule the designer thinks of
as one thing. Because values are always qualified, a multi-namespace ref is
unambiguous and costs nothing at the point of use.

### `damage_type` is a new registry

Versions generalize into refs — but only *where a registry exists to point at*,
and creating that registry is part of the work. `resistance`'s five versions are
`regular`, `psychic`, `fire`, `poison`, `acid`, and `regular` and `psychic` exist
nowhere as ids. So `damage_type` is created as a genuine domain concept the game
already reasons about.

`fire` therefore exists in two namespaces — `token.fire` (the marker placed on
the table) and `damage_type.fire` (the category of harm). That is not a
collision; they are different concepts, and qualification keeps them distinct.

### Unions, and a `die` type

`resistance.N` is declared `type = "int"`, but the Race files author it as either
an integer **or a die**: `Regular[d4]`, `Regular[d8]`, and 24 occurrences of
`[d6]`. That is 26 die-valued arguments against a type system that knows only
`int` and `str`. A `die` type is added, and a variable may declare a union:
`type = ["int", "die"]`. One union mechanism, two uses — namespaces for refs,
types for scalars.

### Ref arguments travel with the ref

A ref's target may declare variables of its own. `Camouflage[terrain]`,
`Take Cover[speed][N]` and `Elusive[speed][N]` are exactly this. **The instance
supplies the union**: its args validate against the rule's declared variables
plus the variables of every resolved ref target, flattened into one table. A
collision between a rule variable and a target variable is an error — rename one.

This is what collapses ~20 hand-spelled "Good shot: +1 to hit" variants into one
id, and it resolves `Take Cover`, `Camouflage` and `Elusive`, which #101 counted
among the missing rules.

### The version overlay

`resistance`'s per-version prose ("Any die rolled by an acid or minor acid token
is reduced by {N}") belongs to *resistance*, not to `damage_type.acid`. So
`versions` survives, redefined: a **rule-local prose overlay keyed by ref value**
— a rule saying "when this ref resolves to *that*, here is my text for it". A
rule with no overlay inherits the target's own text.

### Signature interpolation, and the atmospheric name

`signature` is a template over the declared variables — `"[{N}, {M}+]"` — and
replaces the convention of encoding parameters inside a display name.
`name = "Take Cover[speed][N]"` becomes `name = "Take Cover"` with
`signature = "[{speed}][{N}]"`. A rule's `name` is **never parameterized**.

Signatures are not derived automatically: the real forms (`[{N}+]`,
`[1 for {N}]`, `[{N}, {M}+]`) are too irregular to generate.

A bare `{var}` on a ref-valued variable renders the **target's `name`** — the
lookup this whole model exists to establish. `{var.id}` yields the raw id.

An instance may carry an **atmospheric name**: a local display name that
overrides the *rule's* name in the heading — `id = "to_hit"`,
`name = "Excellent Whip Handling"`, `args.ability = "ability.excellent_shot"`
prints the flavor name while `{ability}` still resolves to "Excellent Shot". It
never overrides a ref target's name inside a signature. The *vocabulary* stays in
one place; what is *printed* may be local.

**Rejected: a mechanical/atmospheric flag on the rule.** The flavor name lives on
the instance, any instance may carry one, and a rule-level enum would be a
taxonomy argument with no consumer.

### Cross-references split by relationship, not by namespace

Two lists, distinguished by what the reference *means*:

- **`places`** — mechanical consequence: the rule *causes* this. Replaces
  `token = "minor_acid"`, generalized past tokens, so a rule may place a hex or a
  token.
- **`see_also`** — editorial pointer: related reading, never load-bearing.

A namespace does not tell you the relationship — a rule can *place* a fog hex or
merely *mention* one. Two relationship-keyed lists say that; one
namespace-grouped list cannot. Both are open to further relationships
(`removed_by`, `replaces`) without a schema redesign.

### Chaining is a graph, not an expansion policy

The model guarantees that every ref **resolves**, and exposes the resulting
reference graph. It defines **no** automatic expansion: traversal depth and cycle
handling are rendering's problem (#73), plausibly per relationship kind —
`places` expands a hop, `see_also` plausibly never does. Cycles will exist and
are legal: `special.assault_poison` and `special.range_poison` see-also each
other.

This is sound **only because every ref is structural** — a declared field or a
typed argument, never merely mentioned in prose. If `hex.fog`'s connection to a
token existed only as words inside its `effect` string, traversal would die at
depth 1. That is why `places` and `see_also` are fields of *any* registry record,
and why populating them in `tokens.toml` and `hexes.toml` is migration work
rather than a later nicety.

## Merge is set-accumulation with an explicit reset

Today merging is `dict |=` — last-wins replace keyed by display label — along a
fixed chain: Unit config → each Model's `unit_special`; Model config → each
Equipment in order. Under the new model (#116):

**1. `extend` is the default, and it keeps N instances.** The data layer never
merges two instances into one. Joining prose under one heading is a *rendering*
decision.

**Rejected: producing one instance with joined `text`.** It is unimplementable
the moment two instances of an id carry different args, which is the majority
case — one Unit carries `resistance` three times with three different versions.
There is no arg set the merger could produce.

**2. `replace = true` is a reset point in the source chain.** It clears every
instance of that id contributed by *earlier* sources, leaving itself and anything
contributed later. It needs no target field, because the table key is the target.

**Rejected: order-independent "clear everything with this id".** It would let a
default Equipment's `replace` silently eat a paid Upgrade's contribution,
inverting the paid-kit-wins ordering that `Model.equipment` and retained defaults
exist to guarantee (ADR-0020).

**3. The source chain stays the spine.** Explicit `replace` does not make
ordering irrelevant — the chain is what makes "earlier" in rule 2 mean anything.
Non-`replace` instances accumulate as a set and are semantically
order-insensitive; chain order determines print order and where reset points
fall.

**4. `replace` crosses levels, never slots.** An Equipment may replace a
unit-level Special: the chain is already cross-level, since `Model.unit_specials`
folds Equipment `unit_special` into the Unit's set, so this is a reset point
further down an existing chain. Crossing *slots* is an error — after the flat
namespace, `assault_poison` and `range_poison` are distinct rules, so a
cross-slot replace would be replacing a different rule.

**5. No implicit dedupe. `replace` is the only collapsing mechanism.**

This one bites. **Seven Units today have the same Model-granted unit Special
contributed by several Model slots** — `goblin_infantry` has four Models each
granting `Pre-Assault Retreat`, `gnome.assault_bots` four granting `Setup`, plus
`elf.pachycephalosaurus_riders`, `elf.pegasus_rider`, `ogre.drone_swarm`,
`ogre.repair_drone` and `ogre.medic_drone`. Today `dict |=` collapses them to one
printed line; under extend-by-default they become four identical instances — a
visible Army Reference regression in seven Units caused purely by adopting the
new rule.

The mechanism to express the old behavior already exists: `replace = true` on
each, so each Model's instance clears the previous sibling's and the net result
is one instance, exactly reproducing `dict |=`. So this is **a migration
instruction, not a new merge rule**.

**Rejected: an implicit structural-equality collapse** (same id + args + text +
name folds to one). It reproduces today's output automatically, but it makes
`replace` half-redundant and gives the model two collapsing mechanisms with
subtly different triggers. One mechanism, stated in the data, is worth a
migration sweep.

## Stat modifiers are a closed list of seven fields

`Stacker[T]` (`add` / `replace` / `extend`) already exists in
`src/spf/schemas/race.py` and already lets Equipment modify Model assault stats.
Extending it to Unit stats is the general mechanism, not a new one (#116).

**Seven modifiable stats. This is the scope fence.**

| stat | owner | today |
|---|---|---|
| `strength`, `strength_die`, `deflection`, `deflection_die`, `damage`, `ap` | Model assault | `EquipmentAssaultConfig`, has `Stacker` |
| `armor` | Unit | `UnitConfig.armor: Angles[int] \| None`, no modifier path |

Explicitly **not** modifiable: `cost`, `size`, `shaken`, `type`, the range block
(Equipment brings its own range profile rather than modifying one) and `orders`
(additive by its own mechanism, ADR-0007). Anything added later is a deliberate
one-at-a-time decision, not an open-ended effects engine.

**The fence needs no lint rule: it *is* the field list.**
`EquipmentAssaultConfig` declares the six modifiable stats as explicit optional
fields, and every config class subclasses `StrictModel` (`extra="forbid"`), so
`cost.add` is rejected at load today. Unit stats get the same treatment via a new
`[equipment.<x>.unit]` block and `EquipmentUnitConfig`, paralleling the existing
`[equipment.<x>.assault]`. One field today; adding a second is a visible act.

**Models may declare unit-stat modifiers too**, exactly as they already declare
`unit_special`. Equipment lives *on* a Model, so the path is already Unit ←
Model ← Equipment; forbidding the middle node — the one that already contributes
`unit_special` — would be the special case.

**Multiplicity follows the purchase.** A Model-declared unit-stat modifier is per
Model and **multiplies** by the number of Model slots declaring it. For
Equipment, multiplicity follows `upgrade_all`: `true` → **×1** (a unit-level
fixture, bought once for the Unit), `false` → **×N** (bought per Model, applies
per Model). This makes multiplicity mean what the price already means. All five
armor-granting Equipment in the data are `upgrade_all = true`, and
`wheeled_shieldwall` is one wall for the Unit at +[5,0,0,0], not +[20,0,0,0] on a
four-Model Unit.

**Rejected: always-×N, with `upgrade_all` staying purely a pricing concept.** More
uniform, but it gives a four-Model abomination Unit +[12,8,0,0] from one 8cp
`tentacle_shield` against a base of [8,6,5,4] — a doubling nobody designed.

**Only `add` multiplies; `replace` is always ×1.** Multiplying a replacement is
meaningless: four Models each replacing armor with `[6,6,6,6]` can only produce
`[6,6,6,6]`. Two competing replaces resolve last-in-chain, per merge rule 3.

**Two verb vocabularies, deliberately not unified.** `Stacker`'s
`add`/`replace`/`extend` quantify over a *value*; the instance `replace` bool
quantifies over a *set*. Unifying gives a verb set where `add` is meaningless for
Specials and `extend` means two unrelated things. The shared word `replace` keeps
one consistent gloss in both — "ignore what came before". Concretely: **no `add`
or `extend` key ever appears on a Special instance.**

### `Protection` leaves the Special vocabulary

Its eight uses are two unrelated things — armor grants
(`"[3, 2, 0, 0] in armor."`) and endurance tokens (`"1 endurance token per Dwalf
model"`). The armor half becomes an `armor` stat modifier; the endurance half
becomes a distinct Special, id `endurance`, with args for count and model class.
Dwarf's `Protection 2` is *both in one string* and becomes one stat modifier plus
one Special instance.

**Consequence:** `endurance` needs both a rule `todo` stub and a `tokens.toml`
entry — neither exists today. The only prose describing endurance tokens lives in
`rules/reference.toml`, which this ADR deletes, so that prose must be rescued
into the stub.

## Checking: a hard gate, a soft gate, and a countdown

The placement principle, fixed first so the list does not become a series of
individual judgment calls (#117):

> **If a violation means the resolver cannot produce correct output, it is a
> schema failure at load time. If the corpus is merely untidy, it is lint.**

**The hard gate** — pydantic, load time, fails `just validate`, which already
loads all eight Races and every `rules` command:

| Check | From |
|---|---|
| Every Special id in a Race file resolves to a rule record | one vocabulary |
| Every id is used in a slot the rule declares (`slots`) | flat namespace |
| Every ref resolves, and its value lands in the permitted set | refs |
| Args validate against the union of the rule's `variables` and every ref target's | ref args |
| Cross-slot `replace` is rejected | merge rule 4 |
| Record completeness: a meaning field or `todo`, never neither | completeness |
| Instance envelope closed — *free from `StrictModel`* | args |
| Stat-modifier fence — *free from `StrictModel`* | seven stats |

The args row is the largest single gain: `N ∈ {4,6,8,10,12}` and the `die` union
are checked for the first time. `variables` is read today only by the Rulebook
renderer, for display — nothing validates against it.

**The soft gate** — a new `spf rules lint` and `just lint-rules`, sitting after
`lint-races`. It covers unreachability and key/name agreement over the registries:
after this ADR the rules TOMLs *are* the vocabulary registry, with keys and
display names of their own, so they earn the same `key`↔`name` discipline Races
already get. `src/spf/lint/rules.py`'s predicates are pure functions over
`(key, name)` with no schema dependency, so they are reused directly. A sibling
command rather than an extension of `spf race lint`, which keeps ADR-0016's
staging honest: a broken `rules/*.toml` should fail `validate` and be *skipped*
by its own linter.

**No warning tier.** The existing contract holds: **lint speaks ⇒ the build
fails.** A permanent warning tier rots — nobody reads output from a green build —
and it would force inventing a suppression syntax for warnings consciously
accepted. Report-only work therefore leaves `just check` entirely.

**The countdown** — `spf rules todos`, one non-gating command the game designer
runs deliberately, with two sections: unwritten rule text (records whose
completeness is satisfied by `todo`, ~45 to start) and unreachable rules
(declared but referenced by no instance).

Adding a stub is deliberately **no harder** than writing a real rule. Making it
harder punishes the designer for honestly marking text as unwritten, and the
failure mode it creates — fake one-line rule text to dodge the ceremony — is
strictly worse than a stub. The countdown's visibility is the friction.

**Unreachability is a countdown, not a gate.** This is the one place an error was
genuinely arguable, and it loses on the allowlist trap: most unreachable rules
are *intentionally* dead (the `assault_*` / `range_*` pairs), so gating would
demand a hand-maintained list of the intentional ones — exactly the kind of list
deleting the `Literal`s exists to remove.

**Three proposed checks are deliberately not built.** Same-id collisions are not
a check at all — N instances is well-defined, and post-migration a deliberate
second `heal` instance and an accidental one are structurally identical, so there
is nothing to discriminate on. The `Stacker` scope fence is already free from
`StrictModel`. And two `replace`s on one stat in one loadout is defined behavior
(last-in-chain-wins) that may be deliberate layering; with no warning tier the
only options are "error" or "nothing", and erroring on defined semantics is
wrong.

Each of these is the same shape as the envelope and overlay decisions: where a
defect can be made **unrepresentable**, that beats making it detectable.

## Rendering is out of scope, and inherits a guarantee

Nothing here decides how Specials are printed. What rendering (#73) receives is:
a resolved instance list per slot with N instances per id, the reference graph
with a guarantee that every edge resolves, and both a rule name and an optional
per-instance atmospheric name.

What rendering owns: grouping N instances of an id under one heading, traversal
depth and cycle policy per relationship kind, how an atmospheric name composes
with the rule name on the page, and — a new one — group order and titles for the
to-hit table.

That last one moves out of Python. Group **order** is namespace declaration order
in `namespaces.toml`; **titles** come from a display `name` field on each
namespace record; **membership** is a *query* — every record in the namespace
carrying `to_hit` / `to_be_hit`, with empty groups dropping out, which is already
`parse_to_hit`'s rule. A namespace may declare `group` to render under another's
heading (`hex` declares `group = "terrain"`, so fog renders among the terrains
rather than in a one-row group of its own). `TO_HIT_TITLES` in
`render/rulebook.py`, and its stale `"order": "Orders"` entry for a category that
does not exist, disappear with the dict (#126).

**Rejected: the Rulebook index owning a hand-listed group order.** It is the more
editorial home and ADR-0018 is the precedent — but `namespaces.toml` exists
precisely so a new namespace is a one-line addition, and hand-listing groups
costs two edits in two files. Worse, it picks the failure mode ADR-0018 fears: a
namespace whose records carry modifiers silently vanishes from the table until
someone edits the index.

## Target shapes

A rule, with variables and both reference kinds:

```toml
[special.assault_poison]
name = "Assault Poison"                   # display name — the one place it lives
slots = ["assault"]                       # where this id may be used; checked at load
signature = "[{N}][1 for {M}]"            # template over the declared variables
effect = "Targets get one poison[{N}] token for each {M} hits."
flavor = "Envenomed blades, worked into the press of melee."
places = ["token.poison"]                 # mechanical consequence: this rule causes it
see_also = ["special.range_poison"]       # editorial pointer only, never load-bearing

[special.assault_poison.variables]
N = { type = "int", values = [4, 6, 8, 10, 12] }
M = { type = "int", min = 1, max = 4 }
```

A stub — `todo` present, no meaning-bearing field, which is the only other legal
state:

```toml
[special.stacking_limit]
name = "Stacking Limit"
slots = ["unit"]
todo = """
Rule text not yet written. From reference.toml: no references identified.
Design note (GA): see hex stacking in overview_round.md — the limit is
per-hex, not per-unit.
"""
```

A rule whose variable is a ref, with a rule-local version overlay:

```toml
[special.resistance]
name = "Resistance"
slots = ["unit"]
signature = "{version}[{N}]"              # {version} renders the TARGET's name
effect = "Gives improved resilience versus {version} damage."

[special.resistance.variables]
version = { type = "ref", namespaces = ["damage_type"] }
N = { type = ["int", "die"], min = 1, max = 12 }   # union: 6 or d6

# rule-local prose keyed by ref value — belongs to resistance, not to the target
[special.resistance.versions.acid]
effect = "Any die rolled by an acid or minor acid token is reduced by {N}."
```

A ref accepting several namespaces:

```toml
[special.immunity.variables]
feature = { type = "ref", namespaces = ["token", "hex", "special", "damage_type"] }
```

A modifier record, with its overlay fields inlined and its own variables:

```toml
[ability.camouflage]
name = "Camouflage"                       # no longer "Camouflage[terrain]"
signature = "[{terrain}]"                 # the parameters move here
to_hit = "0"
to_be_hit = "-1"
effect = "Applies when the unit is in the given terrain."   # was `note`

[ability.camouflage.variables]
terrain = { type = "ref", namespaces = ["terrain"] }
```

The namespace registry:

```toml
# rules/namespaces.toml — declaration order is display-group order
[namespaces]
special     = { name = "Specials",  file = "special.toml",    table = "special" }
token       = { name = "Tokens",    file = "tokens.toml",     table = "tokens" }
hex         = { name = "Hexes",     file = "hexes.toml",      table = "hexes", group = "terrain" }
terrain     = { name = "Terrain",   file = "terrain.toml",    table = "terrain" }
ability     = { name = "Abilities", file = "modifiers.toml",  table = "ability" }
distance    = { name = "Distance",  file = "modifiers.toml",  table = "distance" }
damage_type = { name = "Damage",    file = "namespaces.toml", table = "damage_type" }
```

Instances in a Race file — three `resistance`, an atmospheric name, and a
cross-source `replace`:

```toml
# "Resistance" = "Poison[12], Fire[3]" was ONE label; it is two instances
[[units.armored_unicorn_rider.specials.resistance]]
args.version = "damage_type.poison"
args.N = 12

[[units.armored_unicorn_rider.specials.resistance]]
args.version = "damage_type.fire"
args.N = 3

# args are the UNION of the rule's variables and the ref target's:
# `ability` is to_hit's, `terrain` comes from ability.camouflage
[[units.darkelf_sniper.specials.to_hit]]
args.ability = "ability.camouflage"
args.terrain = "terrain.forest"

# atmospheric name: prints "Excellent Whip Handling", resolves to the shared rule
[[units.ork_whipmaster.specials.to_hit]]
name = "Excellent Whip Handling"
args.ability = "ability.excellent_shot"

# replace needs no target — the table key IS the target
[[equipment.stabilizer.model_specials.to_hit]]
name = "Enhanced Accuracy"
args.ability = "ability.good_shot"
replace = true
```

A unit-stat modifier on Equipment:

```toml
[equipment.tentacle_shield.unit]
armor.add = [3, 2, 0, 0]                  # `add`, not `replace` — see #109 below
```

## Consequences

**Every "Rules do not resolve" problem in #101 is answered by construction**, and
#73 becomes the filtering-and-rendering job it was always meant to be. The ~30
genuinely missing rule texts remain genuinely missing — they are game-design
authorship, and the model's contribution is to make them **countable** rather
than invisible.

**#108 (concatenate Specials) is a rendering issue.** The data layer keeps N
instances and the renderer groups by id under one heading. Two further
consequences: the `(2)` / ` 2` suffixes the issue was written against disappear
entirely under the instance shape, so the relabeling its author offered to do by
hand is unnecessary; and its "labels differing by only space and a number"
heuristic is not needed, because after migration the id *is* the grouping key.

**#109's stated requirement is wrong, and must not be implemented as written.**
It asks for Equipment armor to *overwrite* a Unit's armor. Every real instance in
the data is **additive**: `tentacle_shield` grants `[3, 2, 0, 0]` to Units with
base armor `[8, 6, 5, 4]`, so an overwrite would drop that Unit's front arc from
8 to 3; Dwarf's `Protection 2` spells it out — *"Add [4,3,3,3] in armor"*; and
`wheeled_shieldwall`'s `[5, 0, 0, 0]` is front-arc-only and meaningless as a
replacement. `armor` therefore gets the full `Stacker` — `add`, which is what all
five current cases mean, and `replace`, available for the "this armor supersedes
yours" case that has not yet appeared.

**Seven Units need `replace = true` or they ship visible duplicates** (merge rule
5). This is the migration's sharpest edge and the one regression that adopting
this model causes rather than fixes.

**`spf special show` needs a real rewrite**, not a mechanical edit: frozensets
become a registry lookup, the `TypeIs` guards become the rule's `slots`, and
`key in u.special` becomes iteration over N instances — so `_unit_matches` yields
N rows per holder instead of one.

**`spf.lint.rules` should be renamed.** A module of name predicates and a
directory of game data now share the word, and `spf rules lint` puts both in
scope of one command.

**Migration is a follow-up, planned but not executed here.** The plan lives in
[`docs/specials-migration-plan.md`](../specials-migration-plan.md); the identifier
census it works from is [`docs/specials-census.md`](../specials-census.md).
