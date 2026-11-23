# The Damage Simulator

`spf sim damage` answers one question for game balancing: *given a Unit, some
damage that has just landed on it, and perhaps more damage arriving every Round,
how does it play out?* It plays the situation out thousands of times with real
dice (a Monte Carlo simulation), then reports how often the Unit dies, how many
Models it loses, how long the Continuing Damage lasts, and what the Unit looks
like Round by Round.

It is a balancing aid, not a rules engine. It reads the Damage tables in
`races/` with a best-effort parser. Anything it cannot follow is skipped and
**listed in the report**, so you always know what the numbers leave out.

```console
uv run spf sim damage dwarf.dwarf_infantry --start "d6, bleed=4, future=2"
```

## What is simulated, and what is not

**One Unit, on its own.** The simulator follows a single Unit at its default
loadout: the Unit, its Models and their Default Equipment, with no upgrades.
Anything aimed elsewhere is counted as a **spillover event** but not followed.
That covers a poison cloud on the hex, minor acid splashed on Units in range,
Terror felt by friendly Units, and damage to transported Units.

**Damage that has already landed.** How an attack gets through is out of scope.
Armor and to-hit decide *whether* an attack lands. Once it has landed, Armor
plays no part in the damage, so the simulator starts from the damage roll.

**Models are a count.** "Kill 1 model" takes one off the count. The Unit is
destroyed when the count reaches 0 or a row says "Unit destroyed". Which Model
dies is not tracked: every Model is treated alike. A Temporary Kill
("Temporarily kill 1 model") takes one off the same count, but reaching 0 does
not destroy the Unit. Since nothing heals, a temporarily killed Model stays
that way and counts as lost.

**No player decisions beyond one.** The simulated player always spends
Endurance when it is legal. They never heal or repair, and nothing else is
chosen.

**Not simulated at all:** movement, facing, to-hit modifiers, speed, orders,
healing and repair. Any Token without a damage effect of its own (Cannot Move,
Cannot Turn, …) is only *counted*: it shows up in the per-Round Token means, but
it does nothing. Shaken is also counted and never removed, but it does do one
thing (see [Which table a roll goes to](#which-table-a-roll-goes-to)).

## The two modes

| You give | The simulator plays | A run ends when |
|---|---|---|
| `--start` only | The starting state, then Rounds of Continuing Damage | The Unit is destroyed, **or** no Continuing Damage Token is left, **or** `--max-rounds` is reached |
| `--start` and/or `--incoming` | The same, plus the `--incoming` hits landing at the start of every Round | The Unit is destroyed, **or** `--max-rounds` is reached |

The first answers "what does this hit do to the Unit, all told?" The second is
a Unit under steady fire: "how long does it last?"

### Every Unit of a Race at once

`spf sim damage-race RACE` takes the same options and simulates every Unit of
the Race, printing one line per Unit: its Points, P(Destroyed), E(Points
Destroyed), mean Models lost, and the last row of that Unit's mean-state table.
That row's Round is the Unit's longest run, so it differs from Unit to Unit.
Units without the `--table` table are skipped and named. Every Unit is
simulated with the same seed, so `spf sim damage race.unit --seed N` gives the
full report behind any line.

### Every Unit of an Army at once

`spf sim damage-army ARMY` names the Army as `spf army show` does
(`showcase/dwarf`, `2026/knut`) and takes the same options as `damage-race`. It
prints one line per Unit of the Army, in Army order, each Unit at the Loadout
its player bought: its upgrade Models, its Upgrade Equipment and its Unit
Fixtures. Repeated Units keep a line each. The `#` column is the Unit's
position in the Army, and the Unit column its Nick, or its catalogue name when
it has none. A Unit without the `--table` table is skipped and named, and keeps
its number, so the numbers can have gaps.

A **Total** row sums the Points and E(Points Destroyed) of the Units simulated
that have a Cost. Read its E(Points Destroyed) as "if every Unit took this
damage separately": what an opponent would expect to score, summed over the
Units.

A fielded Unit usually carries a different Loadout from the catalogue Unit that
`spf sim damage` plays, so `spf sim damage` does not reproduce a line of this
report.

## One run, step by step

### Before Round 1: the starting state

1. The Unit starts with all its Models and its Endurance Tokens. An
   `endurance` Instance gives N Tokens for every Model of the class it names
   that it reaches, whether from the Unit, the Model or the Model's
   Equipment: an elite Model is one of Type Elite or SuperElite, a regular
   Model is neither, and any other class (`model`, `soldier`) counts every
   Model.
2. Future Damage and Future Crew Damage from `--start` are placed.
3. Tokens from `--start` are placed (`bleed=4`, `fire=2`, `shaken`, …).
4. Each starting roll is resolved, one after another, as described under
   [Resolving one roll](#resolving-one-roll).

The Unit's state now is **Round 0** in the report. If the Unit is already
destroyed, or carries no Continuing Damage and nothing is incoming, the run is
over after zero Rounds.

### Each Round

Every Round runs these steps in order. They follow the end of a Round in
`rules/round.md`, and the start of the Round when there are incoming hits.

| Step | What happens |
|---|---|
| **Incoming** | Each `--incoming` roll lands on the Unit and is resolved like a starting roll. |
| **Agony 0: Terror and Acid** | Each Terror Token counts one spillover event (Terror on friendly Units). Then each Acid Token rolls a d8 on the acid table, less acid resistance (see below). |
| **Agony 1: Minor Acid** | Each Minor Acid rolls a d6, less acid resistance. On 3+ the Unit gains +1 Future Damage and the Minor Acid stays; otherwise the Minor Acid is removed. |
| **Agony 2: Fire** | *Every* Fire Token rolls a d6, less fire resistance, **before any of them deals damage**. A Fire at 2 or below goes out. Each one still burning then deals its roll as damage on the Regular table, plus Future Damage. |
| **Agony 3: Poison** | Each Poison[N] rolls a dN, less poison resistance, and deals that as damage on the Regular table, plus Future Damage. A Poison that killed a Model is removed; otherwise it drops one step (Poison[8] → Poison[6]), and Poison[4] is removed. |
| **Agony 4: Bleed** | Each Bleed[N] rolls a dN. On a 1 or 2 it is removed. Otherwise it deals that roll as damage on the Regular table, plus Future Damage. That damage never places a new Bleed: a Bleed it would place instead Raises the rolling Bleed, if larger. A Bleed that killed a Model is removed. |

After the last step the state is recorded for the report. The run then checks
whether it should go on (see [The two modes](#the-two-modes)).

A few details matter for reading the results:

- **The Unit can die mid-Round.** As soon as it is destroyed, the run stops,
  even halfway through a Phase.
- **Every Token rolls on its own.** Two Bleed[4] are two separate d4 rolls,
  each with its own chance to stop or to kill.
- **Tokens placed earlier in a Round act later in the same Round.** If Acid
  rolls a 7 in Agony 0 and sets the Unit on fire, that Fire burns in Agony 2.
  A Bleed placed by Fire damage bleeds in Agony 4. A Token placed during its
  own Phase waits for the next Round: a Bleed Raised during Agony 4 rolls at
  its new size next Round.
- **Continuing Damage ignores Armor and regular resistance.** Only fire,
  poison and acid resistance touch their own Tokens. Bleed has no resistance.

### The acid table

Acid's table lives in `token.acid` rather than on the Unit. Each row adds to
the one below it:

| d8, less acid resistance | Effect |
|---|---|
| below 1 | Nothing |
| 1 | The Acid becomes a Minor Acid |
| 2 | +1 Future Damage |
| 3 | As 2; Armor reduced by 1 (counted only, since Armor plays no part here) |
| 4 | As 3; the Unit gets a Minor Acid; poison cloud and minor acid on the other Units in the hex (**spillover**) |
| 5 | As 4; minor acid on Units within range 2 (**spillover**) |
| 6 | As 5; the Unit gains a Terror Token |
| 7 | As 6; the Unit gains a Fire Token |
| 8+ | Roll three more times on this table |

An Acid Token is never removed except by rolling a 1, so Acid keeps a run going
for a long time.

## Resolving one roll

Starting rolls, incoming rolls, and all damage from Fire, Poison and Bleed go
through the same steps.

### Which table a roll goes to

- A roll goes to the table it names: the table chosen with `--table` (Regular
  by default), or the one written in front of it (`psychic:d6`).
- A row's "d6 psychic damage" or "d6 critical damage" rolls on that other
  table.
- If the Unit has **both Crippled Crew and Shaken**, psychic damage goes to the
  **Crew** table instead (`token.crippled_crew`). This is the one thing Shaken
  does in the simulator.
- If the Unit has no such table, the roll has no effect. It is counted under
  "Rolls on a table the Unit lacks".

### What is added and subtracted

| Table | The value looked up is |
|---|---|
| Regular, from a hit | roll − regular resistance + Future Damage |
| Regular, from Fire / Poison / Bleed | Token roll (after its own resistance) + Future Damage |
| Psychic | roll − psychic resistance |
| Crew | roll + Future Crew Damage |
| Critical, Inner | roll |

Future Damage applies to **every** roll on the Regular table, whatever caused
it, and never to Psychic or Critical. Each resistance comes from the Unit's
`resistance` Instances. Each source counts once however many Models carry it:
the Unit itself, a kind of Model, or a kind of Equipment. A Unit Fixture counts
once per purchase. Resistances of the same kind from different sources add up,
and a resistance written as a die is rolled each time. `--no-resistance`
ignores them all, so you can compare.

### Finding the row

- The value is checked against each row's printed roll (`4`, `2-3`, `9+`).
- **Above the top row:** the top row reads as "N and higher". On a table
  ending `18: Unit Destroyed`, a 19 is Unit Destroyed.
- **Below the lowest row, or in a gap between rows:** no effect.
- A Row reference ("As 4-5, Shaken") does everything row 4-5 does first, then
  the rest.

### Applying the row

The row's effects apply in the order written:

| Effect as written | What the simulator does |
|---|---|
| Kill N models / Destroy N models | Kills N Models, one at a time (see [Killing a Model](#killing-a-model)) |
| Temporarily kill N models | The same, except the Unit is not destroyed when the last Model goes |
| +N to future damage (also "x3 +3 …") | Adds Future Damage |
| +N to future crew damage | Adds Future Crew Damage |
| Unit destroyed / Unit killed | The Unit is destroyed |
| d6 psychic damage, d6 critical damage, … | Rolls on that table |
| Bleed[6], Poison[4], Fire, Acid, Minor Acid | Places that Token, except a Bleed rolled by a Bleed (see [Placing a Token](#placing-a-token)) |
| Bleed[M], when a Bleed[N] made this roll | Raises the rolling Bleed to Bleed[M] if M is larger than N; otherwise nothing |
| Shaken, Crippled Crew, Cannot Move, … | Places that Token (counted only, apart from Shaken's routing above) |
| Amplify (all) bleeding | Steps every Bleed up one size: 4→6→8→10→12, capped at 12 |
| If caused by bleeding, amplify bleeding | The same, but only when a Bleed made this roll |
| Roll N times on this table | Rolls the same damage N more times on this table |
| Anything aimed at other Units or the hex | Counted as spillover |
| Anything else | Skipped, and listed under **Not simulated** |

Where a row says `{Bleed[4]:token.bleed}` (a Rule Link), the link decides which
Token is meant, even if its label says something else. Plain words are only the
fallback.

#### Placing a Token

- **Shaken** is placed twice when the Unit has none, and once otherwise
  (`rules/tokens.toml`).
- **Fire** stacks: two Fire placements make two Fire Tokens.
- A Unit **immune** to a Token (a table note such as "Immune to Poison") never
  takes it.
- **Bleed never causes a new Bleed** (`token.bleed`). When a Bleed[N]'s own
  damage would place a Bleed[M], it **Raises** the rolling Bleed instead: to
  Bleed[M] if M is larger than N, and otherwise nothing happens. Only the Bleed
  that rolled is touched. This comes from the Token, not from the table notes:
  the "Bleed does not cause more Bleed" notes are recognized and change
  nothing. Bleed placed by a hit, Fire, Poison or Endurance stacks as usual.
- A Raise and an Amplify in the same row apply in the order written:
  "Bleed[6], Amplify all bleeding" turns a rolling Bleed[4] into Bleed[8].

#### Killing a Model

1. If every Model is already temporarily killed, no Model dies. A table note
   "When all models are temporarily killed: replace kill 1 model with …"
   applies its effects instead; without one, nothing happens. Either way it is
   not a kill, so no Endurance is spent and the Bleed or Poison that rolled
   stays.
2. If the Unit has an **Endurance Token**, it is spent. No Model dies, Future
   Damage is not halved, and the Unit gains Bleed[4]. If a Bleed was doing the
   killing, that Bleed is set back to Bleed[4] instead (`token.endurance`).
3. Otherwise a Model dies. If any of the Unit's table notes halve Future Damage
   on a kill, Future Damage is halved, **rounding down**. This happens once for
   each Model killed.
4. If no Models are left and the kill was not a Temporary Kill, the Unit is
   destroyed.

When a Bleed's roll both kills (or is saved by Endurance) and Raises that
Bleed, the kill wins: the Bleed is removed, or set back to Bleed[4].

## Reading the report

Every report prints the **seed** and the **number of runs**. Rerun with the
same `--seed` to get exactly the same report. Without `--seed`, a fresh one is
chosen and printed.

| Section | What it shows |
|---|---|
| **The Unit's Damage tables** | Printed first, the chosen table on top, each with its notes underneath. Text the parser skipped is colored red, so you see exactly which parts of a row are left out |
| **Summary** | P(Destroyed); the Unit's Points at its default loadout (`–` for a Unit with no Cost); E(Points Destroyed), P(Destroyed) × Points; Models lost (mean, median, 90th percentile, where a destroyed Unit counts as losing all its Models); how runs ended. E(Points Destroyed) assumes the attacker scores a Unit's Points only when the whole Unit is destroyed, and leaves out every other victory-point rule |
| **Rounds played, by how the run ended** | The share of runs that ended after each number of Rounds, in separate columns for runs that ran out of Continuing Damage, were destroyed, or hit the cap |
| **Mean state at the end of each Round** | Mean Models alive, Future Damage, Future Crew Damage and every Token count. Bleed and Poison get a column per strength (`bleed[4]`, `bleed[6]`, …), since strengths change during a run: Poison steps down each Round, and amplified or saved Bleed changes die. Round 0 is the state after the starting rolls. A run that has already ended is held at its final state, so the means stay comparable from Round to Round |
| **Damage table rolls** | How many rolls each table got over all runs, with the chosen table first |
| **Rolls on a table the Unit lacks** | Effects that pointed at a table this Unit doesn't have |
| **Spillover events** | Effects aimed beyond this Unit, with how often they happened |
| **Not simulated** | Every row clause and note the parser skipped, with how often runs reached it. A note is counted each time its table was rolled |

**Read *Not simulated* before trusting a figure.** A rarely hit clause hardly
matters. A clause hit thousands of times may be what decides the outcome. When
a clause on that list matters, write it more plainly in the Unit's table, or
ask for the parser to learn it.

## The `--start` and `--incoming` grammar

Both take a comma-separated list:

| Item | Meaning |
|---|---|
| `d6`, `2d4-1`, `3` | A roll on the chosen `--table` |
| `psychic:d6` | A roll on a named table |
| `future=2`, `future_crew=1` | Future Damage / Future Crew Damage (`--start` only) |
| `bleed=4`, `poison=6` | One Token of that strength (`--start` only; repeat for more) |
| `fire=2`, `acid=1`, `minor_acid=1` | That many Tokens (`--start` only) |
| `shaken`, `crippled_crew` | One Token (`--start` only) |

Other options: `--runs` (default 10 000), `--seed`, `--max-rounds` (default
20), `--no-resistance`.

```console
# How bad is a Bleed[6] with +2 Future Damage, after a hit?
uv run spf sim damage dwarf.dwarf_infantry --start "d6, bleed=6, future=2"

# A vehicle under steady fire, hit by regular and psychic damage every Round
uv run spf sim damage ogre.main_engine --incoming "d6, psychic:d6" --max-rounds 6

# The same starting hit, with and without resistance
uv run spf sim damage ork.troll --start "d8, poison=8" --seed 1
uv run spf sim damage ork.troll --start "d8, poison=8" --seed 1 --no-resistance
```

## Known gaps

These are open questions for the game designer, not oversights:

- **"if already Shaken double initial crew damage"** is not simulated, because
  "initial crew damage" can be read more than one way. It appears under
  *Not simulated*.
- **Shaken is never removed.** It only matters for routing psychic damage to
  the Crew table.
- Conditional rows ("If more than 2 models are alive, …"), crew kills, and a
  whole Unit being "temporarily destroyed" are not simulated. They are listed
  under *Not simulated*.
- **Conditional resistances are always on.** A resistance that holds only
  while an elite is alive applies for the whole run, because the simulator
  does not track which Model dies. The owner chooses which Model to remove, so
  elites tend to be the last to go.
- **"Counts as an elite"** in prose, such as the dwarf Battle Medic's for the
  Vest of Life Support, is not simulated: the Model counts by its Type.
