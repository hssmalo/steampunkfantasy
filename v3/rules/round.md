# The Round

A battle is fought over a sequence of **Rounds**. Every Round runs through the
same fixed list of **Phases**, in the same order, for every Army on the table.
Nobody takes "their turn" — both sides act inside each Phase, and the Phase
order is what decides who shoots before who moves.

Play Rounds until the scenario's end condition is met.

## Phases of a Round

The Phases run in this order. A Phase in which nothing can happen is skipped
silently; you never lose a later Phase by skipping an earlier one.

- **Gunnery 1** — long-range fire, before anyone has repositioned. Apply damage.
- **Trigger hex effects** — the terrain acts: burning hexes, gas, collapsing
  ground.
- **Movement 1** — every Unit executes its movement order for its current Speed.
- **Pre-assault retreat** — a Unit about to be assaulted may pull back.
- **Pre-assault abilities** — abilities that resolve before blows land.
- **Assault 1** — melee in every contested hex. Apply damage.
- **Post-assault retreat** — a surviving Unit may fall back out of contact.
- **Trigger hex effects**
- **Movement 2**
- **Pre-assault retreat**, **Pre-assault abilities**
- **Assault 2** — apply damage.
- **Post-assault retreat**
- **Trigger hex effects**
- **Movement 3**
- **Pre-assault retreat**, **Pre-assault abilities**
- **Assault 3** — apply damage.
- **Post-assault retreat**
- **Gunnery 2** — close-range fire, after the lines have shifted. Apply damage.
- **Healing and repair 1** — the first of the two windows for restoring Units.
- **Agony 0** — major acid and terror. Apply damage.
- **Agony 1** — minor acid. Apply damage.
- **Agony 2** — fire. Apply damage.
- **Agony 3** — poison. Apply damage.
- **Agony 4** — bleeding. Apply damage.
- **Healing and repair 2** — the second restoration window.
- **Aftermath** — remove smoke, clear expired markers, reveal what the Round
  uncovered.

---

## Everything in a Phase happens at once

Within a single Phase, every effect resolves **simultaneously**. Two Units that
shoot each other in Gunnery 1 both fire; a Unit destroyed there still gets its
shot away. In practice this means you may roll all the damage for a Phase
together, in whatever order is convenient, and only then remove casualties.

The same holds for movement: Units do not move one after another, so a hex
vacated during Movement 2 is not available to a Unit that wanted to enter it in
that same Phase unless the movement rules say otherwise.

### Ordering within a Phase

When two effects in the same Phase genuinely cannot be simultaneous — one
creates the condition the other consumes — resolve them in this order:

1. Effects that remove a Unit from the table.
2. Effects that change a Unit's Speed or position.
3. Everything else.

## The three Movement Phases

Movement is split across three Phases rather than taken as one long move. A
Unit's Speed decides what it may do in each: a **still** Unit holds position, a
**slow** Unit takes the cautious order, and a **fast** Unit commits to the full
distance and gives up its options for the rest of the Round.

Because Gunnery 1 lands before any Movement Phase and Gunnery 2 after all three,
a Unit that sprints across open ground is exposed to fire on both sides of the
run.

### Changing Speed mid-Round

A Unit that brakes or accelerates between Movement Phases uses the order for the
Speed it holds **at that Phase**, read from the same Order Card it started the
Round with. Where the card lists nothing for the new Speed, the Unit does
nothing that Phase.

## Ending the battle

The scenario names the end condition — most often a fixed span of time. Finish
the Round in progress, then resolve one final **end sequence**: repeat Agony 0
through Agony 4 for every Unit until each Unit either has no continuing damage
left or is destroyed. Units with healing or repair abilities may apply them
between those Agony Phases, exactly as they would in a normal Round.

Only then count up the Victory Conditions.
