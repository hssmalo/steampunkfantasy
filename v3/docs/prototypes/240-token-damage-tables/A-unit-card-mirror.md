# PROTOTYPE A: written like a unit card, rider repeated per token

> Throwaway prototype for "How a token's damage table reads" (#240). Not
> rulebook text. Rule Links print as plain labels.
>
> **Shape:** each token gets a die line, then a `Roll | Effect` table exactly
> like a unit's Damage Table, then notes. The Continuing Damage rider is
> repeated as notes under every token that deals damage.
> **Poison:** a table with a single `Any` row and a "Then" note.

---

## Tokens

When placing Aim or Shaken on a unit for the first time, place two tokens of
the given type. Otherwise, place only one.

No other token is placed this way. Confused in particular is an exception: it
works differently, and this rule does not cover it.

Follow the instructions for each token.

*(… Shaken through Cannot Turn unchanged …)*

### Minor Acid

Roll a d6.

**Damage Table: Minor Acid**

| Roll | Effect                     |
| ---- | -------------------------- |
| 1-2  | Remove this Minor Acid     |
| 3+   | +1 to future damage        |

**Phases:** Agony 1

**Removed:** Only as part of effect

### Fire

Roll a d6, less the Unit's fire resistance.

**Damage Table: Fire**

| Roll      | Effect                          |
| --------- | ------------------------------- |
| 2 or less | Remove this Fire                |
| 3+        | Deal the roll as Regular damage |

- Fire damage ignores Armor and regular damage resistance.
- Add the Unit's Future Damage to the roll.
- Roll for every Fire on the Unit before any of them deals damage.

**Phases:** Agony 2

**Removed:** Only as part of effect

### Acid

Roll a d8.

**Damage Table: Acid**

| Roll | Effect                                                                                     |
| ---- | ------------------------------------------------------------------------------------------ |
| 1    | Downgrade this Acid to Minor Acid                                                          |
| 2    | +1 to future damage                                                                        |
| 3    | As 2, and reduce the Unit's Armor by 1 in all directions                                   |
| 4    | As 3, and place Poison Cloud[4] in the Unit's hex; every Unit in that hex gets Minor Acid  |
| 5    | As 4, and every Unit within range 2 gets Minor Acid                                        |
| 6    | As 5, and the Unit gets Terror                                                             |
| 7    | As 6, and the Unit gets Fire                                                               |
| 8    | Roll three times on this table                                                             |

**Phases:** Agony 0

**Removed:** Downgraded as part of effect

### Terror

Acts as if unit has Terror[6] (range=2) but effects only units of the same team

**Phases:** Agony 0

### Poison [{N}]

Roll a d{N}, less the Unit's poison resistance.

**Damage Table: Poison**

| Roll | Effect                          |
| ---- | ------------------------------- |
| Any  | Deal the roll as Regular damage |

- Poison damage ignores Armor and regular damage resistance.
- Add the Unit's Future Damage to the roll.
- If this damage killed a Model, remove this Poison.
- Then, if this Poison is still here, downgrade it one step: Poison[12] →
  Poison[10] → … → Poison[4] → removed.

**Phases:** Agony 3

**Removed:** Downgraded as part of effect

**N:** one of 4, 6, 8, 10, 12

### Horrifying Poison

*(unchanged)*

### Bleed [{N}]

Roll a d{N}.

**Damage Table: Bleed**

| Roll | Effect                          |
| ---- | ------------------------------- |
| 1-2  | Remove this Bleed               |
| 3+   | Deal the roll as Regular damage |

- Bleed damage ignores Armor and regular damage resistance.
- Add the Unit's Future Damage to the roll.
- If this damage killed a Model, remove this Bleed.
- Bleed never places a new Bleed. If this damage would place Bleed[M], Raise
  this Bleed to Bleed[M] instead, if M is larger.

**Phases:** Agony 4

**N:** one of 4, 6, 8, 10, 12
