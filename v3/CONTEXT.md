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
