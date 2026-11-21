# PROTOTYPE B: rider written once, lean tables

> Throwaway prototype for "How a token's damage table reads" (#240). Not
> rulebook text. Rule Links print as plain labels.
>
> **Shape:** a short **Continuing Damage** intro holds the shared rider once.
> Each token has a die line and a `Roll | Effect` table, plus only the notes
> that belong to that token alone.
> **Poison:** stays prose (no threshold, so no table).
> **Acid:** rows spelled out in full instead of "As 2, and …".

---

## Tokens

When placing Aim or Shaken on a unit for the first time, place two tokens of
the given type. Otherwise, place only one.

No other token is placed this way. Confused in particular is an exception: it
works differently, and this rule does not cover it.

Follow the instructions for each token.

*(… Shaken through Cannot Turn unchanged …)*

### Continuing Damage

Fire, Poison and Bleed are **Continuing Damage**. When one of them deals
damage:

- it ignores Armor and regular damage resistance,
- the Unit's Future Damage is added to the roll, and
- it goes to the Regular damage table.

### Minor Acid

Roll a d6.

| Roll | Effect                 |
| ---- | ---------------------- |
| 1-2  | Remove this Minor Acid |
| 3+   | +1 to future damage    |

**Phases:** Agony 1

### Fire

Roll a d6, less the Unit's fire resistance. Roll for every Fire on the Unit
before any of them deals damage.

| Roll      | Effect                                    |
| --------- | ----------------------------------------- |
| 2 or less | Remove this Fire                          |
| 3+        | Deal the roll as Continuing Damage        |

**Phases:** Agony 2

### Acid

Roll a d8.

| Roll | Effect                                                                                                                                                   |
| ---- | -------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 1    | Downgrade this Acid to Minor Acid                                                                                                                        |
| 2    | +1 to future damage                                                                                                                                      |
| 3    | +1 to future damage, reduce Armor by 1 in all directions                                                                                                 |
| 4    | +1 to future damage, reduce Armor by 1 in all directions, place Poison Cloud[4] in this hex, every Unit in this hex gets Minor Acid                       |
| 5    | +1 to future damage, reduce Armor by 1 in all directions, place Poison Cloud[4] in this hex, every Unit within range 2 gets Minor Acid                     |
| 6    | +1 to future damage, reduce Armor by 1 in all directions, place Poison Cloud[4] in this hex, every Unit within range 2 gets Minor Acid, Terror             |
| 7    | +1 to future damage, reduce Armor by 1 in all directions, place Poison Cloud[4] in this hex, every Unit within range 2 gets Minor Acid, Terror, Fire       |
| 8    | Roll three times on this table                                                                                                                           |

**Phases:** Agony 0

### Terror

*(unchanged)*

### Poison [{N}]

Roll a d{N}, less the Unit's poison resistance, and deal it as Continuing
Damage. If that killed a Model, remove this Poison. Otherwise downgrade it one
step: Poison[12] → Poison[10] → … → Poison[4] → removed.

**Phases:** Agony 3

**N:** one of 4, 6, 8, 10, 12

### Horrifying Poison

*(unchanged)*

### Bleed [{N}]

Roll a d{N}.

| Roll | Effect                             |
| ---- | ---------------------------------- |
| 1-2  | Remove this Bleed                  |
| 3+   | Deal the roll as Continuing Damage |

- If this damage killed a Model, remove this Bleed.
- Bleed never places a new Bleed. If this damage would place Bleed[M], Raise
  this Bleed to Bleed[M] instead, if M is larger.

**Phases:** Agony 4

**N:** one of 4, 6, 8, 10, 12
