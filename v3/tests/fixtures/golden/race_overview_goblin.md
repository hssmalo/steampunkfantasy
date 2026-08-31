# Goblin

*v1999.12.0*

Goblin are small humanoid creatures, about 1m in height. Sneaky infantry, viewed as somewhat primitive but has proven to have done some surprisingly well done engineering jobs

## Contents

- [Units](#section-units)
- [Models](#section-models)
- [Equipment](#section-equipment)
- [Spawns](#section-spawns)
- [Rules Reference](#section-rules)

<a id="section-units"></a>

## Units

| Unit | Size | Models | ip | mp | xp | cp | vpm |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| [Heavy Carrier](#unit-heavy-carrier) | Large | 1 | 32 |  |  |  |  |
| [Bipedal Mech](#unit-bipedal-mech) | Large | 1 | 24 |  |  |  |  |
| [Mechanical Fire Bird](#unit-mechanical-fire-bird) | Medium | 1 | 24 |  |  |  |  |
| [Goblin Infantry Carrier](#unit-goblin-infantry-carrier) | Large | 1 | 16 |  |  |  |  |
| [Modified Truck](#unit-modified-truck) | Medium | 1 | 8 |  |  |  |  |
| [Goblin Infantry](#unit-goblin-infantry) | Small | 4 |  | 8 |  |  |  |
| [Giant Snake Cavalry](#unit-giant-snake-cavalry) | Large | 1 |  | 4 | 24 |  |  |
| [Tiny Snake](#unit-tiny-snake) | Tiny | 2 |  |  |  |  |  |

<a id="unit-heavy-carrier"></a>

### Heavy Carrier

*The two weapons system attached uses two different philosophies. The bow battery is an inaccurate weapon system but fires lots and lots of arrows with nasty side effect and are best used versus units which are easy to hit. The heavy crossbow only fires up too three arrows each time and a far more precise weapon with surprisingly large punch. In a hurry the goblin may fire weapons before all of them are loaded.*

- Cost: 32ip (96 points)
- Size: Large
- Models: [Heavy Carrier](#model-heavy-carrier)
- Type: Mechanical, Vehicle, Tracked
- Armor: 10/8/6/4
- Shaken: still [-, -, -] / Can't use weapons
- **[Transport](#rule-special-transport)**: May transport up to 1 Goblin infantry. Deploy order is Deploy(range=1). May deploy directly into assault. If Heavy Carrier enters an assault, you may optionally deploy the infantry to join the assault
- **[Forward Position](#rule-special-forward-position)**: [1]
- **[Fire Order](#rule-special-fire-order)**: Fire and load all weapons simultaneously, with identical ammo usage for all weapons

**Tip**: Slightly more armored compared to the Goblin Armored Carrier, much better armed and more flexible exit, but carries only one goblin infantry unit.

These have dual use, one is to deliver Goblin infantry closer to the enemy, anothes is to lay devastating firepower onto the enemy.

**Movement orders**

| Speed | | | |
| --- | --- | --- | --- |
| slow | L/R | (L/R) | - |
| slow | F | (L/R) | (Deploy) |
| slow | (L/R) | F | (Deploy) |
| slow | B | - | - |
| slow | A | F | - |
| slow | B | - | - |
| fast | F | F | F+(Deploy) |
| fast | F | L/R | F+(Deploy) |
| fast | L/R | F | F+(Deploy) |
| fast | F | F+(Deploy) | L/R |
| fast | F | B | - |
| still | L/R | (L/R) | (L/R) |
| still | - | - | - |
| still | (L/R) | A | F |
| still | rev | - | - |

**Fire orders**

| Speed | | |
| --- | --- | --- |
| fast | - | Fire |
| fast | - | Fire |
| slow | Load | Load |
| slow | Load | Fire |
| still | Load | Load |
| still | Load | Fire |

**Damage Table: Regular**

| Roll | Effect |
| ---- | ------ |
| 1-3 | +1 to future damage |
| 4 | As 1-3 , shaken |
| 5-8 | As 4, d6 critical damage |
| 9 | Unit destroyed |

**Damage Table: Critical**

| Roll | Effect |
| ---- | ------ |
| 1 | 1d4 damage to all transported units |
| 2 | Forced Deploy (empty hexes only) |
| 3 | +1 to be hit, -1 to hit |
| 4 | Cannot rotate |
| 5 | Unit cannot move |
| 6 | Fire |

**Damage Table: Crew**

| Roll | Effect |
| ---- | ------ |
| 4-5 | Crippled Crew, if already shaken double initial Crew damage |
| 6-7 | As 4-5, shaken |
| 8-11 | As 6-7, +3 to future Crew damage |
| 12 | Unit destroyed |

<a id="unit-bipedal-mech"></a>

### Bipedal Mech

*These are the pride of goblin innovation, the first tank which walks on two legs. Or at least, that is what the goblin claim.*

- Cost: 24ip (72 points)
- Size: Large
- Models: [Bipedal Mech](#model-bipedal-mech)
- Type: Bio Crew, Mechanical, Walking
- Armor: 8/8/8/6
- Shaken: still [-, -, -] / Can't use weapons
- **[Fire Order](#rule-special-fire-order)**: Fire and load all weapons simultaneously. Fire stinkbomb in addition to two light mortars
- **[Forward Position](#rule-special-forward-position)**: [2]

**Tip**: Do not underestimate the stinkbombs, which are great versus infantry, tanks and vehicles. Versus biological units the stinkbombs poison the enemy, scare them, cover them in acid, and if you hit you get an area effect hopefully doing the same thing over again. Versus tanks with biological crew, the crew damage can be devastating too, especially versus tanks which are already shaken. It is useless versus drones and robots. Goblin do not know what aiming is, so fire load and repeat as often as possible.

**Movement orders**

| Speed | | | |
| --- | --- | --- | --- |
| still | 360° | 360° | 360° |
| still | 360° | A | 360° |
| slow | 360° | F | 360° |
| slow | 360° | F | B |

**Fire orders**

| Speed | | |
| --- | --- | --- |
| still | Load | - |
| still | Fire | - |
| slow | Load | - |
| slow | Fire | - |

**Damage Table: Regular**

| Roll | Effect |
| ---- | ------ |
| 1-3 | +1 to future damage |
| 4 | As 1-3, shaken |
| 5-8 | As 4, d6 critical damage |
| 9 | Unit destroyed |

**Damage Table: Critical**

| Roll | Effect |
| ---- | ------ |
| 1 | Take d12 Crew damage (note, it is not shaken before the apply damage step) |
| 2 | Unit gets a minor acid token |
| 3 | +1 to be hit, -1 to hit |
| 4 | Cannot rotate |
| 5 | Unit cannot move |
| 6 | +1 to future damage and unit gets another shaken token |

**Damage Table: Crew**

| Roll | Effect |
| ---- | ------ |
| 4-5 | Crippled Crew, if already shaken double initial Crew damage |
| 6-7 | as 4-5, shaken |
| 8-11 | as 6-7, +3 to future Crew damage |
| 12 | Unit destroyed |

<a id="unit-mechanical-fire-bird"></a>

### Mechanical Fire Bird

*How the goblin manage to make this marvel of a rebuild mechanism is a mystery.*

- Cost: 24ip (72 points)
- Size: Medium
- Models: [Mechanical Fire Bird](#model-mechanical-fire-bird)
- Type: Mechanical, Flying, Drone
- Armor: 5/4/4/3
- Shaken: fast_fly [-, F, F] / Can't use weapons
- **[Phoenix](#rule-special-phoenix)**: Starts the game with one reassemble token. If temporarily destroyed in 2nd healing phase, you can use one reassemble token to become alive again. Set speed to fast_fly. If so, half (rounded down) all +1 to future damage token this unit has. If it does not have a reassemble token and is not temporarily destroyed at start of 2nd healing phase, gain one reassemble token. If, it is temporarily destroyed and has no reassemble tokens in 2nd healing phase, this unit is permanently destroyed. While temporarily destroyed, count the model as laying still with movement [-,-,-]
- **[Immunity](#rule-special-immunity)**: [Fire]

**Tip**: Try to maneuver to have as many units/models as possible within range 2 and set them on fire with you ring of fire weapon. Sooner or later you will set an enemy on fire, which if the enemy have no means of remove it, is normally devastating. It is fairly well protected, both with fast flying which makes it har to hit, some armor protects from regular muskets and rifles, while simulatiously requires a few shots to disensamble. If you get to use your reassemble token, watch the frustration in your enemy. But do not imagine it is impossible to destroy.

**Movement orders**

| Speed | | | |
| --- | --- | --- | --- |
| fast_fly | L/R+F | F | F+L/R |
| fast_fly | F | F | F |
| fast_fly | F+L/R | F+L/R | F |

**Fire orders**

| Speed | | |
| --- | --- | --- |
| fast | - | Load |
| fast | - | Fire |

**Damage Table: Regular**

| Roll | Effect |
| ---- | ------ |
| 1-3 | +1 to future damage |
| 4-5 | +2 to future damage |
| 6+ | As 4-5, temporarily destroyed |

- While temporarily destroyed, all regular damage do inner damage instead
- + to future damage does not apply to inner damage
- Note that it does not get the status temporarily destroyed before the apply damage step

**Damage Table: Inner**

| Roll | Effect |
| ---- | ------ |
| 1-5 | add one minor acid token |
| 6+ | Remove reassemble token |

<a id="unit-goblin-infantry-carrier"></a>

### Goblin Infantry Carrier

*Since Goblin infantry are smaller than the other races, you can pack more of them in the same vehicle. Once the goblin exit, they swarm the place with lots and lots of goblin infantry.*

- Cost: 16ip (48 points)
- Size: Large
- Models: [Goblin Infantry Carrier](#model-goblin-infantry-carrier)
- Type: Mechanical, Vehicle, Tracked
- Armor: 10/6/5/4
- Shaken: still [-, -, -] / Can't use weapons
- **[Transport](#rule-special-transport)**: May transport up to 3 Goblin infantry. Deploy order is Deploy(range=1). May not be deployed into assault.
- **[Forward Position](#rule-special-forward-position)**: [1]

**Tip**: Mostly used to deliver lots of goblin infantry fast to the front, however the light mortar can do some serious damage to both infantry and vehicles if you are lucky. Well armored from the front, less so from the sides and rear.

**Movement orders**

| Speed | | | |
| --- | --- | --- | --- |
| slow | L/R | (L/R) | - |
| slow | F | L/R | - |
| slow | B | - | - |
| slow | A+F | F | F+Deploy |
| slow | F | - | - |
| slow | B | - | - |
| fast | B | - | - |
| still | L/R | (L/R) | (L/R) |
| still | - | - | - |
| still | (L/R) | A | F |
| still | rev | - | - |

**Fire orders**

| Speed | | |
| --- | --- | --- |
| slow | - | Load |
| slow | - | Fire |
| still | - | Load |
| still | - | Fire |

**Damage Table: Regular**

| Roll | Effect |
| ---- | ------ |
| 1-3 | +1 to future damage |
| 4 | As 1-3, shaken |
| 5-8 | As 4, d6 critical damage |
| 9 | Unit destroyed |

**Damage Table: Critical**

| Roll | Effect |
| ---- | ------ |
| 1-2 | 1d4 damage to all transported units |
| 3 | Forced Deploy (all units, empty hexes only) |
| 4 | Cannot rotate |
| 5 | Unit cannot move |
| 6 | Fire |

**Damage Table: Crew**

| Roll | Effect |
| ---- | ------ |
| 4-5 | Crippled Crew, if already shaken double initial Crew damage |
| 6-7 | As 4-5, shaken |
| 8-11 | As 6-7, +3 to future Crew damage |
| 12 | Unit destroyed |

<a id="unit-modified-truck"></a>

### Modified Truck

- Cost: 8ip (24 points)
- Size: Medium
- Models: [Modified Truck](#model-modified-truck)
- Type: Mechanical, Vehicle, Tracked
- Armor: 4/3/2/1
- Shaken: still [-, -, -] / Can't use weapons
- **[Transport](#rule-special-transport)**: May transport up to 2 Goblin infantry. Deploy order is Deploy(range=1). May deploy directly into assault. If Modified Truck enters an assault, you may optionally deploy the infantry to join the assault
- **[Forward Position](#rule-special-forward-position)**: [1]
- **[Fire Order](#rule-special-fire-order)**: Use both auto bow and goblin grenade on each fire order

**Tip**: These are cheap vehicles, with primarily role to help you place infantry closer to the enemy, which you should do as fast as possible. Having infantry inside one of these inside the truck on round 2 and you have done something wrong.

**Movement orders**

| Speed | | | |
| --- | --- | --- | --- |
| slow | L/R | (L/R) | - |
| slow | F | L/R | (Deploy) |
| slow | L/R | F | (Deploy) |
| slow | B | - | - |
| slow | (A) | F | - |
| slow | B | - | - |
| fast | F+(L/R) | F | (Deploy) |
| fast | F | F | F |
| fast | L/R | F | F+(Deploy) |
| fast | F | F+(Deploy) | L/R |
| fast | F | B | - |
| still | L/R | (L/R) | (L/R) |
| still | - | - | - |
| still | (L/R) | A | F |
| still | rev | - | - |

**Fire orders**

| Speed | | |
| --- | --- | --- |
| fast | Fire | Fire |
| slow | Fire | Fire |
| still | Fire | Fire |

**Damage Table: Regular**

| Roll | Effect |
| ---- | ------ |
| 1-2 | +1 to future damage |
| 3 | As 1-2, shaken |
| 4-7 | As 3, d6 critical damage |
| 8 | Unit destroyed |

**Damage Table: Critical**

| Roll | Effect |
| ---- | ------ |
| 1 | 1d4 damage to all transported units |
| 2 | Forced Deploy (empty hexes only) |
| 3 | +1 to be hit, -1 to hit |
| 4 | Cannot rotate |
| 5-6 | Unit cannot move |

**Damage Table: Crew**

| Roll | Effect |
| ---- | ------ |
| 3-4 | Crippled Crew, if already shaken double initial Crew damage |
| 5-6 | As 4-5, shaken |
| 7-9 | As 6-7, +3 to future Crew damage |
| 10 | Unit destroyed |

<a id="unit-goblin-infantry"></a>

### Goblin Infantry

*They are viewed as somewhat primitive by the standards of other races, and they are easily underestimated, until the Goblin infantry swarm you.*

- Cost: 8mp (8 points)
- Size: Small
- Models: [Goblin Infantry](#model-goblin-infantry)
- Type: Bio, Infantry, Walking
- Shaken: slow [-, -, Flee] / Can't use weapons
- **[To Hit](#rule-special-to-hit)**: Take Cover[Sneak][-2]
- **[Fire Order](#rule-special-fire-order)**: You may either fire a regular arrow, a special arrow (arrow with limited ammo) or use one thrown weapon with each fire order.
- **[Evasion](#rule-special-evasion)**: [4+]

**Tip**: These are cheap and durable infantry which you may use to swarm the enemy. And especially with some upgrades and support, goblin infantry can be deadly. Consider if you want to combine these units with some motorized transport. In game terms you do want to come close and personal to the enemy, but avoid assaults. Luckily they are hard to hit and can evade incoming bombs.

**Movement orders**

| Speed | | | |
| --- | --- | --- | --- |
| sneak | 360° | 360° | 360° |
| sneak | 360° | F | 360° |
| slow | 360° | F | B |

**Fire orders**

| Speed | | |
| --- | --- | --- |
| sneak | Fire | Fire |

**Damage Table: Regular**

| Roll | Effect |
| ---- | ------ |
| 0-5 | Kill 1 model |
| 6-7 | Kill 1 model, Psychic damage[d6] |
| 8+ | Unit destroyed |

- If one model is killed remove half of the +1 future damage tokens and if killed by bleeding/poison, remove that bleeding/poison token

**Damage Table: Psychic**

| Roll | Effect |
| ---- | ------ |
| 4+ | shaken |

<a id="unit-giant-snake-cavalry"></a>

### Giant Snake Cavalry

*A terrifying view for all enemies, which the goblin enjoys a lot since it is an unusual that any goblin in clear sight are scary.*

- Cost: 4mp 24xp (28 points)
- Size: Large
- Models: [Giant Snake Cavalry](#model-giant-snake-cavalry)
- Type: Bio, Cavalry, Walking
- Shaken: slow [-, -, Flee] / Can't use weapons
- **[Fire Order](#rule-special-fire-order)**: You may fire two regular poison bow and use hallucinating poison spit once per fire order
- **[Forward Position](#rule-special-forward-position)**: [1]
- **[Terror](#rule-special-terror)**: [range=1][d6]
- **[Hypnotizing Gaze](#rule-special-hypnotizing-gaze)**: [range=1]
- **[Spawn](#rule-special-spawn)**: tiny_snake: At start of battle, place a hidden tiny snake in the same hex as the Snake Cavalry
- Places: [tiny_snake](#spawn-tiny-snake)

**Tip**: Decent endurance, decent in assault with an devastating poison if they hit, and not to expensive. However their low speed, combined with low range limits the usefulness. The large number of tiny snakes are the real power of this unit.

**Movement orders**

| Speed | | | |
| --- | --- | --- | --- |
| still | 360° | 360° | 360° |
| still | 360° | A | F |
| slow | 360° | F | 360° |
| slow | 360° | B | - |
| slow | 360° | Chs | - |

**Fire orders**

| Speed | | |
| --- | --- | --- |
| still | Fire | Fire |

**Damage Table: Regular**

| Roll | Effect |
| ---- | ------ |
| 1-6 | Bleed[8] |
| 7-8 | +1 to future damage, Bleed[8] |
| 9+ | Unit destroyed |

- Bleeding does not cause more bleeding

**Damage Table: Psychic**

| Roll | Effect |
| ---- | ------ |
| 6+ | shaken |

<a id="unit-tiny-snake"></a>

### Tiny Snake

- Size: Tiny
- Models: [Tiny Snake](#model-tiny-snake)
- Type: Bio, Walking, Monster
- Shaken: slow [-, -, Flee] / Can't use weapons
- Placed by: [tiny_snake](#spawn-tiny-snake)
- **[Hidden](#rule-special-hidden)**: Start with a hidden token
- **[Terror](#rule-special-terror)**: [range=1][d4]

**Movement orders**

| Speed | | | |
| --- | --- | --- | --- |
| slow | - | - | Chs |
| slow | - | - | Reveal |
| slow | Follow | Follow | Follow |

**Fire orders**

| Speed | |
| --- | --- |

**Damage Table: Regular**

| Roll | Effect |
| ---- | ------ |
| 0-3 | kill one model |
| 4+ | unit destroyed |

**Damage Table: Psychic**

| Roll | Effect |
| ---- | ------ |
| 2+ | shaken |

<a id="section-models"></a>

## Models

| Model | Type | Equipment slots | Cost |
| --- | --- | --- | --- |
| [Elite Goblin Infantry](#model-elite-goblin-infantry) | Elite, Bio, Infantry, Walking | Hands 2, Grenades 2, Specialization 1 | 4xp |
| [Goblin Infantry](#model-goblin-infantry) | Bio, Infantry, Walking | Hands 2, Grenades 3, Specialization 1, Special Arrows 3 |  |
| [Giant Snake Cavalry](#model-giant-snake-cavalry) | Bio, Cavalry, Walking | Hands 2 |  |
| [Tiny Snake](#model-tiny-snake) | Bio, Walking, Monster | — |  |
| [Bipedal Mech](#model-bipedal-mech) | Bio Crew, Mechanical, Walking | — |  |
| [Goblin Infantry Carrier](#model-goblin-infantry-carrier) | Mechanical, Vehicle, Tracked | — |  |
| [Heavy Carrier](#model-heavy-carrier) | Mechanical, Vehicle, Tracked | — |  |
| [Modified Truck](#model-modified-truck) | Mechanical, Vehicle, Tracked | — |  |
| [Mechanical Fire Bird](#model-mechanical-fire-bird) | Mechanical, Flying, Drone | — |  |

<a id="model-elite-goblin-infantry"></a>

### Elite Goblin Infantry

- Cost: 4xp (4 points)
- Assault: strength 2/1/1/1 (6+), deflection 4/0/0/0 (6+), damage d4-2, AP 2
- Type: Elite, Bio, Infantry, Walking
- Upgrades from: [Goblin Infantry](#model-goblin-infantry)
- May carry: [Goblin Bow](#equipment-goblin-bow), [Goblin Grenade](#equipment-goblin-grenade)
- *Grants its Unit:*
    - **[Resistance](#rule-special-resistance)**: Psychic[1]. As long as at least one elite model is alive
    - **[Pre-Assault Retreat](#rule-special-pre-assault-retreat)**: [6+]. Improved by 1 per elite in unit
- **[To Hit](#rule-special-to-hit)**: Thrown Weapons[2]
- *In assault:*
    - **[Cunning Assault](#rule-special-cunning-assault)**: [1]

| Holder | Slots |
| --- | ---: |
| Independent | ∞ |
| Hands | 2 |
| Grenades | 2 |
| Specialization | 1 |

<a id="model-goblin-infantry"></a>

### Goblin Infantry

- Assault: strength 1/1/1/1 (6+), deflection 0/0/0/0 (6+), damage d6-2, AP 2
- Type: Bio, Infantry, Walking
- Fielded in: [Goblin Infantry](#unit-goblin-infantry)
- Upgraded by: [Elite Goblin Infantry](#model-elite-goblin-infantry)
- May carry: [Goblin Bow](#equipment-goblin-bow), [Goblin Grenade](#equipment-goblin-grenade)
- *Grants its Unit:*
    - **[Pre-Assault Retreat](#rule-special-pre-assault-retreat)**: [6+]
- *In assault:*
    - **[Cunning Assault](#rule-special-cunning-assault)**: [1]

| Holder | Slots |
| --- | ---: |
| Independent | ∞ |
| Hands | 2 |
| Grenades | 3 |
| Specialization | 1 |
| Special Arrows | 3 |

<a id="model-giant-snake-cavalry"></a>

### Giant Snake Cavalry

- Assault: strength 24/18/12/6 (6+), deflection 0/0/0/0 (6+), damage d6-2, AP 2
- Type: Bio, Cavalry, Walking
- Fielded in: [Giant Snake Cavalry](#unit-giant-snake-cavalry)
- May carry: [Poison Bow](#equipment-poison-bow-free), [Hallucinating Poison Spit](#equipment-hallucinating-poison-spit)
- *In assault:*
    - **[Assault Extra Damage](#rule-special-assault-extra-damage)**: Poison[8][1 for 2]

| Holder | Slots |
| --- | ---: |
| Independent | ∞ |
| Hands | 2 |

<a id="model-tiny-snake"></a>

### Tiny Snake

- Assault: strength 4/1/1/1 (6+), deflection 0/0/0/0 (6+), damage d4-2, AP 0
- Type: Bio, Walking, Monster
- Fielded in: [Tiny Snake](#unit-tiny-snake)
- *In assault:*
    - **[Assault Extra Damage](#rule-special-assault-extra-damage)**: Poison[6][1 for 1]
    - **[Boost](#rule-special-boost)**: If you have reveal bonuses in assault, in addition to regular reveal bonuses, the enemy may not use assault deflection to remove hits from this unit. In addition each assault hit counts as 2 assault deflection

<a id="model-bipedal-mech"></a>

### Bipedal Mech

- Assault: strength 12/12/12/1 (6+), deflection 12/12/12/1 (6+), damage d6, AP 3
- Type: Bio Crew, Mechanical, Walking
- Fielded in: [Bipedal Mech](#unit-bipedal-mech)
- May carry: [StinkBomb](#equipment-stinkbomb), [Light Mortar](#equipment-light-mortar)

| Holder | Slots |
| --- | ---: |
| Independent | ∞ |

<a id="model-goblin-infantry-carrier"></a>

### Goblin Infantry Carrier

- Assault: strength 12/1/1/1 (6+), deflection 12/0/0/0 (6+), damage d4-2, AP 2
- Type: Mechanical, Vehicle, Tracked
- Fielded in: [Goblin Infantry Carrier](#unit-goblin-infantry-carrier)
- May carry: [Light Mortar](#equipment-light-mortar)

| Holder | Slots |
| --- | ---: |
| Independent | ∞ |

<a id="model-heavy-carrier"></a>

### Heavy Carrier

- Assault: strength 16/8/1/1 (6+), deflection 16/0/0/0 (6+), damage d6-2, AP 2
- Type: Mechanical, Vehicle, Tracked
- Fielded in: [Heavy Carrier](#unit-heavy-carrier)
- May carry: [Goblin Bow Battery](#equipment-goblin-bow-battery), [Heavy Crossbow](#equipment-heavy-crossbow)

| Holder | Slots |
| --- | ---: |
| Independent | ∞ |

<a id="model-modified-truck"></a>

### Modified Truck

- Assault: strength 8/4/1/1 (6+), deflection 8/0/0/0 (6+), damage d6-2, AP 2
- Type: Mechanical, Vehicle, Tracked
- Fielded in: [Modified Truck](#unit-modified-truck)
- May carry: [Goblin Auto Bow](#equipment-goblin-auto-bow), [Goblin Grenade](#equipment-goblin-grenade-free)

| Holder | Slots |
| --- | ---: |
| Independent | ∞ |

<a id="model-mechanical-fire-bird"></a>

### Mechanical Fire Bird

- Assault: strength 6/4/1/1 (6+), deflection 16/0/0/0 (6+), damage d6-2, AP 1
- Type: Mechanical, Flying, Drone
- Fielded in: [Mechanical Fire Bird](#unit-mechanical-fire-bird)
- May carry: [Ring of Fire](#equipment-ring-of-fire)
- *In assault:*
    - **[Assault Extra Damage](#rule-special-assault-extra-damage)**: Fire

| Holder | Slots |
| --- | ---: |
| Independent | ∞ |

<a id="section-equipment"></a>

## Equipment

| Equipment | Profile | Cost |
| --- | --- | --- |
| [Commando](#equipment-commando) | Deflection: +4/0/0/0; Deflection die: set to 6+ | 32xp |
| [Grenadier](#equipment-grenadier) | — | 8xp |
| [Archer Specialization](#equipment-archer-specialization) | — | 8xp |
| [Assault Archer](#equipment-assault-archer) | — | 8xp |
| [Clockwork Wings](#equipment-clockwork-wings) | Strength: +1/0/0/0 | 24cp |
| [Seeker Assassin Arrows](#equipment-seeker-assassin-arrows) | range 4, damage d4-2, AP 1 | 16cp |
| [Poison Bow](#equipment-poison-bow) | range 2, damage d4-2 + d4 Crew damage, AP 1 | 16cp |
| [Acid Trap](#equipment-acid-trap) | — | 16cp |
| [Seeker Arrows](#equipment-seeker-arrows) | range 4, damage d4-2, AP 1 | 8cp |
| [Gear Bow](#equipment-gear-bow) | range 3, damage d4-2, AP 1 | 8cp |
| [Ogre Rifle](#equipment-ogre-rifle) | range 2, damage d8-2, AP 2 | 8cp |
| [Poison Deflection Dagger](#equipment-poison-deflection-dagger) | Deflection: +1/0/0/0; Deflection die: set to 6+ | 8cp |
| [Combat Screw Driver](#equipment-combat-screw-driver) | Deflection: +1/0/0/0; Deflection die: set to 6+ | 8cp |
| [Acid Grenade](#equipment-acid-grenade) | range 1, damage n.a., AP 0 | 8cp |
| [Poison Grenade](#equipment-poison-grenade) | range 1, damage d4 Crew damage, AP 0 | 8cp |
| [Goblin Bow](#equipment-goblin-bow) | range 2, damage d4-2, AP 1 |  |
| [Seeker Assassin Arrows](#equipment-seeker-assassin-arrows-free) | range 4, damage d4-2, AP 1 |  |
| [Poison Bow](#equipment-poison-bow-free) | range 2, damage d4-2 + d4 Crew damage, AP 1 |  |
| [Hallucinating Poison Spit](#equipment-hallucinating-poison-spit) | range 3, damage N/A, AP N/A |  |
| [Goblin Grenade](#equipment-goblin-grenade) | range 1, damage d6, AP 2 |  |
| [Goblin Grenade](#equipment-goblin-grenade-free) | range 1, damage d6, AP 2 |  |
| [Goblin Auto Bow](#equipment-goblin-auto-bow) | range 2, damage d4-2, AP 1 |  |
| [Light Mortar](#equipment-light-mortar) | range 3, damage d4 Crew damage, AP N/A |  |
| [Goblin Bow Battery](#equipment-goblin-bow-battery) | range 2, damage d4 -2, AP 2 |  |
| [Heavy Crossbow](#equipment-heavy-crossbow) | range 4, damage d6, AP 4 |  |
| [StinkBomb](#equipment-stinkbomb) | range 4, damage d6 Psychic damage + d6 Crew damage, AP N/A |  |
| [Ring of Fire](#equipment-ring-of-fire) | range 2, damage n.a, AP 0 |  |

<a id="equipment-commando"></a>

### Commando

- Cost: 32xp per Unit
- *Requires all of:*
    - 1 Specialization
    - Model type Infantry
- *In assault:*
    - Deflection: +4/0/0/0
    - Deflection die: set to 6+
- *Grants its Unit:*
    - **[To Hit](#rule-special-to-hit)**: Take Cover[Still][-4]
    - **[Evasion](#rule-special-evasion)**: [2+]
    - **[Hidden](#rule-special-hidden)**: Start with a Hidden token.
    - **[Forward Position](#rule-special-forward-position)**: [2]
    - **[Fire Order](#rule-special-fire-order)**: In any round you have reveal bonus, you may fire a bow three times (either a regular arrow or an special arrow each time) at one target or throw three grenades at one target

**Movement orders granted**

| Speed | | | |
| --- | --- | --- | --- |
| still | - | - | Reveal |
| still | 360° | F | Reveal |
| still | Hide[ruins, forest] | - | - |

<a id="equipment-grenadier"></a>

### Grenadier

- Cost: 8xp per Unit
- *Requires all of:*
    - 1 Specialization
    - Model type Infantry or Cavalry
- *Grants its Unit:*
    - **[Fire Order](#rule-special-fire-order)**: For each fire order: fire a bow once (either a regular or special arrow) and in addition each regular infantry may use one thrown weapon while elite infantry may use 2 thrown weapons (or the same twice)
- *Grants its Model:*
    - **[To Hit](#rule-special-to-hit)**: Thrown Weapons[1]

<a id="equipment-archer-specialization"></a>

### Archer Specialization

- Cost: 8xp per Unit
- *Requires all of:*
    - 1 Specialization
    - Model type Infantry or Cavalry
- *Grants its Unit:*
    - **[Fire Order](#rule-special-fire-order)**: For each fire order: either fire a bow twice (either a regular arrow or a special arrow each time) or use one thrown weapon
- *Grants its Model:*
    - **[To Hit](#rule-special-to-hit)**: Good Shot

<a id="equipment-assault-archer"></a>

### Assault Archer

- Cost: 8xp per Unit
- *Requires all of:*
    - 2 Hands
    - Model type Archer
- *In assault:*
    - **[Retreat](#rule-special-retreat)**: Unit gains aim if you manage to pre-escape an assault

<a id="equipment-clockwork-wings"></a>

### Clockwork Wings

- Cost: 24cp per Unit
- *Requires all of:*
    - Model type Infantry
    - 1 Independent
- *In assault:*
    - Strength: +1/0/0/0

**Movement orders granted**

| Speed | | | |
| --- | --- | --- | --- |
| slow | A(fast, fly) | F | F |
| fast_fly | 360° | F | B(slow, land) |
| fast_fly | F | 360° | F |
| fast_fly | 360° | F | F |
| fast_fly | F | F | 360° |

<a id="equipment-seeker-assassin-arrows"></a>

### Seeker Assassin Arrows

- Cost: 16cp per Unit
- Range: 4, angle True/True/True/True, damage d4-2, AP 1
- *Requires all of:*
    - 1 Special Arrows
    - Model type Infantry
- *When shooting:*
    - **[Limited Ammo](#rule-special-limited-ammo)**: [1]
    - **[Range Extra Damage](#rule-special-range-extra-damage)**: Poison[12]
- *Grants its Model:*
    - **[To Hit](#rule-special-to-hit)**: Excellent Shot. Applies when firing a seeker arrow

<a id="equipment-poison-bow"></a>

### Poison Bow

- Cost: 16cp per Unit
- Range: 2, angle True/True/True/True, damage d4-2 + d4 Crew damage, AP 1
- *Requires all of:*
    - 2 Hands
    - Model type Infantry or Cavalry
- *When shooting:*
    - **[Ammo](#rule-special-ammo)**: Always treated as loaded
    - **[Range Extra Damage](#rule-special-range-extra-damage)**: Poison[4]
    - **[Bonus](#rule-special-bonus)**: Crew damage improved to d8 if target has at least 3 Minor acid or 1 acid token

<a id="equipment-acid-trap"></a>

### Acid Trap

- Cost: 16cp per Unit
- *Requires all of:*
    - 1 Independent
    - Model type Infantry
- *Grants its Unit:*
    - **[Trap](#rule-special-trap)**: With the Lay Trap fire order, Instead of firing any weapons: place a Goblin Acid Trap in an unoccupied neighboring hex.

**Fire orders granted**

| Speed | | |
| --- | --- | --- |
| still | Lay Trap | Lay Trap |
| slow | Lay Trap | Lay Trap |

<a id="equipment-seeker-arrows"></a>

### Seeker Arrows

- Cost: 8cp per Unit
- Range: 4, angle True/True/True/True, damage d4-2, AP 1
- *Requires all of:*
    - 2 Special Arrows
    - Model type Infantry
- *When shooting:*
    - **[Limited Ammo](#rule-special-limited-ammo)**: [2]
- *Grants its Model:*
    - **[Enhanced Arrow](#rule-special-to-hit)**: Excellent Shot

<a id="equipment-gear-bow"></a>

### Gear Bow

- Cost: 8cp per Unit
- Range: 3, angle True/True/True/True, damage d4-2, AP 1
- *Requires all of:*
    - 2 Hands
    - Model type Infantry or Cavalry
- *When shooting:*
    - **[Ammo](#rule-special-ammo)**: Always treated as loaded
    - **[Range Gear Disruption](#rule-special-range-gear-disruption)**: [6+]

<a id="equipment-ogre-rifle"></a>

### Ogre Rifle

- Cost: 8cp per Unit
- Range: 2, angle True/True/True/True, damage d8-2, AP 2
- *Requires all of:*
    - 2 Hands
    - Model type Infantry
- *When shooting:*
    - **[Recoil](#rule-special-recoil)**: After firing this weapon, set speed to slow flying
- **Note (range)**: Remember to track ammo.
- *Grants its Unit:*
    - **[Movement](#rule-special-movement)**: Unit is destroyed if trying to land in an impassable or overcrowded hex.

**Movement orders granted**

| Speed | | | |
| --- | --- | --- | --- |
| slow_fly | rev | - | B[still] |

**Fire orders granted**

| Speed | | |
| --- | --- | --- |
| still | Load | - |
| still | - | Load |

<a id="equipment-poison-deflection-dagger"></a>

### Poison Deflection Dagger

- Cost: 8cp per Unit
- *Requires all of:*
    - 1 Independent
    - Model type Infantry
- *In assault:*
    - Deflection: +1/0/0/0
    - Deflection die: set to 6+
- *In assault:*
    - **[Damage on Deflect](#rule-special-damage-on-deflect)**: Each deflected hit gives enemy poison[4] token

<a id="equipment-combat-screw-driver"></a>

### Combat Screw Driver

- Cost: 8cp per Unit
- *Requires all of:*
    - 1 Independent
    - Model type Infantry
- *In assault:*
    - Deflection: +1/0/0/0
    - Deflection die: set to 6+
- *In assault:*
    - **[Cunning Deflection](#rule-special-cunning-deflection)**: Each deflected hit counts as hits for cunning assault purposes.

<a id="equipment-acid-grenade"></a>

### Acid Grenade

- Cost: 8cp per Unit
- Range: 1, angle True/True/True/True, damage n.a., AP 0
- *Requires all of:*
    - 1 Grenades
    - Model type Infantry
- *When shooting:*
    - **[Type](#rule-special-type)**: Thrown weapon
    - **[Ammo](#rule-special-ammo)**: Always treated as loaded
    - **[Range Extra Damage](#rule-special-range-extra-damage)**: Minor Acid. No regular damage.

<a id="equipment-poison-grenade"></a>

### Poison Grenade

- Cost: 8cp per Unit
- Range: 1, angle True/True/True/True, damage d4 Crew damage, AP 0
- *Requires all of:*
    - 1 Grenades
    - Model type Infantry
- *When shooting:*
    - **[Type](#rule-special-type)**: Thrown weapon
    - **[Ammo](#rule-special-ammo)**: Always treated as loaded
    - **[Range Extra Damage](#rule-special-range-extra-damage)**: Poison[4]
    - **[Bonus](#rule-special-bonus)**: Crew damage improved to d8 if target has at least 3 Minor acid or 1 acid token

<a id="equipment-goblin-bow"></a>

### Goblin Bow

- Range: 2, angle True/True/True/True, damage d4-2, AP 1
- Carried by: [Elite Goblin Infantry](#model-elite-goblin-infantry), [Goblin Infantry](#model-goblin-infantry)
- *Requires all of:*
    - 2 Hands
    - Model type Infantry
- *When shooting:*
    - **[Ammo](#rule-special-ammo)**: Always treated as loaded

<a id="equipment-seeker-assassin-arrows-free"></a>

### Seeker Assassin Arrows

- Range: 4, angle True/True/True/True, damage d4-2, AP 1
- *When shooting:*
    - **[Limited Ammo](#rule-special-limited-ammo)**: [1]
    - **[Range Extra Damage](#rule-special-range-extra-damage)**: Poison[12]
- *Grants its Model:*
    - **[To Hit](#rule-special-to-hit)**: Excellent Shot. Applies when firing a seeker arrow

<a id="equipment-poison-bow-free"></a>

### Poison Bow

- Range: 2, angle True/True/True/True, damage d4-2 + d4 Crew damage, AP 1
- Carried by: [Giant Snake Cavalry](#model-giant-snake-cavalry)
- *When shooting:*
    - **[Ammo](#rule-special-ammo)**: Always treated as loaded
    - **[Range Extra Damage](#rule-special-range-extra-damage)**: Poison[4]
    - **[Bonus](#rule-special-bonus)**: Crew damage improved to d8 if target has at least 3 Minor acid or 1 acid token

<a id="equipment-hallucinating-poison-spit"></a>

### Hallucinating Poison Spit

- Range: 3, angle True/True/True/True, damage N/A, AP N/A
- Carried by: [Giant Snake Cavalry](#model-giant-snake-cavalry)
- *When shooting:*
    - **[Ammo](#rule-special-ammo)**: Always treated as loaded
    - **[Range Extra Damage](#rule-special-range-extra-damage)**: Poison[4]; Confused

<a id="equipment-goblin-grenade"></a>

### Goblin Grenade

- Range: 1, angle True/True/True/True, damage d6, AP 2
- Carried by: [Elite Goblin Infantry](#model-elite-goblin-infantry), [Goblin Infantry](#model-goblin-infantry)
- *Requires all of:*
    - 1 Grenades
    - Model type Infantry

<a id="equipment-goblin-grenade-free"></a>

### Goblin Grenade

- Range: 1, angle True/True/True/True, damage d6, AP 2
- Carried by: [Modified Truck](#model-modified-truck)
- *When shooting:*
    - **[Ammo](#rule-special-ammo)**: Always treated as loaded

<a id="equipment-goblin-auto-bow"></a>

### Goblin Auto Bow

- Range: 2, angle True/True/True/False, damage d4-2, AP 1
- Carried by: [Modified Truck](#model-modified-truck)
- *When shooting:*
    - **[Ammo](#rule-special-ammo)**: Always treated as loaded
    - **[Multiple Shots](#rule-special-multiple-shots)**: Shoot three times per fire order

<a id="equipment-light-mortar"></a>

### Light Mortar

- Range: 3, angle True/True/True/True, damage d4 Crew damage, AP N/A
- Carried by: [Bipedal Mech](#model-bipedal-mech), [Goblin Infantry Carrier](#model-goblin-infantry-carrier)
- *When shooting:*
    - **[Range Extra Damage](#rule-special-range-extra-damage)**: Poison[4]
    - **[Bonus](#rule-special-bonus)**: Crew damage improved to d8 if target has at least 3 Minor acid or 1 acid token

<a id="equipment-goblin-bow-battery"></a>

### Goblin Bow Battery

- Range: 2, angle True/True/True/True, damage d4 -2, AP 2
- Carried by: [Heavy Carrier](#model-heavy-carrier)
- *When shooting:*
    - **[Ammo](#rule-special-ammo)**: May be loaded (one at a time) with up to 3 ammo
    - **[Multiple Shots](#rule-special-multiple-shots)**: Fire d12 shots in one fire order per ammo spent, all targeted the same unit.
    - **[Range Extra Damage](#rule-special-range-extra-damage)**: Minor Acid; Poison[6]
    - **[Range Gear Disruption](#rule-special-range-gear-disruption)**: [6+]
- **Note (range)**: For each fire order, choose one of Minor Acid, Poison, or Gear Disruption as extra damage.
- *Grants its Model:*
    - **[Imprecise Weapon](#rule-special-to-hit)**: Bad Shot

<a id="equipment-heavy-crossbow"></a>

### Heavy Crossbow

- Range: 4, angle True/False/False/False, damage d6, AP 4
- Carried by: [Heavy Carrier](#model-heavy-carrier)
- *When shooting:*
    - **[Ammo](#rule-special-ammo)**: May be loaded (one at a time) with up to 3 ammo
    - **[Multiple Shots](#rule-special-multiple-shots)**: Fire once per ammo spend per fire order
- *Grants its Model:*
    - **[To Hit](#rule-special-to-hit)**: Enhanced Accuracy

<a id="equipment-stinkbomb"></a>

### StinkBomb

- Range: 4, angle True/True/True/False, damage d6 Psychic damage + d6 Crew damage, AP N/A
- Carried by: [Bipedal Mech](#model-bipedal-mech)
- *When shooting:*
    - **[Range Extra Damage](#rule-special-range-extra-damage)**: Minor Acid; Poison[6]
    - **[Area](#rule-special-area)**: If you hit the enemy, Area[5+] with same damage as main hit (with extra damage)
    - **[Cloud](#rule-special-cloud)**: Place a Poison Cloud[6] in the hex of the targeted unit

<a id="equipment-ring-of-fire"></a>

### Ring of Fire

- Range: 2, angle True/True/True/True, damage n.a, AP 0
- Carried by: [Mechanical Fire Bird](#model-mechanical-fire-bird)
- *When shooting:*
    - **[Area](#rule-special-area)**: [6+] target at all enemies within exactly range 2
    - **[Range Extra Damage](#rule-special-range-extra-damage)**: Fire

<a id="section-spawns"></a>

## Spawns

| Spawn | Unit | Equipment | Copies the loadout |
| --- | --- | --- | --- |
| <a id="spawn-tiny-snake"></a>tiny_snake | [Tiny Snake](#unit-tiny-snake) | — | no |

<a id="section-rules"></a>

## Rules Reference

<a id="rule-damage-type-acid"></a>
**Acid (damage type)** — *Rule text pending.*

- *See also:* [Acid (token)](#rule-token-acid), [Minor Acid (token)](#rule-token-minor-acid)

<a id="rule-token-acid"></a>
**Acid (token)** — Roll a d8 on the following damage table:

1. Downgrade from acid to minor acid.
2. +1 to future damage
3. As 2, and if unit has armor, it is reduced by 1 (all directions)
4. As 3, and place a poison cloud [4] at hex, and all units in this hex gets a minor acid token.
5. As 4, and in addition all units within range=2 gets a minor acid token
6. As 5, and unit gains a terror token.
7. As 6 and unit is set on fire.
8. Roll three times on this table.,


- *Phases:* Agony 0
- *Removed:* Downgraded as part of effect
- *See also:* [Acid (damage type)](#rule-damage-type-acid)

<a id="rule-token-aim"></a>
**Aim (token)** — Get +2 to hit an enemy. Only valid for units in line of sight of the hex where the aim was given. Last for only 1 round.

- *Phases:* Gunnery 1, Gunnery 2
- *Removed:* Either remove all aim tokens when you fire, or remove one each aftermath phase. Also remove all of them if you enter an assault (regardless of whether you win or not)
- *To hit:* +2
- *To be hit:* 0

<a id="rule-special-ammo"></a>
**Ammo (special)** — Describes how a weapon is loaded and how its ammo is tracked.

- *See also:* [Limited Ammo (special)](#rule-special-limited-ammo)

<a id="rule-special-area"></a>
**Area (special)** — Roll a die per enemy model in the hex. For each die at {N}+, roll for damage and and add extra damage to the corresponding unit.

<a id="rule-special-assault-extra-damage"></a>
**Assault Extra Damage (special)** — The target gets one {version} if hit at least once. Where a ratio is given, it gets one per {M} hits instead.

- *See also:* [Range Extra Damage (special)](#rule-special-range-extra-damage), Assault Gear Disruption (special)

<a id="rule-ability-bad-shot"></a>
**Bad Shot (ability)**

- *To hit:* -1
- *To be hit:* 0

<a id="rule-special-bonus"></a>
**Bonus (special)** — Bonus to range attacks

- *See also:* Penalty (special)

<a id="rule-special-boost"></a>
**Boost (special)** — Boosts and modifies assault capabilities

- *See also:* Penalty (special)

<a id="rule-special-cloud"></a>
**Cloud (special)** — *Rule text pending.*

- *See also:* [Fog (hex)](#rule-hex-fog), [Poison Cloud (hex)](#rule-hex-poison-cloud)

<a id="rule-token-confused"></a>
**Confused (token)** — Only effects biological units or units with biological crew. While confused, any movement order is replaced by a random move. Roll a d6, on 1-2, rotate unit left, on 3-4 rotate unit right, on 5-6: -. In addition, while confused you get -1 to hit.

- *Phases:* Gunnery 1, Movement 1, Movement 2, Movement 3, Gunnery 2
- *Removed:* Remove one token each pre-assault step in each movement phase
- *To hit:* -1
- *To be hit:* 0

<a id="rule-special-cunning-assault"></a>
**Cunning Assault (special)** — For each {N} assault successes assigned to one mechanical unit in assault, add +1 to all future damage tokens. If you manage to inflict two or more +1 to future damage this way, the enemy is shaken. Multiple hits from multiple models with same ability stack.

- *See also:* Cunning Assault Defense (special)

<a id="rule-special-cunning-deflection"></a>
**Cunning Deflection (special)** — *Rule text pending.*

- *See also:* [Cunning Assault (special)](#rule-special-cunning-assault), Cunning Assault Defense (special)

<a id="rule-special-damage-on-deflect"></a>
**Damage on Deflect (special)** — *Rule text pending.*

<a id="rule-hex-drone-trap"></a>
**Drone Trap (hex)** — All units from the team which placed the trap are immune to the trapp. All other units are effectd. Area(5+): roll a die per unit, at 5+, the target unit triggers the trap and the unit which triggered the trap gets a minor acid token.

- *Removed:* Trap is removed only after triggered
- *See also:* [Trap (special)](#rule-special-trap), [Goblin Acid Trap (hex)](#rule-hex-goblin-acid-trap)

<a id="rule-ability-enhanced-accuracy"></a>
**Enhanced Accuracy (ability)**

- *To hit:* +1
- *To be hit:* 0

<a id="rule-alias-enhanced-arrow"></a>
**Enhanced Arrow** — see [To Hit (special)](#rule-special-to-hit)


<a id="rule-special-evasion"></a>
**Evasion (special)** — Roll a die per area of effect damage. Ignore the damage at {N}+

<a id="rule-ability-excellent-shot"></a>
**Excellent Shot (ability)**

- *To hit:* +2
- *To be hit:* 0
- *See also:* Superb Shot (ability)

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

<a id="rule-special-fire-order"></a>
**Fire Order (special)** — *Rule text pending.*

<a id="rule-hex-fog"></a>
**Fog (hex)** — Treat hex as if it blocks line of sight and gives to-hit penalties for units standing in fog. To Hit penalties stacks with other terrain features.

- *Removed:* Remove one Fog in each hex in aftermath phase
- *To hit:* -1
- *To be hit:* -1

<a id="rule-special-forward-position"></a>
**Forward Position (special)** — At setup this unit may setup upt to {N} hexes away from normal setup area.

<a id="rule-hex-goblin-acid-trap"></a>
**Goblin Acid Trap (hex)** — All flying or floating units are immune to the trapp. All other units, including the goblin, are effectd. Roll a die per unit, at 5+, the target unit triggers the trap and the unit which triggered the trap gets an acid token.

- *Removed:* Trap is removed only after triggered
- *See also:* [Trap (special)](#rule-special-trap), [Drone Trap (hex)](#rule-hex-drone-trap)

<a id="rule-ability-good-shot"></a>
**Good Shot (ability)**

- *To hit:* +1
- *To be hit:* 0

<a id="rule-special-hidden"></a>
**Hidden (special)** — *Rule text pending.*

- *See also:* [Hidden (token)](#rule-token-hidden), Hide (special)

<a id="rule-token-hidden"></a>
**Hidden (token)** — While hidden you cannot be fired upon or be assaulted, nor can you fire or assault. You are also immune to Fear and Terror,

While hidden replace the unit with a hidden token. If you have multiple hidden units you do not have to reveal which one is under which token (but you have to keep track your self). In the start of the game you do not have to show the enemy exactly what units you have hidden. (but you have to state how many victory points worth of units that are hidden),

Reveal order: Place your unit within 2 hexes of the hidden token and gain reveal bonuses. In addition to revealing your self as a movement order, you may reveal your self any time you share an hex with an enemy. If so, make an assault and gain the stated reveal bonuses

If you reveal your self you get reveal bonuses: +2 to hit of ranged weapons and plus 50 percent assault strength and deflection for the first assault you participate in this round.

- *Removed:* You stay hidden until you reveal yourself, in aftermath phase if an enemy is within point blank range, or an enemy special action reveals your location. Cloaking devices stay hidden even if in clear terrain, while all others sources of hidden abilities are revealed if they are in slow or fast in clear terrain within line of sight to an enemy. You only get reveal bonuses if you willingly reveal your self, not if you are forced to.
- *See also:* Hide (special), Fear (special), [Terror (special)](#rule-special-terror)

<a id="rule-token-hypnotized"></a>
**Hypnotized (token)** — Can only be given to bio units which are already shaken, and not insane. Any flee order is treatet as do nothing, stand still. In addition, Reduce assault strength 50% rounded down.

- *Phases:* Movement 1, Movement 2, Movement 3
- *Removed:* When unit is not longer shaken
- *See also:* [Shaken (token)](#rule-token-shaken), [Insane (token)](#rule-token-insane), [Hypnotizing Gaze (special)](#rule-special-hypnotizing-gaze)

<a id="rule-special-hypnotizing-gaze"></a>
**Hypnotizing Gaze (special)** — In agony 3, all units that are shaken within range of given unit, also becomes hyptnotized

- *See also:* [Shaken (token)](#rule-token-shaken)

<a id="rule-special-immunity"></a>
**Immunity (special)** — *Rule text pending.*

<a id="rule-alias-imprecise-weapon"></a>
**Imprecise Weapon** — see [To Hit (special)](#rule-special-to-hit)


<a id="rule-token-insane"></a>
**Insane (token)** — Can only be given to bio units which are already shaken. If also hypnotized, remove hyptnotized token and replace it with insane. Any flee order is treatet at chase, but targets friends or foe alike. If there are two or more equally valid hexes to move to with chase, the owner still decides where to go

- *Phases:* Movement 1, Movement 2, Movement 3
- *Removed:* When unit is not longer shaken
- *See also:* [Shaken (token)](#rule-token-shaken), [Hypnotized (token)](#rule-token-hypnotized), Insanity Field (special)

<a id="rule-special-limited-ammo"></a>
**Limited Ammo (special)** — This weapon may be fired a maximum of {N} times in a match. Starts the game with {N} ammo loaded

<a id="rule-token-minor-acid"></a>
**Minor Acid (token)** — Role a die, at 3+, unit gets +1 on future damage. Otherwise, remove minor acid

- *Phases:* Agony 1
- *Removed:* Only as part of effect
- *See also:* [Acid (token)](#rule-token-acid), [Acid (damage type)](#rule-damage-type-acid)

<a id="rule-special-movement"></a>
**Movement (special)** — *Rule text pending.*

<a id="rule-special-multiple-shots"></a>
**Multiple Shots (special)** — *Rule text pending.*

- *See also:* Burst (special)

<a id="rule-special-phoenix"></a>
**Phoenix (special)** — *Rule text pending.*

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

<a id="rule-special-pre-assault-retreat"></a>
**Pre-Assault Retreat (special)** — In pre-assault phase you may roll a die. At N+ you may retreat before the assaults starts. Treat this as a regular reatreat but give or take no assault damage. This ability may only be used if the hex retreating into neither becomes overcrowded, is an illegal hex or contain enemies.

- *See also:* [Retreat (special)](#rule-special-retreat)

<a id="rule-damage-type-psychic"></a>
**Psychic (damage type)** — *Rule text pending.*

<a id="rule-special-range-extra-damage"></a>
**Range Extra Damage (special)** — The target gets one {version}.

- *See also:* [Assault Extra Damage (special)](#rule-special-assault-extra-damage), [Range Gear Disruption (special)](#rule-special-range-gear-disruption)

<a id="rule-special-range-gear-disruption"></a>
**Range Gear Disruption (special)** — Only applies when target is a drone. The drone gets one shaken token per roll of {N}+.

- *See also:* Assault Gear Disruption (special)

<a id="rule-special-recoil"></a>
**Recoil (special)** — *Rule text pending.*

<a id="rule-special-resistance"></a>
**Resistance (special)** — Gives improved resilience versus {version} damage

<a id="rule-special-retreat"></a>
**Retreat (special)** — *Rule text pending.*

- *See also:* [Pre-Assault Retreat (special)](#rule-special-pre-assault-retreat)

<a id="rule-token-shaken"></a>
**Shaken (token)** — While shaken set unit speed to the specified speed, and how a unit behaves is described by each unit. Disregard the original orders and replace them with the order(s) described by the unit

- *Phases:* Gunnery 1, Movement 1, Movement 2, Movement 3, Gunnery 2
- *Removed:* Remove one each aftermath phase. Can also be removed by appropriate repair or healing abilities
- *See also:* Heal (special), Repair (special)

<a id="rule-speed-sneak"></a>
**Sneak (speed)**

- *To hit:* +1
- *To be hit:* 0

<a id="rule-special-spawn"></a>
**Spawn (special)** — *Rule text pending.*

<a id="rule-speed-still"></a>
**Still (speed)**

- *To hit:* +1
- *To be hit:* +1

<a id="rule-ability-take-cover"></a>
**Take Cover (ability)** — Applies when the unit is in the given speed

- *To hit:* 0
- *To be hit:* +N

<a id="rule-special-terror"></a>
**Terror (special)** — In agony 0, roll a d{M} psychic damage on any enemy unit within range of this unit.

- *See also:* [Terror (token)](#rule-token-terror), [Psychic (damage type)](#rule-damage-type-psychic)

<a id="rule-token-terror"></a>
**Terror (token)** — Acts as if unit has Terror[6] (range=2) but effects only units of the same team

- *Phases:* Agony 0
- *See also:* [Terror (special)](#rule-special-terror)

<a id="rule-ability-thrown-weapons"></a>
**Thrown Weapons (ability)** — Applies to thrown weapons only

- *To hit:* +N
- *To be hit:* 0

<a id="rule-special-to-hit"></a>
**To Hit (special)** — Shifts the to-hit and to-be-hit rolls by {ability}.

- *See also:* [Aim (token)](#rule-token-aim)

<a id="rule-special-transport"></a>
**Transport (special)** — *Rule text pending.*

<a id="rule-special-trap"></a>
**Trap (special)** — *Rule text pending.*

- *See also:* [Goblin Acid Trap (hex)](#rule-hex-goblin-acid-trap), [Drone Trap (hex)](#rule-hex-drone-trap)

<a id="rule-special-type"></a>
**Type (special)** — *Rule text pending.*
