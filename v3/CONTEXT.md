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

**Unit**:
A group of Models fielded and activated together (e.g. Elf Infantry, four
`elf_infantry` Models). The costed, ordered building block of an Army.

**Model**:
A single figure within a Unit. Carries assault stats, a type, and Equipment. A
Model slot may be swapped for a costed upgrade Model.
_Avoid_: miniature, figure, piece

**Equipment**:
Weapons or gear attached to a Model. Either default (free, baked into the Model)
or an upgrade (paid). Modifies assault, range, orders, and specials.
_Avoid_: gear, item, weapon, kit

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
Melee combat. Characterised by strength, deflection, damage, and armour
penetration, resolved per facing Angle.
_Avoid_: melee, close combat

**Range** (ranged attack):
A ranged weapon's attack profile: reach, firing angle, damage, and armour
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
A named rule that modifies a Unit, Model, Equipment, Assault, or Range beyond
the base stats. Defined in `rules/special.toml` and referenced by name.
_Avoid_: ability, trait, perk

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

### Board and state

**Hex**:
A single tile of the hex-based board. May carry terrain effects that apply in
particular Phases.

**Token**:
A marker tracking transient state on a Unit or Model (bleeding, poison, +1
future damage, …), placed and removed in specific Phases.

**Nick**:
The player-chosen name of an Army instance.
_Avoid_: nickname, label, title

### Game-data maintenance

**Changelog**:
A human-maintained record of deliberate balance changes to game data, one per
data directory: `races/changelog.md` for Race edits and `rules/changelog.md` for
rules edits. A Markdown table of **Date, Description, Why**. It records the
*reasoning* behind a change — why a Unit, Model, Equipment, or Special was
buffed, nerfed, or removed — not the mechanical edit itself (git already records
that).
_Avoid_: history, release notes, git log (git records the edit; the Changelog
records the intent)

### Rendering (generated reference artifacts)

**Rendering**:
A generated file artifact produced by rendering one Product to one Format. The
output of the `spf/render/` subsystem; distinct from terminal/Rich output, which
serves authoring and inspection, not gameplay reference.
_Avoid_: export, document, output

**Product**:
One of the four kinds of gameplay reference we generate: **Order Card**, **Army
Reference**, **Race Overview**, **Rulebook**. Each Product binds to one
source-of-truth object and is rendered through a template family.

**Format**:
An output syntax a Product renders to: `markdown`, `html`, `latex`, `pdf`.
Markdown and LaTeX are *authored* as template families; HTML derives from the
Markdown family, PDF derives (via pdflatex) from the LaTeX family.

**Order Card**:
A single printed card carrying one *order option* — one Order type (Movement
**or** Fire, never both) for one Unit — showing that option's cells across every
Speed the Unit has it at (e.g. one Movement card lists `still`, `slow`, `fast`
rows for option 1; option 2 is the next card). The Order Card Product renders a
whole resolved Army as one **deck** file (in PDF, nine cards to an A4 page).

Each Unit's orders are the *merged* orders: its base `orders` unioned per Speed
with any orders gained from equipment (`orders_gained`), appending the gained
rows. Units that produce identical cards collapse to one set (no duplicates).
_Avoid_: order sheet, unit card (a card is one option, not one Unit)

**Army Reference**:
A Rendering of the exact rules pertaining to one Army, built from a resolved
Army. A nested Unit → Model → Equipment view of the fielded force: stats,
specials (the short override text — full rule text belongs to the Rulebook),
and damage tables. Orders are *not* part of it; those live on the Order Cards.
Identically-configured Units (and identical Models within a Unit) appear once.
_Avoid_: army sheet, roster printout

**Race Overview**:
A Rendering covering all Units, Models, and Equipment of one Race. Built from a
Race's `RaceConfig` (unresolved, for now).

**Rulebook**:
A Rendering of the general, army-agnostic rules. Built from the `rules/*.toml`
configs.

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
Stored under `assets/<race>/images/`. May later be embedded by a Rendering —
that embedding is out of scope for the generation step.

**Model** (asset):
A 3D-mesh Asset (for on-demand printing) depicting a Unit or Model, stored
under `assets/<race>/models/`. The print-on-demand ordering leg is out of scope
for the generation step.
_Note_: overloads the domain **Model** (a single figure in a Unit); a Model
asset is the printable mesh *of* such a figure.

**Environment** (image generation):
A configured ComfyUI target — `local` (a contributor's own ComfyUI) or `cloud`
(Comfy Cloud) — the Image Service submits to, selected by
`assets.image.comfyui.env`. Each Environment runs its own Workflow against its
own models; the same request may yield different images in each.
_Avoid_: shell environment (unrelated), backend, target.

**Workflow** (image generation):
A ComfyUI API-format graph (JSON) naming the nodes and models one generation
runs. Per-Environment, and one each for generating and refining: `cloud.json`
and `cloud-refine.json` are committed, the `local*` ones are per-machine. The
Image Service patches only the positive prompt, the Negative Prompt, and the
seed — plus, for a refine Workflow, the sole `LoadImage`'s filename.
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
from a Race description. Chains, because the result is itself a Candidate.
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
coordinate both `refine --from` and `promote --pick` take.
_Avoid_: version, revision, generation, history
