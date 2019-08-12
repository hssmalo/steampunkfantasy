## Build your army.


- A pure tank game consists of 12 industry points(12ip)
- An infantry battle consists of 12manpower (mp), 12crafts points and 12xp.
- A small game consists of 12industry points(12ip), 12manpower (mp), 12crafts points and 12xp.
- A standard game consists of 12industry points(12ip), 24manpower (mp), 12crafts points and 12xp.
- An advanced game consists of 12industry points(12ip), 24manpower (mp), 12crafts points, 12xp and 12 command 

Industry represent heavy equipment production. Tanks and vehicles.
Manpower: Represent the manpower needed to form infantry and cavalry.
Craft points represent small arms production, and which is hand crafted.
XP represent extra training, and taming of fantastical creatures
(Command: gives you officers, officers abilities and engineering etc. Advanced games only. Not jet implemented.)

Build your army in any way you like, as long as the total cost is less than the total amount of points.
Infantry, and some cavalry and special units may be upgraded with xp and crafts points (and command).
Each upgrade has it requirements. Some upgrade the entire unit base, while some only upgrade one or a few members.


A unit base typically has 1,2 or 4 unit members. A unit base can be upgraded with as much as you like as long as you have the space.
Unless otherwise stated, an infantry unit base may have

- 1 two-handed weapon or 2 one-handed equipment (heavy musket, pistol&shield)
- Any number of misc equipment (such as grenades, gas-masks, wings...)
- A unit base may have a maximum of one unit-base weapon. (hand-held cannon)

Each member of the unit base can fire it's weapons independently, and you add assault dice to the assault die pool for each unit. 
But all members of a unit base gets the same order.


Elites typically upgrades 2 regular infantry, which then replaces the regular in one or two unit bases.
Normally weapons upgrades all weapons in the unit base. The exception being elite equipment.

In some cases some equipment reqiuers an elite and the cost is typical for one weapon and only one elite in the unit base gets that weapon. However, as long as you have more elites left in the unit base, you may pay the price multiple times to equip as many as you like with elite weapons.

Special cases should be clearly stated with limitation and how to apply in the cost.

\pagebreak

# Terrain 

This game is played on a hex-based map. Each hex contains a given type of terrain, some blocks line of sight and hinders movement and gives cover. For last, se to-hit table under the fire section.

It is also possible that smoke, entrenchements etc. modify the default terrain.

For movement and line of sight, se table below:
-------- --------------------------------------------------------------------------------------------------------------------------------------
Clear    No modifiers
Hills    2 movement points up, 1 down. Line of sight as Tide of Iron (almost)
Forrest  2 movement points to enter for vehicles, 1 for all other things. Block line of sight
Swamp    1 movement point to enter for medium and smaller,
         +1/+2 movement points to exit for large/huge size
         Vehicles get stuck, at 2- the unit cannot move this movement step
         Does not block line of sight
Rough    2 movement points to enter. Does not block line of sight
Smoke    1 movement point to enter. Blocks line of sight 
         removed in aftermath. (place two smoke markers, remove 1 in each aftermath)
-------- --------------------------------------------------------------------------------------------------------------------------------------


If a unit tries to enter a hex which cost more than 1 to enter, place a 'entering difficult terrain token' for the unit base. It can only move into the hex if it already have enough of these tokens to enter the hex. An hex cost 2 movement points to enter needs 1 of these token already presents, while a hex costing 3 needs 2 of those tokens. (2 token then you spend the third action to enter). You loose all tokens if you do any movement not trying to enter the hex.

Stacking Limit
One hex may maximum hold either up two 2 units if at most one of them is large, or 1 huge unit.


If trying to enter the same hex with MORE than that simultaneously, all from within same team/faction, then all units trying to move into the hex stay put and are *stunned* (se unit abilities and conditions) next sequence. 


\pagebreak

# Turn


Each turn contains the following steps:


- Gunnery 1 \
Trigger Hex effect(if hex effect was fired in a hex you were standing)
 
- Movement 1 \
Pre assault retreat \
Trigger hex effect (including all units in contested hexes)\ 
Pre assault abilities

- Assault 1 \
Post assault retreat\
Trigger hex effect 

- Movement 2 \
Pre assault retreat\
Trigger hex effect (including all units in contested hexes) \
Pre assault abilities

- Assault 2 \ 
Post Assault retreat \
Trigger hex effect 

- Movement 3\
Pre assault retreat\
Trigger hex effect (including all units in contested hexes)\
Pre assault abilities

- Assault 3\
Post assault retreat\
Trigger hex effect 

- Gunnery 2\
Trigger Hex effect(if hex effect was fired in a hex you were standing)

- Agony 0 
- Agony 1
- Agony 2
- Agony 3
- Agony 4

- Aftermath  (remove smoke, etc.)

---


Multiple things may happen in same step, but they happen simultaneously. The exception is damage, where any damage taken are rolled in sequence. Roll damage in any order the attacker wishes, apply damage before rolling for next damage. 


\pagebreak

# Orders

Give each unit base at least one movement order and the number of fire orders dictated by the unit stats. At any time you should have orders 1 round of orders ahead of time. For most units, this means you should have 1 movement order and one fire order on the table when making a new order. Then, after setting up orders, you should follow those orders.


Action are ordered in advance, and in principal everything in one step is done simultaneously. However, if the orders include choices as for example who to fire at etc. and that choice depends on what the enemy choice is, then resolve it as follows: Any unit which MAY enter an assault depending on the choices it does in movement (if existing), declares whether it want to enter an assault or not. The ones not entering assaults must choose first, and the ones entering assault second, and they must then enter assault (if possible). If there are still choices which depends on what the other chooses, the ones choosing last according to this table. The highest rank choices last:

Spartan \
Elf \
Dark-Elf \
Dwarf \
Ork \


Movement orders are dependent on whether you are fast, slow or stand-still (or possible other as special rules).

Movement orders may for example be:
(fast) F + F + -\
(fast) F + L + -\
(fast) F + B + -\
(slow) A + F + -\

Defults
(fast) F + F + - \
(slow) F + - + - \
(atand-still) - + - + - \

Each unit has a set of available orders. Code:


- F = forward
- R = rotate one click right
- L = rotate one click left
- B = break, change to one speed slower.
- B[X] = as break, but set speed to a special case, described by a work(X).
- A = Accelerate, change to one speed faster
- A[X] = As accelerate, but set speed to a special case, described by a word(X).
- Rev=reverse
- - = no action
- Chase: move towards nearest enemy.
- 360$^0$: rotate in any direction you want.
- Flee: Move in any hex you like as long as you move further away from the enemy. If no such hex is available, move to a hex which is not closer to the enemy
If still no such hex is available, let your enemy move your unit to any hex he/she likes


Any order divided in 3 happens in movement step, where the first is executed in movement 1, the second in movement 2 and the third in movement 3.
If Two different steps are separated by comma instead of a +, they happen in same step. For example: \
-360$^0$,A + F + F \

Would read you could rotate 360$^0$ and accelerate in first movement, and forward in movement 2 and 3.


Gunnery orders are for example:\
- + Aim \
- + Load (stand still only) \
- + Fire\
Aim + -\
Load + -\
Fire + -\

Default Gunnery: - + - \

The first is executed in gunnery 1, the second in gunnery 2. 
Some orders are only available during one or more spesific speeds/movement modes.
If a movement triggers a change in speed, it is possible that the first gunnery order part 1 not allowed, but part 2 is. If a unit breaks and goes from fast to slow, gunnery part 1 does not allow gunnery orders associated with slow but gunnery part 2 do.

If an elegal order is given, do default order instead.



Load: loads weapon. A weapon cannot fire without a load token available.
      Some weapons may load more than one ammo per loading. It is then noted as
      load[5] \
Aim : optional: +2 to hit\
Fire: fire at an enemy within line of sight and within aloud firing angle of tank.
Default: - \

The speed of the unit may restrict what options are available.

If, for some reason or another, the given order for one step is not allowed, it is replaced by default. If default for one reason or another is not allowed, replace it with -. Some units may override the default.

\pagebreak

# Angles
All units are always facing one spesific direction, noted as forward. Then all units has a front-side, back-side and and back angle.

Some values and stats depend on the angle you are using. All stats dependent on angles is divided into 4, separated by /-symbol.
The first entry is front, the second is front-side (both left and right), the third entry is back-side(both left and right) and fourth is back.

Firing angles:
\* indicates firing angle is allowed, - indicates firing with that weapon is not allowed in that angle. Anything going to the front hex-side is considered in front, and anything tracing line of sight through side-front hex-side is considered front-side etc. Shots directly inbetween front and front-side are considered on-edge of firing angle, and can be used but at a penalty (see to-hit table).

\*/-/-/-   Can fire in front only \
\*/\*/\*/\*   Can fire in any direction \

Armor:
Use the armor value which your target is using.
4/3/3/2   has 4 armor in front, 3 in front-side, 3 in back-side and 2 in back.

Any stat which is not divided in 4 groups is assumed to be identical for all 4 angles.


ps! All units are symetrical with respect to left and right!

\pagebreak

# Fire

At firing orders, you may roll a die to see if you hit the enemy. 

Basic to-hit: 5+

Modify it with the following modifiers:


                          to hit, to be hit  special
------------------------ ------- ---------- ---------------------
Stand still                +1      +1
Crawling                   +1      +1
Rest                       +1      +1
Setup speed                +1      +1
Slow                        0       0
Fast                       -1      -1
Flying                     -1      -1         (stacks with speed)
Smoke                      -1      -1
Forrest                     0      -1
Aim                        +2       0
Point-Blank                +1       0
Normal range                0       0
Long range                 -1       0         (max x2 range)
On-edge of firing-angle    -1       0
HUGE                        0      +1
*unit* *abilities*
Good Shot                  +1       0
Excellent Shot             +2       0
Camouflage\[terrain\]       0      -1         when unit is in given terrain
Take Cover[speed, -N]       0      -N         When in given speed, stacks with speed.
------------------------ -------  ---------- ---------------------

Roll an open ended d6 for to-hit.

Open ended dN. \
-If you roll a N to hit, you may role another d6. If you roll above 4, add one to the original result. Keep rolling dies as long as you roll above 4.

Example: open ended d6: You roll a 6, then a 5 and you may roll another die. That ends up a 6 again. You roll another die and you roll a 3. The result is 6+1+1=8.


On-edge hexes: \
The firing vehicles decides which angle the shots come from and enter into.
However, employing hexes at the edge of it's own firing angle gives a to-hit penalty.


Area To-Hit: \
Area(n+): roll 1 die per enemy unit in hex. Apply damage per success.

Area success success modifiers: \
+1 to success per extra identical area attack.

Example: success for 4 x area(6+) attacks versus a single hex becomes 3+.


\pagebreak

# Damage

If you hit, roll for damage.

Any specified damage is regular damage, and follow these rules:
Before you roll damage, roll armor penetration first.

Armor penetration is divided into two categories, both are given by weapon.
1) AP: Ignores that many armor die.
2) Pen: how easy it is to break through the armor which is not ignored.
If not stated it is assumed they are zero.

AP is reduced by 1 for each 3 hex between units, to a minimum of 0.


Roll (Armor - AP) number of die. \
Apply -3 on damage for each  die above N, where N is: 

- N= 5 for weapons without any penalty on penetration. 
- N= 4 for weapons with -1 on penetration 
- N= 3 for weapons with -2 on penetration 
- N= 2 for weapons with -3 on penetration 

If armor_penetration = armor, count as no armor.


Damage: Roll on damage for the unit, add previous bonus and weapon modifiers if any. Any result less than the starting value of the damage table counts as no damage.

Whenever one member of a unit with multiple members die, half previous bonus to damage round down.

# Special Damage types


Unless otherwise stated by the weapon, any weapon has regular damage. Some weapons and effects may have special damage in addition or instead of.
Some special damage types have special rules, which include
- Poison
- Fire
for which details can be seen under continious damage.

Other, more generic damage types will be noted by the following in weapon stats:\
- [type] damage[dN]
For example, a weapon may have Psychic Damage in addition to regular damage.

If so, and if the target has a damage table of name equal to the type of damage, roll a dN on that damage table. For example if you have
- Psychic Damage[d6]
Roll a d6 on psychic damage table of target.
If the target don't have a pcychic damage table, the unit is immune to this damage.


\pagebreak

# Assault

If two or more units from different team/faction tries to enter the same hex simultaneously, use ASSAULT rules.

- Before any assault, any unit which has the ability to retreat before assault have the option to do so now.
- Then trigger any hex effects (as poison cloud, fire in hex etc.) to all units trying to enter the hex.
- Then apply any pre-assault special effects such as fear if any.
- After assault, trigger any hex effect again, but note that one unit may only be effected by the same hex effect once per turn.
This is just in case a unit was forced into a hex with for example poison cload.

The winner of the assault enters the hex. If the looser is forced out of the hex, it then retreats. If looser was stationary, it moves out of the hex in the backward direction. If the looser was trying to enter a hex, it stays in the hex it was before trying to enter the hex. In any way, during a retreat, the looser may rotate to Left or Right or 180$^0$ if you wish.

If trying to retreat into a overcrowded hex... ???

If more than Stacking Limit number of units enters the hex after winning an assault, all winners are also stunned as if trying to move into a hex with friendly units only.



Assault: Number of dice, to_hit, any Damage modifiers. \
Facing : Use front assault values and armor for units entering the hex, with the exception, when reversing into an assault, set facing = back.
         For stationary units being assaulted, use assault and armor from the side which it is assaulted from.
	 If being assaulted from more than one side, choose one.
	 


Multiple Units: add all dice for up to stacking_limit number of unit bases, roll separate dice if necessary, both if the different units have different to_hit value for the assault and if they have different damage output.
It may be the case that some units involved have better damage, it is then necessary to track which unit did hit and which did not. If you for example have an orc-warhero with an flaming waraxe in a mix with 3 ork-grunts, roll all dice for the warhero with red dice and the grunts with blue die. If a red die hits, you may employ the flaming waraxe special damage, but if only blue dice hit, you may not.

Assault Deflection: Number of dice, to_hit\
Use the appropriate stats for similar to the assault values.
Add the number of dice for all unit involved in the assault, roll separate dice if they have different to_hit stats.
Each succuessfull deflection remove one successful assault. (winner of assault chooses which hits to deflect)

An good practice is to roll assault and assault deflections simultainiously but with different color. Choose for example green die for deflections.


Whoever rolls the highest number of successfully assaults (after deflection) wins. If equal, use Nation assault winning-power order:

Spartan\
Dark_Elf\
Ork\
Dwarf\
Elf\


Apply successful assault to enemy units. The winner may choose which hits are assigned to which unit as long as any assault successes are asign to the opposing team. The must apply at least one hit to each unit member if possible. Roll one damage for each unit assigned atleast one success. Add +1 to damage for each extra successful assault assigned to one unit beyond the first. Thus with 4 successes versus a unit with 2 member, you may assign 3 hits to 1 of the members and 1 hit to the other if you wish.



Example: \
DarkElf: 1 tank, a infantry base with 4 unit member: 7 success, 3 deflections. \
Elf: 1 tank, a infantry base with 3 alive member: 6 success\
Total: Side 1 scored 7 hits, side 2 scored 3. \
Winner: Side 1.

Side 1 the assigns 7 hits to side 2, and 3 hits versus his own.
She must assign atleast 3 hits to side



Roll for Armor penetration and add all special abilities as normal shot.

Example:
Standard Tank\
   Assault:     4, 5+ / 3, 5+ / 3, 5+ /2, 5+: -1 on penetration and damage.\
   Deflection:  2, 5+ / -, -  / -, -  /-, - : \

This tank rolls 4 dice which hits on 5+ when assaulting a hex, and also when being assaulted from the front. Then it also gains 2 deflection die.
If this tank is stationary and is assaulted from the sides it only gets 3 dice and no deflections.

\pagebreak

# Unit Abilities and conditions:

Fear[N]

In pre-assault phase, roll a dN on psychic damage for each enemy unit base which has a psychic damage table (ignore armor and regular damage modifiers)
Half number of dice rounded down from all pinned unit bases entering assault with you. Your enemy chooses which dice to remove if they represent different attacks

Cunning Assault[1 per N]

You may replace N assault successes assigned to one unit-base for light damage[d6].

Thus, for example Cunnin Assault[1 per 2] would allow you to replace to assault-successes with one roll on light damage table (if enemy unit base has a light damage table, which typical is only for tanks and vehicles). Note that the replacements are done after asigning hits to different untis, and only hits versus the spesific target can be replaced, not hits versus other units. 

[type] Resistances[n]

Reduce damage by [n] from damage of given type.
Default type of any shot is regular damage. Other types are always specified.

Regular: any damage rolled on regular damage table of unspecified type. This does not include damage from any other type.
Psychic : any damage rolled on psychic damage table of unspecified type.
Poison : any damage rolled by poison effect
Fire   : any damage rolled by fire effect

Any other resistance may be added in future. It then is effective only versus the spesific damage type.
Damage type is either regular damage, or explisitly given by the firing unit or effect.


Pinned/Stunned.

Pinned: when first pinned, place two pinned tokens. One is removed during each aftermath.
While pinned a unit do not continue with any orders until it is fresh again. Orders in stack are activated after pinned is over.
For vehicles this represent temporarily mechanical problems.

Replace all movement orders with the default for the given speed, and no orders for gunnery action (Unless, overwritten by special rule: fast: F+F+-, slow: F +- + -, stand-still: - + - + - , gunnery-orders: - + - )

\pagebreak

# Continuous Damage:

Done in step: \
Agony 0 to Agony 4.

Acid: (roll by enemy)\ 

- At agony step 1, unit gain +1 on future damage \
- At agony step 2, roll a die: \
			     at 1-: Downgrade from major acid to minor acid.\
    	      	      	     at 2 : Any unit in same hex as this unit get
			     	    infected by minor acid.\
			     at 3 : place a poison cloud \[4\](4+) at hex.\
			     at 4 : if unit has armor, it is reduced by 1/1/1/1\
			     at 5 : unit is set on fire.\
			     at 6 : roll on this table twice, and gain +1 on future damage\

- If you happen to get two (or more) downgrade in same round, you remove acid instead of downgrading it.

Minor Acid:

- At agony step 1 roll a die, at 3+, unit base gets +1 on future damage. At 2-, remove minor acid

Unit on Fire: (roll by enemy)

- At agony step 3 Ignore armor and roll one d6 on damage table.
Add bonus for previous damage (plus on future damage results). 
Apply any fire resistance modifiers if any.
Ignore armor.
If the natural d6 roll 2 or lower, remove the fire





Unit Poisoned [n]\
Only biological units effected. All other types ignore poison.

- At agony step 3: Roll a dN (d4, d6, d8, d10 or d12) on damage. Apply any poison-resistance and any plus on future damage modifiers if any.
Ignore armor. Further, if poison killed one member from unit base, remove that instance of poison from unit. If not, downgrade poison by one step (12 -> 10 -> 8 -> 6 -> 4 -> NONE)


Bleeding:

- At agony step 4: Bleeding[n]: roll a dN. If you get 1, remove the bleeding with no effect.
If not, count the result as damage, ignore armor but add bonus from previous damage as normal.
Bleeding does not cuz more bleeding, but all other effects of damage are applied to unit.
If bleeding kills one member, remove this bleeding effect.


# Hex based effect.

Hex based effects are triggered in any 'trigger hex based effects' step, and only tiggers the first time a unit encounters the effect in that hex. It only retriggers if entering the same hex for a second time.

When placing Clouds and smoke on a hex for the first time, place two markers of the given type. Then remove one of them in the aftermath phase.

Hex based effects are not cumulative. 


Follow the instructions for each hex based effect

**Poison** **Cloud** [N] (4, 6, 8, 10 or 12) (n+)
(n=1+, 2+, 3+, 4+, 5+ or 6+)


Roll 1 die per biological unit in hex. At n+, apply a poison[N] to target enemy base. Roll 1 die per unit. Thus one unit base with 4 units may get multiple poison markers.
-Roll 1 dN-die per unit base with either biological or biological crew description (without immunity from poison or immunity from poison cloud), if you get above (n+poison_resistance) of the unit, the unit base is pinned. 

If placing a poison cloud in a hex with a poison cloud already,
increase  the density of the most dense cloud one step, and set the level equal to the highest level: Ie Poison Cloud[8](4+) + Poison Cloud[4](5+) = Poison Cloud[8](3+)

**Acid** **Cloud** [Minor/major] (n+)

Roll a die per unit base in hex. At n+ place a minor or major acid on the unit base.

**Poison** & **Acid** **Cloud** [n, minor/major] = poison Cloud[n] + acid Cloud [minor/major]



**Hex** **on** **Fire**\
Roll 1 die when per unit base, at 5+ set that unit base on fire.

- At agony step 4: Remove Fire at hex. Replace any forest with rough terrain. Place TWO smoke markers in hex.

Units under the effect of acid, fire and poison are cumulative with both with itself and each other. Roll separate dice for each instance.



**AFTERMATH**: \
Remove one \* Cloud or smoke marker of each type in hex

Remove one pinned/stunned token from unit base.



