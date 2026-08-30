# Showcase Ogre Hydra — ogre — 576 points

*v1999.12.0*

## Ogre Hydra

- Size: Huge
- Models: 1x Ogre Hydra, 2x Ogre Hydra Crew
- Type: Bio
- Points: 112
- Shaken: slow [-, -, flee] / Can't use weapons

- **Regeneration**: Heal[N, self, 2nd Healing], where N is one per minor head plus 4 for the major head. (N is 10 when all minor heads are alive). Instead of Healing normal effect, you may use 4 points to heal a destroyed head
- **Heads**: 1 major head, 6 minor head. Keep track of number of alive minor heads at any time, Poison spits, regeneration and assault is dependent on the number of alive heads.
- **Fire Order**: Breath weapon and poison spit always treated as loaded and used with Fire(H) orders. Crew weapons are used with Load(crew) and Fire(crew) orders
- **Forward Position**: [1]

**Damage Table: Regular**

| Roll | Effect |
| ---- | ------ |
| 1-2 | Bleed[4] |
| 3-5 | +1 to future damage, Bleed[4] |
| 6-10 | +1 to future damage, Bleed[6], destroy one minor head. If all minor heads are destroyed, add additional +3 to future damage instead. Amplify all bleeding one step. (4 to 6, 6 to 8, 8 to 10 and 10 to 12) |
| 10-17 | As below, d6 Psychic damage |
| 18 | Unit destroyed |
- Bleed does not cause more bleeding

**Damage Table: Psychic**

| Roll | Effect |
| ---- | ------ |
| 6+ | shaken |


### Ogre Hydra

- Equipment: 1x Acid Breath, 1x Poison Spit
- Assault: strength 6/6/6/6 (5+), deflection 6/2/2/2 (5+), damage d6, AP 2


- **Bonus**: +3 assault strength  and +1 assault deflection per alive head
- **Assault Extra Damage**: Poison[6][1 for 2]
- **Fear**: [d6]

#### Acid Breath

- Range: 2, angle True/True/False/False, damage -, AP N/A
- **Range Extra Damage**: Acid. Choose one hex within normal range. Automatically consider all units in the hex hit. Give all units in the hex acid if it is at point blank range, and minor acid otherwise.; Minor Acid

#### Poison Spit

- Range: 2, angle True/True/False/False, damage -, AP N/A
- **Range Extra Damage**: Poison[6]
- **Multiple Shots**: Fire one time per alive minor head


### Ogre Hydra Crew

- Equipment: 1x Ogre Rifle
- Assault: strength 0/0/0/0 (5+), deflection 0/0/0/0 (5+), damage -, AP N/A

- **To Hit**: Good Shot


#### Ogre Rifle

- Range: 4, angle True/True/True/True, damage d8-2, AP 2


---

## Ogre Infantry (5×)

- Size: Large
- Models: 2x Ogre Infantry
- Type: Bio, Infantry, Walking
- Points: 32
- Shaken: slow [-, -, Flee] / Can't use weapons

- **To Hit**: Take Cover[Still][-1]

**Damage Table: Regular**

| Roll | Effect |
| ---- | ------ |
| 2-3 | Bleed[4] |
| 4-6 | Kill 1 model |
| 7-10 | Kill 1 model, Psychic damage[d6] |
| 11+ | Unit destroyed |
- If one model is killed remove half of the +1 future damage tokens and if killed by bleeding/poison, remove that bleeding/poison token

**Damage Table: Psychic**

| Roll | Effect |
| ---- | ------ |
| 6+ | shaken |


### Ogre Infantry

- Equipment: 1x Fancy Arquebus
- Assault: strength 3/2/1/1 (5+), deflection 1/0/0/0 (5+), damage d8, AP 2



#### Fancy Arquebus

- Range: 3, angle True/True/True/True, damage d8+2, AP 4


---

## Ogre Robot

- Size: Medium
- Models: 2x Ogre Robot
- Type: Bio, Mechanical, Infantry, Walking
- Armor: 3/3/0/0
- Points: 16
- Shaken: slow [-, -, Flee] / Can't use weapons

- **To Hit**: Take Cover[Still][-2]

**Damage Table: Regular**

| Roll | Effect |
| ---- | ------ |
| 2-3 | +1 to future damage |
| 4-6 | +2 to future damage |
| 7-10 | Kill 1 model |
| 11+ | Unit destroyed |
- remove half of the +1 future damage tokens when one robots dies


### Ogre Robot

- Equipment: 1x Ogre Rifle
- Assault: strength 1/1/1/1 (5+), deflection 1/0/0/0 (5+), damage d6-2, AP 2



#### Ogre Rifle

- Range: 4, angle True/True/True/True, damage d8-2, AP 2


---

## Main Engine

- Size: Huge
- Models: 1x Main Engine
- Type: Mechanical, Tracked, Drone, Carrier
- Armor: 12/10/10/8
- Points: 96
- Shaken: slow [-, -, -] / Can't use weapons

- **LoS**: Blocks Line of Sight
- **Tow**: May tow one wagon. Towed wagon always faces the main engine, and when the engine leaves its hex, the towed wagon enters the hex the engine exited, and conduct assault if necessary.
- **Transport**: May carry up to 6 tiny drone units. Treat all 3rd movement steps as including an optional + deploy(range=2) order. May not be deployed into assault

**Damage Table: Critical**

| Roll | Effect |
| ---- | ------ |
| 1-3 | +3 to future damage |
| 4 | Cannot rotate |
| 5 | Cannot move |
| 6 | set on Fire |

**Damage Table: Regular**

| Roll | Effect |
| ---- | ------ |
| 1-3 | +1 on future damage |
| 4 | as below, shaken |
| 5-8 | Critical damage[d6], +1 on future damage |
| 9+ | Destroyed |

**Damage Table: Crew**

| Roll | Effect |
| ---- | ------ |
| 4-5 | Crippled Crew, if already shaken double initial Crew damage |
| 6-7 | as 4-5, shaken |
| 8-12 | as 6-7, +3 to future Crew damage |
| 13 | Unit destroyed |


### Main Engine

- Equipment: 1x Ogre Cannon
- Assault: strength 6/6/3/0 (5+), deflection 9/6/3/0 (5+), damage d8, AP 3


- **Retreat**: If after all assault any wagon cannot enter the hex it should, the wagon is disconnected from this unit and cannot move. If a wagon which cannot move is forced to retreat, the unit is destroyed instead

#### Ogre Cannon

- Range: 3, angle True/False/False/False, damage d8 (+2 if penetrating all armor), AP 5


---

## Artillery Wagon (2×)

- Size: Large
- Models: 1x Artillery Wagon
- Type: Mechanical, Drone, Towed
- Armor: 2/10/10/8
- Points: 96
- Shaken: still [-, -, -] / Can't use weapons

- **Tow**: Must be towed by an main engine, or an other wagon which is connected to a main engine to move. If so, this unit is considered to be connected with a main engine. It has the same speed as the main engine if towed if connected, else it is still. A Towed wagon always faces the unit which tows it, and when the unit leaves its hex, the towed wagon enters the hex the other unit exited. Conduct assault if necessary.
- **Fire Order**: May not Aim without firing, and may only aim if a scout has line of sight to target (ie you must spend one ammo to get aim bonuses) You only get aim bonuses versus the same target unit. You retain aim while loading

**Damage Table: Critical**

| Roll | Effect |
| ---- | ------ |
| 1-5 | +3 to future damage |
| 6 | set on Fire |

**Damage Table: Regular**

| Roll | Effect |
| ---- | ------ |
| 1-3 | +1 on future damage |
| 4 | as below, shaken |
| 5-8 | Critical damage[d6], +1 on future damage |
| 9+ | Destroyed |

**Damage Table: Crew**

| Roll | Effect |
| ---- | ------ |
| 4-5 | Crippled Crew, if already shaken double initial Crew damage |
| 6-7 | as 4-5, shaken |
| 8-12 | as 6-7, +3 to future Crew damage |
| 13 | Unit destroyed |


### Artillery Wagon

- Equipment: 1x Ogre Artillery
- Assault: strength 6/6/6/3 (5+), deflection 6/6/6/3 (5+), damage d8, AP 3

- **To Hit**: Need Command; Good Shot. Applies while a scout has line of sight to the target

- **Retreat**: If after all assault any wagon cannot enter the hex it should, the wagon is disconnected from this unit and cannot move. If a wagon which cannot move is forced to retreat, the unit is destroyed instead

#### Ogre Artillery

- Range: 5, angle True/True/True/True, damage d8 (+3 if penetrating all armor), AP 6
- **Area**: If you hit enemy, in addition to regular damage, Area[5+], AP=4, damage=d8 in the target hex
- **Indirect Fire**: May use line of sight of any scout instead of its own.


---
