# PROTOTYPE D: one Continuing Damage overview table

> Throwaway prototype for "How a token's damage table reads" (#240). Not
> rulebook text. Rule Links print as plain labels.
>
> **Shape:** the radical option. The threshold tokens share one shape, so they
> share one table, in Agony order. The rider and per-token notes sit under it.
> Only Acid, the one real multi-row table, keeps its own table. Each token
> entry below then holds just its Phases and a pointer.
> **Poison:** a row with `—` in the "Removed on" column.
> **Cost:** this no longer has the unit-card shape that "same row grammar as
> unit damage tables" (#238) aimed for: a row here is a token, not a roll.

---

## Tokens

*(… intro and Shaken through Cannot Turn unchanged …)*

### Continuing Damage

Each Agony Phase, every token of that Phase rolls its die. On a low roll it is
removed. Otherwise it has its effect.

| Phase   | Token       | Roll                     | Removed on | Otherwise                                         |
| ------- | ----------- | ------------------------ | ---------- | ------------------------------------------------- |
| Agony 0 | Acid        | d8                       | —          | Roll on the Acid table (below)                    |
| Agony 1 | Minor Acid  | d6                       | 1-2        | +1 to future damage                               |
| Agony 2 | Fire        | d6 − fire resistance     | 2 or less  | Deal the roll as damage                           |
| Agony 3 | Poison[N]   | dN − poison resistance   | —          | Deal the roll as damage, then downgrade one step  |
| Agony 4 | Bleed[N]    | dN                       | 1-2        | Deal the roll as damage                           |

Damage dealt by Fire, Poison and Bleed:

- ignores Armor and regular damage resistance,
- adds the Unit's Future Damage, and
- goes to the Regular damage table.

Notes:

- **Fire:** roll for every Fire on the Unit before any of them deals damage.
- **Poison and Bleed:** if the damage killed a Model, remove that token
  instead of downgrading it.
- **Poison:** downgrading steps Poison[12] → Poison[10] → … → Poison[4] →
  removed.
- **Bleed:** Bleed never places a new Bleed. If its damage would place
  Bleed[M], Raise the rolling Bleed to Bleed[M] instead, if M is larger.

**Acid table**

| d8  | Effect                                                                              |
| --- | ----------------------------------------------------------------------------------- |
| 1   | Downgrade this Acid to Minor Acid                                                   |
| 2   | +1 to future damage                                                                 |
| 3   | As 2, and reduce Armor by 1 in all directions                                       |
| 4   | As 3, and place Poison Cloud[4] in this hex; every Unit in this hex gets Minor Acid |
| 5   | As 4, and every Unit within range 2 gets Minor Acid                                 |
| 6   | As 5, and Terror                                                                    |
| 7   | As 6, and Fire                                                                      |
| 8   | Roll three times on this table                                                      |

### Minor Acid

See Continuing Damage. **Phases:** Agony 1

### Fire

See Continuing Damage. **Phases:** Agony 2

### Acid

See Continuing Damage. **Phases:** Agony 0

### Poison [{N}]

See Continuing Damage. **Phases:** Agony 3 · **N:** one of 4, 6, 8, 10, 12

### Bleed [{N}]

See Continuing Damage. **Phases:** Agony 4 · **N:** one of 4, 6, 8, 10, 12
