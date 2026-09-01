# SteamPunkFantasy

SteamPunkFantasy (spf) is a tabletop hex-based wargame army-management tool. It
reads race definitions from TOML, lets players assemble armies from them, and
validates and displays the result.

## Language

### Core hierarchy

**Race**:
A playable faction (elf, ork, goblin, …), defined by a single TOML file in
`races/`. Supplies the catalogue of Units, Models, and Equipment a player may
draw from.
_Avoid_: faction, army (a Race is the catalogue, not a player's force)

**Army**:
A player's fielded force, built from a single Race.
_Avoid_: team, roster, list

**Showcase Army**:
A ready-made Army that demonstrates a Race, built for simplicity and
beginner-friendliness: it uses as few distinct combinations of Unit and
Equipment as it can while still showing what the Race is about. It is the
beginner's on-ramp — an Army a new player can pick up and learn the game with
before designing one of their own. It spends within the budget like any other
Army but is under no obligation to exhaust it; buying the last few points may
not be worth the complexity it adds.
_Avoid_: sample army, starter army, demo army

**Unit**:
A group of Models fielded and activated together (e.g. Elf Infantry, four
`elf_infantry` Models). The costed, ordered building block of an Army.

**Model**:
A single figure within a Unit. Carries assault stats, a type, and Equipment. A
Model slot may be swapped for a costed upgrade Model.
_Avoid_: miniature, figure, piece

**Equipment**:
Weapons or gear attached to a Model, claiming capacity in one of its Holders.
Modifies assault, range, orders, and specials. Comes in two kinds: Default
Equipment and Upgrade Equipment.
_Avoid_: gear, item, weapon, kit

**Default Equipment**:
The Equipment a Model carries before a player spends anything on it. Costs
nothing, and is listed by the Model rather than chosen. A Model's Defaults yield
to its Upgrades under Holder pressure, so buying an Upgrade only costs a Default
its place when the two compete for the same Holder.
_Avoid_: free equipment, base equipment

**Upgrade Equipment**:
Equipment a player buys for a Model, adding to its Cost. Never yields a Holder
to anything else.

**Holder**:
A named place on a Model where Equipment sits, with a limited capacity — Hands,
Tentacles, Reserve Melee and so on. Each piece of Equipment claims capacity in
one; a Model that has run out of capacity in a Holder can carry no more
Equipment there. Sixteen Holders exist in the game data.

### Cost and points

**Cost**:
The price of a thing across four independent dimensions: **manpower points**
(`mp`), **craft points** (`cp`), **experience points** (`xp`), and **industry
points** (`ip`). Costs add dimension-by-dimension; they are never collapsed to a
single number except as Points.

**Points**:
The single scalar value of an Army for balancing, `mp + cp + xp + 3·ip + VPM`
(industry points count triple). This is the victory-point value a player fields.
_Avoid_: score, value, price (price is the multi-dimensional Cost)

**Victory Point Modification** (VPM):
A per-thing flat adjustment added to the Points total, over and above what the
Cost dimensions yield. Lets a Unit or Equipment be worth more or fewer Points
than its raw Cost implies.
_Avoid_: point adjustment, handicap, bonus points

**Unit Fixture**:
An Upgrade Equipment that a player buys once for a whole Unit, and that is
charged a single time however many of the Unit's Models carry it. Every other
Upgrade is priced per Model: each Model carrying one adds its Cost again.
_Avoid_: shared equipment, unit-wide upgrade, group upgrade

### Combat and the round

**Round**:
One full turn cycle. It opens with a planning phase in which players commit
their Orders, then runs through fixed Phases: Gunnery 1, Movement 1–3, Gunnery
2, and several clean-up phases (Healing, Agony, Aftermath).
_Avoid_: turn

**Phase**:
One named step within a Round (e.g. Gunnery 1, Movement 2). Orders, Tokens, and
Hexes take effect in specific phases.

**Order**:
The actions available to a Unit at a given Speed, arranged per Phase and
committed during planning. **Fire Orders** govern shooting; **Movement Orders**
govern moving (turn, forward, flee, …).
_Avoid_: command, action

**Assault**:
Melee combat. Characterized by strength, deflection, damage, and armor
penetration, resolved per facing Angle.
_Avoid_: melee, close combat

**Range** (ranged attack):
A ranged weapon's attack profile: reach, firing angle, damage, and armor
penetration.
_Avoid_: shooting, ranged

**Damage table**:
A lookup mapping a rolled damage result to its effects (kills, tokens, unit
destruction), made up of Damage rows plus table-wide notes. Kinds include
`Regular`, `Critical`, `Crew`, `Inner`, and `Psychic`.

**Damage row**:
One entry in a Damage table: a Damage roll paired with its effect text.
_Avoid_: damage line, damage table entry

**Damage roll**:
The roll portion of a Damage row that a rolled result is checked against —
an exact value, a range, or an "at least" threshold.

**Special** (special rule):
A rule that modifies a Unit, Model, Equipment, Assault, or Range beyond the base
stats. Defined once in `rules/special.toml` and referred to by **Identifier**,
never by its display name (ADR-0024). Race data carries **Instances** of a
Special, not copies of it.

A Special declares the **Slots** it is legal in, the **Variables** its Instances
may supply, and what it **places** — the Token or Hex Effect it causes.
_Avoid_: ability, trait, perk; label (a label was the old display-name key)

**Identifier** (id):
The snake_case key that names a rule inside its Registry —
`assault_extra_damage`, `good_shot`. The single vocabulary shared by rules data and race data, and the
lookup key, so a bad one fails the build rather than resolving to nothing.
_Avoid_: label, key (bare), name (the Display Name is a different thing)

**Display Name**:
The human-readable name of a rule (`"Assault Extra Damage"`), living in exactly one
place — the `name` field of its record. Never parameterized: parameters live in
the **Signature**. Race data never spells it.

**Atmospheric Name**:
An optional Display Name carried by a single **Instance**, overriding the rule's
own name where that Instance is printed — one Unit's `to_hit` printing as
"Excellent Whip Handling". The *vocabulary* stays central; what is *printed* may
be local.
_Avoid_: alias, nickname (Nick is an Army/Unit/Model name), flavor name

**Instance**:
One occurrence of a Special on a Unit, Model, or Equipment: an **Identifier**
plus typed **Args**, and optionally free `text`, an **Atmospheric Name**, and
`replace`. A holder may carry several Instances of the same Identifier — three
`resistance` for three damage types — and they stay distinct. An Instance is
either *prose-shaped* (`text`) or *case-shaped* (a **Preamble** over **Cases**),
never both (ADR-0030).
_Avoid_: entry, occurrence, usage

**Preamble**:
Prose an **Instance** prints *before* its **Cases**, scoping all of them — a
condition ("If not using aim") or an instruction ("fire once at all enemy models
within range"). Only meaningful with Cases: prose that scopes several Instances,
or that holds regardless of the rule, belongs in the carrier's `note`.
_Avoid_: condition (only some are conditional), prefix, lead

**Case**:
One value-bearing line of an **Instance**: **Args**, merged over the Instance's
own, plus a scrap of prose saying when those values apply ("[5+] at point blank
range"). Cases are hand-written in one array, so two that read alike are both
printed — unlike Instances, which are deduplicated.
_Avoid_: variant, band, entry

**Slot**:
Where a Special sits on the thing that carries it: `unit`, `model`, `assault`,
or `range`. A rule declares the Slots it is legal in, and using it elsewhere is
a load-time error. One rule may be legal in several Slots.

**Registry**:
A table in `rules/` that *owns* a vocabulary: its Identifier set **is** the legal
value set for its **Namespace**, it is the single definition site for each
record's name and text, and deleting it destroys a concept. Contrast an
**overlay**, which only annotates Identifiers another Registry owns — overlays
are inlined into their owner's record rather than modeled separately.
_Avoid_: table, lookup, catalogue (the Race is the catalogue)

**Namespace**:
The abstract single-segment name a **Ref** is qualified by — `special`, `token`,
`hex`, `terrain`, `ability`, `damage_type`. Declared in `rules/namespaces.toml`,
which maps it to the file and table holding it, so a Namespace name never encodes
the file layout. The list is open: adding one is a single line.

**Ref** (reference):
A typed pointer into rules data, always fully qualified as `<namespace>.<id>` —
`token.poison`, `hex.fog`. One value type with one syntax wherever a reference
appears: as an **Arg**, in a record's `places` or `see_also`, or as the target of
a **Version** overlay. Every Ref is *structural* — a declared field or a typed
Arg, never a name mentioned in prose — which is what makes the reference graph
traversable.
_Avoid_: link, pointer, cross-reference

**Variable** / **Arg**:
A rule declares **Variables** (a name, a type, and constraints); an **Instance**
supplies **Args** for them under `args.*`. An Instance's legal Arg set is the
union of its rule's Variables and those of every Ref target it resolves, so a
Ref's parameters travel with it. A Variable marked `optional` may be left out;
every other declared Variable must be supplied.

**Signature**:
The compact printed form of a rule, a template over its Variables —
`"[{N}, {M}+]"`. A bare `{var}` on a Ref-valued Variable renders the *target's*
Display Name, followed by the target's own Signature. A bracketed group whose
placeholders are all unfilled is dropped rather than printed. Replaces the old
convention of encoding parameters inside a name.
_Avoid_: short, format, pattern

**Version**:
Rule-local prose keyed by a Ref value: a rule saying "when this Ref resolves to
*that*, here is my text for it" — `resistance`'s per-damage-type wording. An
overlay on the target, not a second kind of reference; a rule with no Version for
a value inherits the target's own text.

A Special is **versioned over** a Namespace when a Ref-valued Variable is what
one Instance of it differs from the next by: `resistance` over damage types,
`assault_extra_damage` over the kinds it applies (ADR-0027). Version prose is
optional, and a versioned Special often carries none.
_Avoid_: **Variant** (a Version is keyed by a **Ref** into a Namespace and
overlays the *rule's* own text, not by an id the rule owns itself)

**Variant**:
Shared **Instance** prose, defined once on a Special and named by an id the rule
owns — `ammo`'s `always_loaded`. An Instance or **Case** draws one into the prose
slot its shape allows: an Instance with **Cases** takes it as a **Preamble**, one
without as its `text`, and a Case always as its `text`. The pool is one set of
bare strings per rule; the same Variant may be a Preamble in one place and a text
in another. Spelling the prose out longhand instead is untidy rather than wrong,
so it is a lint finding, not a load error.
_Avoid_: version (a **Version** is keyed by a **Ref** and overlays the *rule's*
`effect`; a Variant is keyed by a bare id and supplies an *occurrence's* prose)

**Stub**:
A record whose rule text is not yet written, marked by the presence of a `todo`
field carrying *what* is missing. A record is either complete or a Stub, never
both and never neither, and Stubs are **counted** rather than gated.
_Avoid_: placeholder, TODO (the field is `todo`; the concept is a Stub)

**Stat Modifier**:
A change an Equipment or Model makes to a stat it does not own, spelled with the
`Stacker` verbs `add` / `replace` / `extend`. Seven stats are modifiable and no
others: six Model assault stats plus a Unit's `armor`. Only `add` multiplies
across Models; `replace` is always applied once.
_Note_: `replace` is also an **Instance** key, where it means "ignore what came
before" over a *set* of Instances rather than over a *value*. The gloss is the
same; the vocabularies are deliberately separate, and `add` and `extend` never
appear on an Instance.
_Note_: a Stat Modifier has a **value** only once it is fielded, since what it
modifies belongs to the Unit or Model fielding it. A catalogue view such as the
**Race Overview** therefore prints the declared delta itself — `+3/+2/0/0` —
and resolves nothing (ADR-0031).

**Source Chain**:
The fixed order in which Specials and Stat Modifiers reach a Unit or Model: Unit
config → each Model's `unit_special`; Model config → each Equipment in order
(retained Defaults first, then Upgrades). Instances **accumulate** along it — the
default is to keep all of them — and an Instance marked `replace` is a **reset
point**, clearing every earlier Instance of that Identifier while leaving
anything contributed later. The chain is what makes "earlier" mean anything, so
`replace` never makes ordering irrelevant.
_Avoid_: merge order, precedence, override

**Spawn**:
The creation and placement of a new Unit on the battlefield during play, triggered by an event (e.g. game setup, shooting, or model death). Defined by a Spawn Rule.

**Spawn Rule**:
A structured configuration in a Race's TOML file under the `spawns` section that specifies the target Unit, optional initial Equipment, and whether to inherit equipment from the spawning model.
_Avoid_: summon, deploy

**Speed**:
A movement setting (still, slow, fast, and flying/sneak variants) that selects
which Order rows apply.

**Size**:
A Unit's physical scale, Tiny through Enormous.

**Type**:
A Model's classification (Infantry, Cavalry, Vehicle, Mechanical, …), used by
Equipment requirements and rules.

**Common Type**:
The Types shared by *every* Model in a Unit — the intersection of the Models'
Types. Summarizes a Unit's classification when its Models differ; empty when
they share nothing.

### Board and state

**Hex**:
A single tile of the hex-based board. May carry Terrain, and may have Hex
Effects placed on it.

**Terrain**:
A permanent feature of the board — forest, building, ruins, swamp — fixed at
setup. Terrain is never placed or removed during play, though a rule may
*replace* one Terrain with another (a destroyed building becomes ruins).

**Hex Effect**:
A transient effect placed on a Hex during play — fog, a poison cloud, a trap —
and removed again in a particular Phase. Distinguished from Terrain by being
placed and removable; a Hex Effect may still modify to-hit the way Terrain
does.
_Avoid_: "terrain effect" for this — that names Terrain, not a Hex Effect.

**Token**:
A marker tracking transient state on a Unit or Model (bleeding, poison, +1
future damage, …), placed and removed in specific Phases.

**Nick**:
The player-chosen name of an Army, Unit, or Model instance.
_Avoid_: nickname, label, title

### Game-data maintenance

**Changelog**:
A human-maintained record of deliberate changes to game data, one per data
directory: `races/changelog.md` for Race edits (**Date, Race, Description,
Why**) and `rules/changelog.md` for rules edits (**Date, Description, Why**).

A change belongs in it when it is *intentional* **and** alters rules or gameplay
identity — a Unit buffed, nerfed, or removed, but also one renamed (a player who
fielded the Mothership needs to know where it went). Corrections that change no
intent — spelling fixes, casing — are not Changelog material.

It records the *reasoning*, not the mechanical edit (git already records that).
_Avoid_: history, release notes, git log (git records the edit; the Changelog
records the intent)

**Hard gate**:
A check that runs when game data is *loaded* — a schema failure, raised by
pydantic and surfaced by `just validate` and by any command that reads the data.
Where a violation means the resolver cannot produce correct output, the check
belongs here. Best of all is a rule that makes the defect **unrepresentable**
rather than merely detected: a closed model, an explicit field list.
_Avoid_: validation (too broad), error (names the outcome, not the gate)

**Soft gate**:
A lint check over a corpus that loads fine but is untidy — key/name agreement,
naming conventions. Run by `spf race lint` / `spf rules lint` and their `just`
recipes. There is exactly one severity: **lint speaks ⇒ the build fails.** There
is deliberately no warning tier, because output from a green build goes unread.
_Avoid_: warning, advisory

**Countdown**:
A number that should go down but gates nothing — unwritten rule text (**Stubs**),
and rules no Instance reaches. Reported by `spf rules todos`, which sits outside
`just check` and is run deliberately. A Countdown is the right shape wherever
gating would demand a hand-maintained allowlist of the acceptable cases.
_Avoid_: warning (that would imply a tier the Soft gate does not have), backlog

### Rendering (generated reference artifacts)

**Rendering**:
A generated file artifact produced by rendering one Product to one Format. The
output of the `spf/render/` subsystem; distinct from terminal/Rich output, which
serves authoring and inspection, not gameplay reference.
_Avoid_: export, document, output

**Product**:
One of the five kinds of gameplay reference we generate: **Order Card**, **Army
Reference**, **Army Pack**, **Race Overview**, **Rulebook**. Each Product binds
to one source-of-truth object and is rendered through a template family.

**Format**:
An output syntax a Product renders to: `markdown`, `html`, `latex`, `pdf`.
Markdown and LaTeX are *authored* as template families; HTML derives from the
Markdown family, PDF derives (via pdflatex) from the LaTeX family.

**Order Card**:
A single printed card carrying one *order option* — one Order type (Movement
**or** Fire, never both) for one **Order Source** of one Unit — showing that
option's cells across every Speed it applies at (e.g. one Movement card lists
`still`, `slow`, `fast` rows for option 1; option 2 is the next card). The Order
Card Product renders a whole resolved Army as one **deck** file (in PDF, nine
cards to an A4 page).

A Unit's *merged* orders are its base `orders` unioned per Speed with any orders
gained from equipment (`orders_gained`), appending the gained rows. That merged
view is what the Markdown family shows. The LaTeX deck instead transposes each
Order Source separately, so no card mixes base rows with an equipment's gained
rows (ADR 0021). Units that produce identical cards collapse to one set (no
duplicates).

The front of a card carries the order kind, the option's rows, and the Unit
name; on an Equipment's cards the Equipment's name sits under the order kind, so
a deck can be sorted by loadout face up. The back carries the Unit's Image
Asset, with the Unit name above it and the order kind below; a Unit with no
committed art keeps the same layout minus the picture, so the back still
identifies the card.

_Avoid_: order sheet, unit card (a card is one option, not one Unit)

**Order Source**:
What a Card Set's orders come from: the base Unit, or one Equipment that
modifies its orders (`orders_gained`). Sources are independent — `orders_gained`
is additive (ADR 0007) — so a Unit's deck is the sum of its sources' Card Sets,
and a player fields a loadout by taking the base set plus one set per Equipment
carried.
_Avoid_: origin, provenance, owner

**Card Set**:
The Order Cards one Order Source contributes for one order kind. Shared between
Units only when every card in it applies to every Unit sharing it.
_Avoid_: deck (a deck is the whole Army's cards), stack, pile

**Army Reference**:
A Rendering of the exact rules pertaining to one Army, built from a resolved
Army. A nested Unit → Model → Equipment view of the fielded force: stats,
specials (the short override text on the Unit line, and the full rule text for
the rules it reaches in its **Rules Reference**), and damage tables. Orders are
*not* part of it; those live on the Order Cards. Identically-configured Units
(and identical Models within a Unit) appear once.
_Avoid_: army sheet, roster printout

**Rules Reference**:
The flat, alphabetical list of rule Records an Army's Specials reach, printed
after the Units in an Army Reference and in each Army's entry in an Army Pack.
One entry per Record, showing the rule's general text; the Unit lines link into
it. Omitted with `--no-rules`.
_Avoid_: appendix, glossary, rules index

**Kind Qualifier**:
The parenthetical namespace label after a Rules Reference heading — `Fog (hex)`
— carried by every entry, not only colliding ones.
_Avoid_: namespace tag, suffix

**Alias Entry**:
A Rules Reference entry for an Instance's atmospheric name, pointing at the
Record it is an occurrence of: *Insanity Field — see Terror (special)*.
_Avoid_: alias, nickname stub, redirect

**Army Pack**:
A Rendering binding the Army References of several Armies into one document —
a tournament's field in a single file, so a player can see both their own
Army and every competitor's. Built from an **Army Pack Index**. Each Army
starts on a fresh page and is complete on its own: nothing is shared or
deduplicated across Armies, so an organizer can hand one player their pages.
It renders an Army's rules through the *same* authored body template the Army
Reference does, so the two can never drift apart.
_Avoid_: booklet, compendium, tournament pack (a pack of showcase Armies is
not a tournament)

**Army Pack Index**:
The authored TOML file naming, in order, the Armies an Army Pack contains
(`armies/<dir>/pack.toml`), plus the Pack's title. Armies resolve relative to
the Index's own directory. An entry may carry a **Label**; a directory scan
deliberately is not used, because a roster is an editorial statement about who
is in the event, not a listing of whatever files happen to be present
(ADR 0018).
_Avoid_: roster file, manifest

**Label** (Army Pack):
An optional Index entry field — typically the player's name — combined with
the Army's Nick as "Label: Nick" in a Pack's contents. Distinct from the
Army's Nick: the Nick belongs to the Army wherever it is fielded, the Label
says who is fielding it *at this event*. An entry without a Label appears
under its Nick alone.
_Avoid_: nick (that is the Army's own name), player (a Label need not be one)

**Race Overview**:
A Rendering of one Race's whole catalogue, answering what a player can field,
what it can carry, and what it costs. Built from the Race's raw `RaceConfig`,
which is **unresolved by design**: nothing in a catalogue is fielded, so a
**Stat Modifier** prints as the delta it was declared as rather than a value
(ADR-0031, and the Race Overview addendum to ADR-0005). Four flat, cross-linked
sections — Units, Models, Equipment, Spawns — followed by a Rules Reference;
every record appears exactly once, rather than nested under each path that
reaches it.
_Avoid_: race reference (the nesting it implies is the shape this Product
rejects), race card

**Rulebook**:
A Rendering of the general, army-agnostic rules. Built from a **Rulebook
Index** — an ordered, authored list of Sections — not from whatever happens to
sit in `rules/` (ADR 0018). Its sources are the rules TOML files and free-text
Markdown files beside them.

**Rulebook Index**:
The authored TOML file listing, in order, the Sections a Rulebook contains
(`rules/rulebook.toml`). The editorial decision of what the rulebook *is*, kept
beside the rules as game data rather than in developer config.
_Avoid_: manifest, table of contents (the TOC is generated *from* the index)

**Section**:
One entry in a Rulebook Index: a source file, the Section Kind that reads it,
and the title it appears under. The title comes from the Index, never from the
source, and the source's own headings nest beneath it.
_Avoid_: chapter, part

**Section Kind**:
The shape of a Section's source, declared by the Section and bound to one parser
and one template partial per family (`markdown`, `specials`, `tokens`, `hexes`).
The extension point for a new rules file: adding one is a registration, never a
change to the pipeline. A parser is also handed a shared context over the
sibling rules files, so a Kind can resolve cross-references (a Special's Token)
whether or not the Index renders what it points at.
_Avoid_: type, format (Format is the output syntax)

**Site Index**:
The authored TOML file naming, in order, the Army Packs the deployed site
publishes and the heading each one appears under (`armies/site.toml`). The
third member of the authored-index family, with the Rulebook Index and the
Army Pack Index: publishing is an editorial statement about what the site
contains, not a listing of whatever pack directories happen to exist
(ADR 0018, ADR 0028).
_Avoid_: manifest, roster file, site map

**Landing Page**:
The generated entry page of the deployed reference site, linking to every
Rendering published there — one section per Army Pack, in Site Index order.
Generated from what actually built, so it cannot advertise a link to something
that failed to render. Distinct from a Product: it binds to no source-of-truth
object and no template family, so it is not a Rendering either — it is a
build-time artifact over the site's own contents.
_Avoid_: table of contents (that belongs to the Rulebook), manifest, homepage

### Generated assets (AI-authored color & atmosphere)

**Asset**:
A curated, committed artifact generated from source TOML by an AI service and
reviewed by a human before it lands. Canonical, versioned in git under
`assets/<race>/…`. Distinct from a Rendering (a throwaway build artifact) and
from a Cost dimension (`ip` is Industry Points, unrelated). Three kinds: Lore,
Image, Model.
_Avoid_: artifact (that's a Rendering build output), resource, media

**Candidate**:
A raw, uncurated Asset produced by a generate step, awaiting human review.
Candidates are non-canonical and gitignored, written under `candidates/<race>/…`
mirroring the Asset layout and addressed by Lineage. Promoting exactly one
Candidate commits it as the Asset; the rest are discarded.
_Avoid_: draft, option, variant, sample

**Lore** (asset):
A Markdown Asset holding the full story, history, and atmosphere of a Race,
generated from its TOML. Grows beyond what a TOML `description` field can hold;
stored as `assets/<race>/lore.md`.
_Avoid_: story, background, fluff, description (the TOML `description` is a
short prose field, the seed — not the Lore)

**Image** (asset):
A 2D image Asset depicting a Race or Unit, generated from its `description`.
Stored under `assets/<race>/images/`. Embedded by the Army Reference Rendering
and on the back of the Order Cards, both of which reference the committed file
where it lies rather than copying it (ADR 0017).

**Model** (asset):
A 3D-mesh Asset (for on-demand printing) depicting a Unit or Model, stored
under `assets/<race>/models/`. The print-on-demand ordering leg is out of scope
for the generation step.
_Note_: overloads the domain **Model** (a single figure in a Unit); a Model
asset is the printable mesh *of* such a figure.

**Brief** (asset generation):
The authored TOML text a Kind generates a Target's Candidates from — for an
Image, the Target's `description` field. Which text that is, is declared by the
Kind itself (`Kind.brief`), so a Kind that generates from something other than
`description` needs no change to the Targets or the listing code (ADR 0014).
Distinct from the Prompt, which is *composed* from the Brief plus the configured
preamble. A Target without a Brief cannot be generated for, so `spf assets list`
marks it `no brief` and `spf assets image` warns and skips it (ADR 0015).
_Avoid_: prompt (that's the composed string), seed (that's the RNG seed),
description (the TOML field name; for an Image the two coincide, for another
Kind they may not)

**Environment** (image generation):
A configured ComfyUI target — `local` (a contributor's own ComfyUI) or `cloud`
(Comfy Cloud) — the Image Service submits to, selected by
`assets.image.comfyui.env` or `--env`. Each Environment runs its own Workflows
against its own models; the same request may yield different images in each.
_Avoid_: shell environment (unrelated), backend, target.

**Profile** (image generation):
A named pair of Workflows within an Environment — one to generate, one to
refine — identified by the filename stem under `workflows/<env>/`. Discovered
by scanning that directory, not declared in config. Each Environment has its
own set; the same Profile name need not exist in both. Selected by the
per-env `profile` config key or `--profile`.
_Avoid_: model (bound twice already), variant, preset.

**Workflow** (image generation):
A ComfyUI API-format graph (JSON) naming the nodes and models one generation
runs. Laid out per Environment per Profile under `workflows/<env>/`:
`<profile>.json` for generating, `<profile>-refine.json` for refining.
`cloud/` is committed; `local/` is gitignored per-machine. The Image Service
patches only the positive prompt, the Negative Prompt, and the seed — plus,
for a refine Workflow, the sole `LoadImage`'s filename.
_Avoid_: pipeline, graph (in user-facing text).

**Negative Prompt** (image generation):
What an image should _not_ contain, authored in the file named by
`assets.image.negative_prompt` (by default `prompts/image-negative.txt`) and
patched into a Workflow's negative encoder at generation time. One file
serves both Environments and both operations (generate and refine), and it
**replaces** whatever the Workflow authored rather than adding to it. Required
— a missing file is an error, not a fall-through.
_Avoid_: negative, neg prompt, exclusions, banned terms

**Refinement**:
Generating Candidates from an existing Candidate plus a Correction, rather than
from a Race description. Chains, because the result is itself a Candidate. May
also start from a promoted Asset: the Asset is staged into the Candidate store
first, so the operation itself is unchanged.
_Avoid_: edit, variation, touch-up, img2img (an implementation mechanism, not
the domain operation)

**Correction**:
The verbatim edit prompt a Refinement applies ("make the hat brass instead of
leather"). Used as the whole positive prompt — no description, no wrapper — and
always phrased positively: the Negative Prompt is a fixed, shared file, so a
Correction has no per-call negative to carry an exclusion in.
_Avoid_: instruction, tweak, fix, note

**Lineage**:
The dotted 1-based Candidate index (`2`, `2.1`, `2.1.3`) recording derivation:
`2.1` is the first Candidate of the Refinement of Candidate `2`. Readable
straight off the filename, so no provenance is recorded anywhere else. The
coordinate both `refine --from` and `promote --pick` take. Permanent: a Lineage
is allocated past whatever already exists, never reclaimed and never
renumbered, so it is a coordinate rather than a count of anything.
_Avoid_: version, revision, generation, history

**Target**:
The thing an Asset depicts — a Race, a Unit, or a Model. Which of those a given
Kind applies to is declared by the Kind itself (Lore targets a Race only; an
Image targets a Race or a Unit). The name that addresses a Target on the command
line is the same key `promote` and `refine` take.
_Avoid_: subject, referent

**Survey**:
The result of checking one Kind's Targets for one Race against the two stores:
which have an Asset, which have Candidates waiting, and which files match no
Target. Derived on demand, never stored.
_Avoid_: inventory (a Survey is driven by what *should* exist, not by what is on
disk), report, census

**Coverage**:
One Target's line in a Survey: whether its Asset exists, and its Candidates.
_Avoid_: status, entry

**Orphan**:
A file in the Asset or Candidate store matching no Target of its Kind — usually
a Target renamed in TOML after generation, or a typo. Surfaced under the
`Unknown` heading rather than silently ignored.
_Avoid_: stray, dangling
