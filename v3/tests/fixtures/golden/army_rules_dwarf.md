# The Rolling Wall — dwarf — 64 points

*v1999.12.0*

## Dwarf Infantry

- Size: Medium
- Models: 1x Dwarf Infantry, 3x Dwarf Infantry
- Type: Bio, Infantry, Walking
- Armor: 5/0/0/0
- Points: 24
- Shaken: slow [-, -, flee] / Can't use weapons

- **[Resistance](#rule-special-resistance)**: Poison[2]; Fire[1]
- **[To Hit](#rule-special-to-hit)**: Take Cover[Still][-2]

**Damage Table: Regular**

| Roll | Effect |
| ---- | ------ |
| 1-5 | Kill 1 model |
| 6-9 | Kill 1 model, roll d6 Psychic damage |
| 10+ | Unit killed |

**Damage Table: Psychic**

| Roll | Effect |
| ---- | ------ |
| 4+ | Unit shaken |


### Dwarf Infantry

- Equipment: 1x Musket, 1x Wheeled ShieldWall
- Assault: strength 1/1/1/1 (4+), deflection 1/0/0/0 (4+), damage d6-2, AP 2


- **[Cunning Assault](#rule-special-cunning-assault)**: [2]
- **[Penalty](#rule-special-penalty)**: -1 in assault strength if speed is not still. Don't get any armor bonus in assault

#### Musket

- Range: 3, angle True/True/True/True, damage d6-2, AP 2


### Dwarf Infantry

- Equipment: 1x Musket
- Assault: strength 1/1/1/1 (4+), deflection 0/0/0/0 (n.a.), damage d6-2, AP 2


- **[Cunning Assault](#rule-special-cunning-assault)**: [2]

#### Musket

- Range: 3, angle True/True/True/True, damage d6-2, AP 2


---

## Mini Zeppelin

- Size: Medium
- Models: 3x Mini Zeppelin
- Type: Bio, Mechanical, Floating, Open Vehicle
- Armor: 0/0/0/0
- Points: 40
- Shaken: slow [random, -, -] / Normal

- **[Resistance](#rule-special-resistance)**: Poison[3]
- **[Movement](#rule-special-movement)**: random movement: scatters one hex in a random direction first movement phase, but keep the unit orientation. If it enters an hex with an enemy unit, enter an assault (as if assaulting from enemy from front). In slow mode the unit uses its engines to neutralize the effect of the weather
- **Note**: Floats

**Damage Table: Regular**

| Roll | Effect |
| ---- | ------ |
| 2-3 | shaken |
| 4+ | kill 1 model |

**Damage Table: Psychic**

| Roll | Effect |
| ---- | ------ |
| 6+ | Unit shaken |


### Mini Zeppelin

- Equipment: 1x AxeThrower Machine, 1x Poison Gas Grenade
- Assault: strength 2/1/1/1 (4+), deflection 3/2/1/1 (4+), damage d6-2, AP 2

- **[To Hit](#rule-special-to-hit)**: Even Range

- **[Cunning Assault Defense](#rule-special-cunning-assault-defense)**: [1, 4+]

#### AxeThrower Machine

- Range: 4, angle True/True/False/False, damage d6-2, AP 2
- **[Multiple Shots](#rule-special-multiple-shots)**: Fire x2 per fire order per model

#### Poison Gas Grenade

- Range: 1, angle True/True/True/True, damage N.A, AP 0
- **[Cloud](#rule-special-cloud)**: Place a poison cloud[4] within normal range
- **[Ammo](#rule-special-ammo)**: Always treated as loaded
- **[Order](#rule-special-order)**: Activated by throw order


---



## Rules Reference

<a id="rule-token-aim"></a>
**Aim (token)** — Get +2 to hit an enemy. Only valid for units in line of sight of the hex where the aim was given. Last for only 1 round.

- *Phases:* Gunnery 1, Gunnery 2
- *Removed:* Either remove all aim tokens when you fire, or remove one each aftermath phase. Also remove all of them if you enter an assault (regardless of whether you win or not)
- *To hit:* +2
- *To be hit:* 0

<a id="rule-special-ammo"></a>
**Ammo (special)** — Describes how a weapon is loaded and how its ammo is tracked.

- *See also:* Limited Ammo (special)

<a id="rule-special-cloud"></a>
**Cloud (special)** — *Rule text pending.*

- *See also:* [Fog (hex)](#rule-hex-fog), [Poison Cloud (hex)](#rule-hex-poison-cloud)

<a id="rule-special-cunning-assault"></a>
**Cunning Assault (special)** — For each {N} assault successes assigned to one mechanical unit in assault, add +1 to all future damage tokens. If you manage to inflict two or more +1 to future damage this way, the enemy is shaken. Multiple hits from multiple models with same ability stack.

- *See also:* [Cunning Assault Defense (special)](#rule-special-cunning-assault-defense)

<a id="rule-special-cunning-assault-defense"></a>
**Cunning Assault Defense (special)** — Roll {N} dice, for each die at {M}+, the unit gets one less +1 to future damage due to cunning assault. If the number +1 to future damage caused by cunning assault is reduced to 1 or less, the unit is not schaken. This effect stack with multiple models having the same ability

- *See also:* [Cunning Assault (special)](#rule-special-cunning-assault), Cunning Deflection (special)

<a id="rule-ability-even-range"></a>
**Even Range (ability)** — Shifts the roll by the parity of the range to the target

<a id="rule-damage-type-fire"></a>
**Fire (damage type)** — *Rule text pending.*

- *See also:* [Fire (token)](#rule-token-fire)

<a id="rule-token-fire"></a>
**Fire (token)** — Role a d6 and suptracked unit fire resistance if any. If this number is 1 or below, fire is removed. Otherwise_


- Ignore armor and regular damage resistance
- Apply bonus to damage based on the number +future damage tokens
- Apply damage to the regular damage table  (apply damage after you roll damage for all fire tokens)


- *Phases:* Agony 2
- *Removed:* Only as part of effect
- *See also:* [Fire (damage type)](#rule-damage-type-fire), [Resistance (special)](#rule-special-resistance)

<a id="rule-hex-fog"></a>
**Fog (hex)** — Treat hex as if it blocks line of sight and gives to-hit penalties for units standing in fog. To Hit penalties stacks with other terrain features.

- *Removed:* Remove one Fog in each hex in aftermath phase
- *To hit:* -1
- *To be hit:* -1

<a id="rule-special-movement"></a>
**Movement (special)** — *Rule text pending.*

<a id="rule-special-multiple-shots"></a>
**Multiple Shots (special)** — *Rule text pending.*

- *See also:* Burst (special)

<a id="rule-special-order"></a>
**Order (special)** — *Rule text pending.*

<a id="rule-special-penalty"></a>
**Penalty (special)** — *Rule text pending.*

- *See also:* Bonus (special)

<a id="rule-damage-type-poison"></a>
**Poison (damage type)** — *Rule text pending.*

- *See also:* [Poison (token)](#rule-token-poison)

<a id="rule-token-poison"></a>
**Poison (token)** — Roll a d{N}.

- Ignore armor and regular damage resistances
- Reduce damage by poison resistances of target
- Apply bonus to damage based on the number +future damage tokens
- Apply damage to the regular damage table.
- If poison killed a model, remove poison.

If poison did not kill a model, downgrade poison one step

- *Phases:* Agony 3
- *See also:* [Poison (damage type)](#rule-damage-type-poison), [Resistance (special)](#rule-special-resistance)

<a id="rule-hex-poison-cloud"></a>
**Poison Cloud (hex)** — Area(5+): roll a die per unit, at 5+, target unit gets a poison[N] or take dN in crew damage if it is a vehicle with a crew damage table.

- *Removed:* Remove one Poison Cloud in each hex in aftermath phase
- *See also:* [Poison (damage type)](#rule-damage-type-poison)

<a id="rule-special-resistance"></a>
**Resistance (special)** — Gives improved resilience versus {version} damage

<a id="rule-token-shaken"></a>
**Shaken (token)** — While shaken set unit speed to the specified speed, and how a unit behaves is described by each unit. Disregard the original orders and replace them with the order(s) described by the unit

- *Phases:* Gunnery 1, Movement 1, Movement 2, Movement 3, Gunnery 2
- *Removed:* Remove one each aftermath phase. Can also be removed by appropriate repair or healing abilities
- *See also:* Heal (special), Repair (special)

<a id="rule-speed-still"></a>
**Still (speed)**

- *To hit:* +1
- *To be hit:* +1

<a id="rule-ability-take-cover"></a>
**Take Cover (ability)** — Applies when the unit is in the given speed

- *To hit:* 0
- *To be hit:* +N

<a id="rule-special-to-hit"></a>
**To Hit (special)** — Shifts the to-hit and to-be-hit rolls by {ability}.

- *See also:* [Aim (token)](#rule-token-aim)
