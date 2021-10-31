# Turn

Each turn contains the following steps:

- Gunnery 1 \
Apply damage \


Trigger hex effect \

- Movement 1 \

Pre assault retreat/abilities\
Pre assault abilities

- Assault 1 \

Post assault retreat\
Apply damage \

Trigger hex effect \

- Movement 2 \

Pre assault retreat/abilities \

- Assault 2 \
Post Assault retreat \
Apply damage \

Trigger hex effect \

- Movement 3\
Pre assault abilities \


- Assault 3\
Post assault retreat \
Trigger hex effect  \
Apply damage \

- Gunnery 2\
Apply damage \


- Agony 0 (major acid, terror)
- Agony 1 (minor acid)
- Agony 2 (fire)
- Agony 3 (poison)
- Agony 4 (bleeding)

- Aftermath  (remove smoke, etc.)

\pagebreak

Phase      Name        Effect
---------- ----------  ------------------------------------------------------
Agony 0    Acid        * se below \\
           Terror[N]   Roll dN psycic damage for everyone with spesific range 
Agony 1    Minor Acid  1-2: remove minor acid, 3-4: +1 on future damage
Agony 2    Fire        1: no damage, stop burning, 2+: do fire damge
Agony 3    Poison[N]   doll dN poison damage, downgrade poison one step
Agony 4    Bleeding[N] Roll dN. 1: stopp bleeding, 2+ do damage
Aftermath  Remove      Remove 1 shaken token, cloud marker etc.
---------- ----------  ------------------------------------------------------

Poison damage: Applies ONLY to biological units! Apply damage to regular damage table, but apply poison resistances if any. Ignores armor. +1 future damage applies to poison damage as well.

Fire damage: Apply damage to regular damage table, but apply poison resistances if any. Ignores armor and +1 future damage tokens applies to fire damage as well.

Bleeding damgage: Ignore armor, aply + to future damage if any, roll on regular damage table.

Psycic damage: Only applies to units with a psycic damage table. Ignore regular + to future damage

Crew damage: Only applies to units with a psycic damage table. Apply only + to future crew daamge

Any other special damage: only applies to units with given special damage table

Acid:

Roll d6: \
at 1, downgrade to minor acid \
at 2: +1 to future damge \
at 3: As 2, and place a poison \& acid cloud \[4, minor] athex \
at 4: As 3, and if unit as armor, it is reduced by 1 (all directions) \
at 5: As 4, and unit is set on fire\ 
at 6: roll twice on this table. \


# Hex based effect.

Hex based effects are triggered in all 'trigger hex based effects' steps. (before any movement in all movement phases)
When placing Clouds, smoke or fire on a hex for the first time, place two markers of the given type. Otherwise, place only one.
Hex based effects are not cumulative. However the effect of acid, fire and poison on units are cumulative with both itself and each other. 
In case of poison clouds with different strength, apply the strongest if overlapping.

Follow the instructions for each hex based effect

**Poison** **Cloud** [N] 

Area(6+): roll 1 die per model in hex. At 6+, apply a poison[N] to target, and do dN in crew damage.

Note that poison only applies to biological units, while crew damage only applies to units with crew damage table. (usually this means a unit takes either poison OR crew damage)

**Acid** **Cloud** [Minor] 

Area(6+) roll 1 die per model in hex. At 6+ place a minor acid on the unit base.

\pagebreak

For movement and line of sight, se table below:
--------              -----------------------------------------------------------------------------------------------------------------------------
Clear                 No modifiers
Mountains             2 movement points up, 1 down. 2 hight level, level 2 blocking terrain.
Hills                 2 movement points up, 1 down. 1 hight level, level 1 blocking terrain.
Forest                2 movement points to enter for vehicles, 1 for all other things.
                      Level 0 blocking terrain
Burned Forrest        Level 0 blocking terrain
Ruins	              1 movement points to enter. Does not block line of sight
Rough                 1 movement points to enter. Does not block line of sight
Sand Dunes            2 movement point to enter. Level 0 blocking terrain
*Advanced* *terrain*
Swamp                 1 movement point to enter for medium and smaller, 
                      +1/+2 movement points to enter for large/huge size
                      Units with track or wheel in description may get stuck,
                      at 1 or 2 on a d6, the unit cannot move this movement step, regardless of order
                      Does not block line of sight
Building              2 movement points to enter for infantry,
                      any other type cannot enter without a special rule
		      Level 0 blocking terrain.
Road                  If moving from a road to another hex with road, movement always cost 1.
Smoke                 Blocks line of sight 
                      Removed in aftermath. (place two smoke markers, remove 1 in each aftermath)
River                 +1 movement point to enter		      
Water                 1 movement point to enter for ships, floating or flying
                      (and can only be entered while flying). Cannot be entered by any other way.
--------              -----------------------------------------------------------------------------------------------------------------------------

\pagebreak


                          to hit, to be hit  special
------------------------ ------- ---------- ---------------------
*Speeds*
Stand still                +1      +1
Crawling                   +1      +1
Rest                       +1      +1
Setup speed                +1      +1
Slow                        0       0
Fast                       -1      -1
Flying                     -1      -1         (stacks with speed)
*Terrain*
Smoke                      -1      -1
Forrest                     0      -1         Grants Evation(-1) for any unit with active take cover
Burned Forrest              0      -1         Grants Evation(-1) for any unit with active take cover
Building                    0      -1         Grants Evation(-1) for any unit with active take cover
Ruins                       0      -1         Grants Evation(-1) for any unit with active take cover
Rough Terrain	            0      -1         Grants Evation(-1) for any unit with active take cover
Sand Dunes                  0      -1         Grants Evation(-1) for any unit with active take cover
*Orders*
Aim                        +2       0         (aim bonus last 1 round. If not applied next turn)
*Range*
Point-Blank                +1       0         (range =1)
Normal range                0       0         (within weapon range)
Long range                 -1       0         (within max x2 of weapon range)
*Angle*
On-edge of firing-angle    -1       0
*Size*
HUGE                        0      +1
*unit* *abilities*
Good Shot                  +1       0
Excellent Shot             +2       0
Superb Shot                +3       0
Bad Shot                   -1       0
Steady                     +1       +1
Camouflage\[terrain\]       0      -1         when unit is in given terrain
Take Cover[speed, -N]       0      -N         When in given speed, stacks with speed. Improves Evation(+1)
Elusvie[speed, -N]          0      -N        
Optimal at point blank     +1       0         Firing at enemies at point blank range only
*Weapon* *abilities*
Enhanced Accurazy           +1      0
------------------------ -------  ---------- ---------------------



\pagebreak

Unit abilities

**Take Cover**[speed, -N]

When unit is in given speed the unit is considered taking cover and gets -N to be hit, as indicated by to-hit table. Whenever this condition apply, AND unit is in cover-providing terraing, also gain the Evation[-1] trait.


**Evation**[-1]

Modified the success of an area of effect. For example, an Area(5+) effect will no be an Area(6+) effect. Furhter, an Area(6+) will now be an Area(7+), where you use the open ended d6 rules to get 6.



**Forward Position**[N]

At setup this unit may setup upt to N hexes away from normal setup area.


**Pre-Assault** **retreat**[N+]

In pre-assault phase you may roll a die. At N+ you may retreat before the assaults starts. Treat this as a regular reatreat but give or take no assault damage. If speed is currently at stand-still it become slow afterwards. This ability may only be used if the hex retreating into neither becomes overcrowded, is an illegal hex or contain enemies.

The unit base have this ability if atleast one model in the unit has this spesicial ability.

**Stuborn**

After loosing an assualt, if you occupied the hex you where fighting over in an assault before the assault, you never retreat. Repeat the assault instead, untill you either win or die.


**Terror**[range=n][dN]

In agony 0, roll a dN psycic damage on any enemy unit within range of this unit. Half number of dice rounded down from all enemy shaken unit bases entering assault with you. Your enemy chooses which dice to remove if they represent different attacks

**Fear**[N]

In pre-assault phase, roll a dN on psychic damage for each enemy unit base which has a psychic damage table (ignore armor and regular damage modifiers)
Half number of dice rounded down from all enemy shaken unit bases entering assault with you. Your enemy chooses which dice to remove if they represent different attacks


**Cunning** **Assault**[1 per N]

For each N assault successes assigned to one unit-base (from sources with this ability), do one light damage[d6]. 

Thus, for example Cunning Assault[1 per 2] would allow you to do d6 light damage if you hit it the unit two times, in addition to the regular damage. Note however, that light damage only does damage versus unit with a light damage table (vehicles only). 

This represent any cunning way to take out heavily armored units in assaults, where regular hits would do little damage.


**Reroll** **Assault** N

For each 6 you get in assault, you may reroll up to N assault or assault deflection dice. All rerolled dice have to be rolled in one go (thus you may not reroll one dice more than once). However, if get another 6 in the assault dice, repeat the process.


**Ork** **Assault**

Each 6 in assault counts as two successes.