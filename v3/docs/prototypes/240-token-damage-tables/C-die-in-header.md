# PROTOTYPE C: die in the table header, rider written once

> Throwaway prototype for "How a token's damage table reads" (#240). Not
> rulebook text. Rule Links print as plain labels.
>
> **Shape:** like B, but the die and resistance go into the first column's
> header (`d6 − fire resistance`) instead of a line above the table. Notes
> follow the table, as on unit cards.
> **Poison:** a table with one `Any` row; the step-down is a note.

---

## Tokens

*(… intro and Shaken through Cannot Turn unchanged …)*

### Continuing Damage

Fire, Poison and Bleed are **Continuing Damage**. When one of them deals
damage it ignores Armor and regular damage resistance, the Unit's Future Damage
is added, and it goes to the Regular damage table.

### Minor Acid

| d6  | Effect                 |
| --- | ---------------------- |
| 1-2 | Remove this Minor Acid |
| 3+  | +1 to future damage    |

**Phases:** Agony 1

### Fire

| d6 − fire resistance | Effect                             |
| -------------------- | ---------------------------------- |
| 2 or less            | Remove this Fire                   |
| 3+                   | Deal the roll as Continuing Damage |

- Roll for every Fire on the Unit before any of them deals damage.

**Phases:** Agony 2

### Acid

| d8  | Effect                                                                                  |
| --- | --------------------------------------------------------------------------------------- |
| 1   | Downgrade this Acid to Minor Acid                                                       |
| 2   | +1 to future damage                                                                     |
| 3   | As 2, and reduce Armor by 1 in all directions                                           |
| 4   | As 3, and place Poison Cloud[4] in this hex; every Unit in this hex gets Minor Acid     |
| 5   | As 4, and every Unit within range 2 gets Minor Acid                                     |
| 6   | As 5, and Terror                                                                        |
| 7   | As 6, and Fire                                                                          |
| 8   | Roll three times on this table                                                          |

**Phases:** Agony 0

### Terror

*(unchanged)*

### Poison [{N}]

| d{N} − poison resistance | Effect                             |
| ------------------------ | ---------------------------------- |
| Any                      | Deal the roll as Continuing Damage |

- If this damage killed a Model, remove this Poison.
- Otherwise downgrade it one step: Poison[12] → Poison[10] → … → Poison[4] →
  removed.

**Phases:** Agony 3

**N:** one of 4, 6, 8, 10, 12

### Horrifying Poison

*(unchanged)*

### Bleed [{N}]

| d{N} | Effect                             |
| ---- | ---------------------------------- |
| 1-2  | Remove this Bleed                  |
| 3+   | Deal the roll as Continuing Damage |

- If this damage killed a Model, remove this Bleed.
- Bleed never places a new Bleed. If this damage would place Bleed[M], Raise
  this Bleed to Bleed[M] instead, if M is larger.

**Phases:** Agony 4

**N:** one of 4, 6, 8, 10, 12
