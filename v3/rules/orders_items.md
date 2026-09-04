General:
- X/Y: Do either X or Y.
- (X): Order X is optional.
- X+Y: Do X and Y in either the same movement step or same gunnery phase. In case of assault, all assaults happens during X before you do Y. Apply any damage before you do Y. If you are shaken, the order is interrupted and Y is not carried out. In addition, you may not enter any contested hexes during Y, and you do nothing instead.



Movement Orders:
- F = forward
- L/R = rotate one click left or right
- B = Break, change to one speed slower.
- BB = Break twice, if optional, you may break once or twice as desired.
- B[X] = As Break, but set speed to a special case, described by a X.
- A = Accelerate, change to one speed faster
- A[X] = As accelerate, but set speed to a special case, described by a X.
- Rev: Reverse.
- - = no action
- Chs: Chase, move towards nearest enemy, taking current orders into account. Thus the unit moves one step closer to where the enemy is going to be this turn. Where a unit chases is determined after all decisions and special movement have been planned. However, ignore any enemy units which cannot be reached even if it stood still. Thus a land unit without having a flying speed available, ignore flying units when determining where it chases. Chase may specify special targets (such as specific type of enemy). If so, move one hex closer to the closest specified target instead of one hex closer to the closest enemy. If there are multiple hexes which are equally distance to target hex, you choose which to enter.
- Chs[target]: As Chs, but move towards nearest enemy of type target instead.

- Follow: Duplicate the movement order of the other unit it is sharing a hex with. If it does not share a hex with a friendly unit, treat this order as -.
- 360°: rotate in any direction you want.
- Flee: Move in any hex you like as long as you move further away from the enemy. If no such hex is available, move to a hex which is not closer to the enemy. If still no such hex is available, let your enemy move your unit to any hex they like.
- Help: move toward friendly unit which may be healed or repaired. If no such unit exist, move towards the nearest friendly unit of the type specified by in the special rules of the unit. If no such unit exist, move towards nearest friendly unit. If only unit alive, treat it as Flee. During Help orders you may swap the position with any friendly nearby biological unit. If you don't need to move in order to end up in a hex with an wounded unit at end of any movement phase, you may execute an heal[1, any, movement X] instead of moving.
- D: Drift. Move 1 hex in any direction, regardless of facing. But do not rotate the unit.
- Road: Move along the road. Facing is always along the road.
- Deploy: Place a transported unit within the specified range of the unit. Place the transported units facing away from this unit if range>0, else put it in same facing as this unit. Any unit having deploy orders should specify the range and if the unit can be deployed into an assault or not. If it cannot enter an assault as part of deploy, the target hex of the deployment must be an empty hex. Otherwise, enter an assault if hex is occupied.
- Aim: get aim tokens in movement phase.
- Random: scatters one hex in a random direction first movement phase, but keep the unit orientation. If it enters an hex with an enemy unit, enter an assault (as if assaulting from enemy from front). In slow mode the unit uses its engines to neutralize the effect of the weather.



Gunnery orders\
- Load: loads weapon. A weapon cannot fire without a load token available. Some weapons may load more than one ammo per loading. It is then noted as Load[2] or Load[5]
- Aim: get aim tokens.
- Fire: fire at an enemy within line of sight and within a legal firing angle of a unit.
- Fire(X): As fire, but only use the specified weapons. The unit should have a fire order special describing which weapons to use.
- Throw: Same as fire, but for thrown weapons.
- Spot: try to reveal a hidden unit. Roll a normal to-hit as if you were shooting. If successful the hidden unit is revealed.
