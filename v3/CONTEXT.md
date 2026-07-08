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
destruction). Kinds include `regular` and `psychic`.

**Special** (special rule):
A named rule that modifies a Unit, Model, Equipment, Assault, or Range beyond
the base stats. Defined in `rules/special.toml` and referenced by name.
_Avoid_: ability, trait, perk

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
A per-Unit Rendering holding that Unit's Movement and Fire Orders. Built from a
resolved Army.

**Army Reference**:
A Rendering of the exact rules pertaining to one Army. Built from a resolved
Army.

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
