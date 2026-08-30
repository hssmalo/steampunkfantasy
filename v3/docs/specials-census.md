# Specials census: every identifier currently in use

Resolves [wayfinder ticket #115](https://github.com/hssmalo/steampunkfantasy/issues/115),
a child of map [#111](https://github.com/hssmalo/steampunkfantasy/issues/111) (Wayfinder:
the Special data model). Counted directly from `races/*.toml` (all eight race
files) against `rules/special.toml`, `rules/to_hit.toml`, `rules/tokens.toml`
and `rules/hexes.toml`, measured 2026-08-23.

Grain is **one row per distinct label per slot** — the (slot, label) pair is
the lookup key (decision 4 on map #111: labels collide across slots). Where a
label's identity is genuinely disputed (wrong slot, absorbed elsewhere,
suffix-collapsed), the row still exists but its target id points elsewhere.

**Counts**: unit 48, model 6, assault 20, range 23 — **97 labels**, 1 more
than issue #101's 2026-08-19 snapshot (47/6/20/23 = 96); the data moved
between the two counts (recent commits reworded/added references). No
attempt is made to reconcile the exact delta — treat #101's counts as
historical, this census as current.

**Updated 2026-08-30** for the Extra Damage rework (ADR 0027): the assault and
range Extra Damage rules are now versioned over the kinds they apply, the six
kind-and-slot rules ADR 0024 anticipated are deleted, and four labels that never
were Extra Damage moved off it — three into stubs of their own, one onto the
existing `area` rule.

Legend for the **Category** column:
`slug` straight slug · `drift` wording drift to reconcile · `slot!` wrong slot ·
`multi` multi-slot · `hit` absorbed by to_hit.toml · `ref` points at a token/hex ·
`stat` becomes a stat modifier (#109) · `vocab` leaves the vocabulary (Note) ·
`suffix` suffix collapse · `orders` wants an orders ref, unavailable ·
`missing` genuinely missing rule text.

## Unit slot (48 labels)

| Label | Chosen id | Category | Notes |
|---|---|---|---|
| Activate | `activate` | orders | Orders-namespace intent; no rule today. |
| Camouflage | `to_hit` (version `camouflage`) | hit | `to_hit.toml#unit_ability.camouflage`; args `[terrain][-1]` already match the rule's `{speed}`-style shape (here keyed by terrain, not speed — note the mismatch, see judgement calls). |
| Chase | `chase` | orders | Orders-namespace intent; also the subject of `rules/orders_items.md`. |
| Darkelf Officer | `officer` (atmospheric name) | missing | No `officer` rule exists anywhere; also see Officer/Officer 2/Officer Order below — one missing rule family. |
| Elusive | `to_hit` (version `elusive`) | hit | Label was misspelled "Ellusive"; renamed to match the rule id `elusive`. |
| Enormous | `enormous` | missing | Bespoke per-unit mechanic (2-hex footprint); no shared rule. Naming collision with `to_hit.toml#size.enormous` (different concept) — flag. |
| Evasion | `evasion` | slug | `special.toml#unit.evasion`; label and rule were both misspelled "Evation" and are renamed. |
| Fire Order | `fire_order` | orders | Orders-namespace intent (49 occurrences — most-used unit label). |
| Fog | `fog` | multi | Two distinct meanings across races (impassable-hex chase rule vs to-hit-penalty rule) under one label — same multi-slot problem as the Bonus/Extra Damage/LoS/Spawn family, just within one slot instead of across slots. Flag. |
| Forward Position | `forward_position` | slug | `special.toml#unit.forward_position`. |
| Heads | `heads` | missing | Bespoke per-unit mechanic (functional head tracking); no shared rule. |
| Heal | `heal` | slug | `special.toml#unit.heal`. |
| Heal 2 | `heal` | suffix | Collapses onto `heal`; each occurrence becomes an instance. |
| Hidden | `hidden` | ref | **Correction to the ticket's own grouping**: `tokens.toml#hidden` already has a full rule; this is NOT missing/orders-unavailable despite being listed alongside Chase/Transport in the ticket body. Points at the token, doesn't need an orders ref. |
| Hypnotizing Gaze | `hypnotizing_gaze` | slug | `special.toml#unit.hypnotizing_gaze`. |
| Illusion | `illusion` | missing | Bespoke (elf), no shared rule. |
| Immunity | `immunity` | slug | `special.toml#unit.immunity`; `feature` variable is exactly the open `ref` namespace decision 7 describes. |
| LoS | `los` | multi + missing | Multi-slot per decision 3 (also range); no shared rule text exists in either slot. |
| Movement | `movement` | missing | Every occurrence is fully bespoke per-unit prose; no shared rule concept detected across any race. |
| Note | — | vocab | Leaves the vocabulary; becomes a free note field, not a special id. |
| Officer | `officer` | missing | See Darkelf Officer. |
| Officer 2 | `officer` | suffix + missing | Collapses onto `officer`. |
| Officer Order | `officer_order` | orders | Distinct from plain "Officer" — orders-namespace intent. |
| Pet | `pet` | missing | Bespoke (ogre), no shared rule. |
| Phoenix | `phoenix` | missing | Bespoke (goblin), no shared rule. |
| Poison Cloud | `hexes.poison_cloud` | ref | `hexes.toml#poison_cloud`. |
| Pre-Assault Retreat | `pre_assault_retreat` | slot! | **Wrong slot, opposite direction from Fear**: label used in *unit* slot, but the rule sits in `special.toml`'s **assault** section — and the rule file's own comment already says *"This should be a unit ability, because it does not make sense models of the same unit have different pre assault retreat."* Resolve by moving the rule to `[unit]`, consistent with that comment. |
| Protection | armor stat modifier | stat | Becomes a stat modifier via #109, not a special (decision 5). |
| Protection 2 | armor stat modifier | suffix + stat | Collapses onto the Protection stat-modifier instance. |
| Regeneration | `regeneration` | missing | Bespoke per-unit, though every occurrence composes with `Heal[...]` in its own prose — a real (if informal) dependency on `heal`. No shared `regeneration` rule exists. |
| Reload | `reload` | orders | Orders-namespace intent. |
| Repair | `repair` | slug | `special.toml#unit.repair`. |
| Repairing | `repairing` | missing | Distinct from Repair — bespoke per-unit extension text, references "repair ability" but has no rule of its own. |
| Resistance | `resistance` | slug | `special.toml#unit.resistance`; `versions` variable is the decision-8 versions-as-refs case. |
| Resistance 2 | `resistance` | suffix | Collapses; flag as extend (stacking resistance) vs replace — treat as extend absent evidence otherwise. |
| Resistance 3 | `resistance` | suffix | Same as Resistance 2. |
| Setup | `setup` | missing | Bespoke (deployment-timing text), no shared rule. Possible overlap with `forward_position`'s deployment context — flag. |
| Side Weapon | `side_weapon` | missing | Bespoke (abomination flagship), single occurrence. |
| Spawn | `spawn` | multi + missing | Multi-slot per decision 3 (also assault, range); no shared rule text in any slot. |
| Stacking Limit | `stacking_limit` | missing | Bespoke, single occurrence. |
| Steady | `to_hit` (version `steady`) | hit | `to_hit.toml#unit_ability.steady`. |
| Take Cover | `to_hit` (version `take_cover`) | hit | `to_hit.toml#unit_ability.take_cover`. |
| Terror | `terror` | slug | `special.toml#unit.terror`. |
| Tow | `tow` | missing | Bespoke (ogre), two flavors (tower vs towed) sharing one label — no shared rule. |
| Transfer | `transfer` | missing | Bespoke (darkelf), single occurrence. |
| Transport | `transport` | orders | Orders-namespace intent. |
| Trap | `trap` | ref | Points at `hexes.toml#drone_trap` / `hexes.toml#goblin_acid_trap` depending on race. |
| Vulnerability | `vulnerability` | missing | Bespoke per-unit, no shared rule; the eventual inverse-of-resistance mechanism decision 7's `ref` namespace could plausibly cover, but not yet designed. |

## Model slot (6 labels)

| Label | Chosen id | Category | Notes |
|---|---|---|---|
| Escape Artist | `escape_artist` | missing | No rule anywhere. |
| Fog | `to_hit` reference? | missing | Distinct meaning from the unit-slot "Fog" (to-hit penalty doubling in fog terrain) — closer to `to_hit.toml#terrain.fog` conceptually but no formal rule ties them. Flag. |
| Not Yet Dead | `not_yet_dead` | missing | No rule anywhere. |
| To Hit | `to_hit` | hit | The absorption target for all four To Hit variants below. |
| To Hit (2) | `to_hit` | suffix + hit | Collapses onto `to_hit`. |
| To Hit (3) | `to_hit` | suffix + hit | Collapses onto `to_hit`. |

`special.toml` has **no `[model]` section at all** (confirmed, matches #101 finding 5) — every model-slot label is either absorbed into `to_hit.toml` or missing.

### To Hit free-text census (absorbed group, the largest)

43 distinct free-text values were found across the 61 To-Hit-family occurrences (unit `To Hit`-adjacent equivalents don't exist; this group is model-slot only). Owner confirmed: "spelling and use of capital letters or not should be made consistent" — recommend Title Case display, snake_case ids, canonicalized against `to_hit.toml#unit_ability`.

**Clean matches** (wording-drift only — case/spelling variants of an existing `unit_ability` id):

| `unit_ability` id | Variant spellings found |
|---|---|
| `good_shot` | "Good Shot: +1 to hit", "Good shoot: +1 to hit", "Good shot, +1 to hit", "Good shot +1", "Good shot: +1", "good shot: +1 to hit", "Gains good shot: +1 to hit", "model gain good shoot: +1 to hit", "If a scout has line of sight to target, the unit gains good shot: +1 to hit" |
| `excellent_shot` | (only referenced compositely, see below) |
| `superb_shot` | "Superb shot: +3 to hit", "Great Shot: +2 to hit" (⚠ "Great Shot: +2" text-matches `excellent_shot`'s +2 value, not `superb_shot`'s +3 — likely mislabeled, see judgement calls) |
| `bad_shot` | "Bad shot, -1 to hit" |
| `terrible_shot` | "Terrible Shot: -2 to hit" |
| `enhanced_accuracy` | "Enhanced accuracy: +1 to hit", "enhanced accuracy: +1 to hit", "Enhanced Accuracy[Assault Musket]: +1 to hit", "Enhanced accuracy[Heavy Crossbow]: +1 to hit", "Enhanced accuracy. +1 to hit", "Gives all weapons the enhanced accuracy (+1 to hit) trait" |
| `optimal_at_point_blank` | "optimal Point blank: +1 to hit at point blank range" |

**Compound values** (reference two or more `unit_ability` ids in one instance — needs the instance-args shape from #112 to express, not a single id):

- "Good Shot: +1 to hit or Excellent Shot: +2 to hit if helicopter is hovering still in the air (still flying)." → `good_shot` OR `excellent_shot`, conditional.
- "Good Shot: +1 to hit, Negates to-hit penalty for shooting while moving fast" → `good_shot` + a bespoke "ignore fast penalty" clause.
- "Ignore to-hit penalty (both self and target) for moving fast and flying. Bad at long range: double to-hit penalties at long range. Enhanced accuracy: +1/+3/+5 to hit" (three variants, N varies) → `bad_at_long_range` + `enhanced_accuracy`, **but `enhanced_accuracy`'s to-hit value is hardcoded `+1` in `to_hit.toml`, while the data needs +1, +3, and +5** — the rule needs a variable, not a fixed value. Flag.
- "Ignore to-hit penalties for moving fast" → bespoke, no matching id.
- "Excellent Whip Handling (counts as Excellent shot, +2 to hit)" → `excellent_shot` with an atmospheric name (exactly decision 9's worked example).

**No existing `unit_ability` home** (genuinely missing rule text, or a new `unit_ability` entry is needed):

"+1 to hit if range to enemy is an even number, -1 to hit if it is an odd number"; "+2 to hit if using seeker arrow"; "+2 to hit with thrown weapons"; "Double to-hit bonuses and penalties for movement speed, both for you and the target" (×2); "Enhanced Arrow: +2 to hit"; "Expert throw: +2 to hit while throwing pyro grenade"; "Flagship gains +1 to hit while having an out of fog token"; "Get +1 to hit for thrown weapons"; "Guided[Guided Missile]: +4 to hit"; "Imprecise weapon[Bow Battery]: -1 to hit"; "Inaccurate: -1 to Hit"; "Loses aim when moving away from the hex where it aimed"; "Need command: -2 to hit if unit is not connected to a main engine"; "Reroll 2 dice in ranged combat per natural 6 rolled for to-hit…".

## Assault slot (20 labels)

| Label | Chosen id | Category | Notes |
|---|---|---|---|
| Angle | `angle` | missing | Armor-piercing-angle mechanic ("ap 2 from non-front arcs") — unrelated to `to_hit.toml#angle.on_edge` despite the name; no shared rule. Naming collision, flag. |
| Bonus | `bonus` | multi + missing | Multi-slot (also range); no shared rule text in either slot. |
| Bonus 2 | `bonus` | suffix + missing | Collapses onto `bonus`. |
| Counter Attack | `counter_attack` | missing | No rule anywhere. |
| Cunning Assault | `cunning_assault` | slug | `special.toml#assault.cunning_assault`. |
| Cunning Assault Defense | `cunning_assault_defense` | slug | `special.toml#assault.cunning_assault_defense`; the rule's British spelling was the one outlier and is renamed to the American spelling the repo standardizes on. |
| Cunning Deflection | `cunning_deflection` | missing | No rule; name is close to Cunning Assault Defense — possibly the same ability under two names, possibly genuinely distinct. Flag. |
| Damage on Deflect | `damage_on_deflect` | missing | No rule anywhere. |
| Extra Damage | `assault_extra_damage` | slug | Written, versioned over `token` and `damage_type` (ADR 0027). The range label is a separate rule, not a multi-slot one. Two occurrences were never extra damage and became stubs of their own: `weakest_armor` (elf) and `crew_damage` (ork, a *substitution* of the regular damage). |
| Extra Damage 2 | `assault_extra_damage` | suffix | Collapses onto `assault_extra_damage`; each occurrence becomes an instance. |
| Fear | `fear` | slot! | **Confirmed by owner**: rule sits in `special.toml`'s unit section but the label is assault-only; move the rule to `[assault]`. |
| FlyBy | `fly_by` | missing | No rule anywhere. |
| Improved Extra Damage | `assault_extra_damage` | suffix | Third member of the suffix-collapse family; the versioned rule expresses every occurrence, so the flag is settled. |
| Lands | `lands` | missing | No rule anywhere. |
| Ork Reroll | `reroll` | slug | `special.toml#assault.reroll` already has `name = "Ork Reroll"` — exact match on name, only the internal id (`reroll` vs a more descriptive `ork_reroll`) is a style choice, not a drift problem. |
| Overrun | `overrun` | missing | No rule anywhere (also flagged by #101 as an example of missing text). |
| Penalty | `penalty` | missing | Presumed opposite of Bonus; no shared rule. |
| Retreat | `retreat` | missing | Distinct from Pre-Assault Retreat; no shared rule. |
| Size | `size` | missing | Auto-win-vs-smaller-units mechanic — unrelated to `to_hit.toml#size` (tiny/huge/enormous to-hit modifiers) despite the name. Naming collision, flag. |
| Stench | `stench` | missing | This is decision 9's own worked example ("Troll Stench") — atmospheric name over a mechanic that currently has no shared rule (grants Poison[6] + d8 crew damage inline). Could route through `assault_extra_damage` instead of bespoke text. |

## Range slot (23 labels)

| Label | Chosen id | Category | Notes |
|---|---|---|---|
| Ammo | `limited_ammo` | drift | `special.toml#range_.limited_ammo`; "Ammo" is the informal short form. |
| Area | `area` | missing | The `Area(N+)` mechanic appears repeatedly in `hexes.toml` effect prose but has no formal rule of its own — every hex effect re-describes it inline. Candidate for its own shared rule. One Extra Damage label (ogre `ogre_artillery`) turned out to be this rule and became an instance of it (ADR 0027). |
| Bonus | `bonus` | multi + missing | See assault. |
| Burst | `burst` | slug | `special.toml#range_.burst`. |
| Cloud | `hexes.fog` (or `hexes.poison_cloud`) | ref | Places a hex effect; which one depends on the weapon (fog vs poison cloud) — resolve per-instance, not per-label. |
| Critical | `critical` | slug | `special.toml#range_.critical`. |
| Drag | `drag` | missing | No rule anywhere. |
| Extra Damage | `range_extra_damage` | slug | Written, versioned over `token` and `damage_type` (ADR 0027). Flat where the assault rule counts hits, which is why the two are separate rules. Two occurrences were never extra damage: one is `area` (ogre), one became the `break` stub (abomination). |
| Focus Fire | `focus_fire` | missing | Modifies how the `aim` token is used ("instead of aim, roll 6 dice"); related to `tokens.toml#aim` but not itself a token — no shared rule. |
| Fumble | `fumble` | slug | `special.toml#range_.fumble`. |
| Improved Aim | `improved_aim` | missing | Modifies `tokens.toml#aim`'s bonus (+4 instead of +2, stacking); related but no shared rule ties them together today. |
| Indirect Fire | `indirect_fire` | missing | No rule anywhere. |
| Insanity | `insanity` | missing | Grants an "Insane" token (`tokens.toml#insane`) via psychic damage — conceptually close to `special.toml#unit.insanity_field`, but that's unit-slot and this is range-slot. Possible wrong-slot or points-at-rule case; flag rather than guess. |
| LoS | `los` | multi + missing | See unit slot. |
| Multiple Shots | `multiple_shots` | missing | No shared rule; text is close enough to `burst`'s "fired N times" mechanic that the two may be duplicates under different names. Flag. |
| Multipurpose | `multipurpose` | missing | Bespoke, equipment-flavor text (abomination/gnome multipurpose weapons); no shared rule. |
| Note | — | vocab | Leaves the vocabulary. |
| Order | `order` | missing | Weapon-specific firing-order restriction (e.g. "used with Throw order") — **name collides with the future `orders` ref namespace (decision 7) but is a different concept**; needs a name that won't collide once `orders` exists. Flag. |
| Range | `range` | missing | Weapon range-value modifier text; no shared rule. |
| Recoil | `recoil` | missing | No rule anywhere. |
| Sniper | `sniper` | missing | No rule anywhere (also flagged by #101). |
| Spawn | `spawn` | multi + missing | See unit slot. |
| Type | `type` | missing | Generic weapon-type flavor text; no shared rule. |

## The 15 rules #101 found unreachable — reachability under this census

| Rule | 2026-08-19 (per #101) | Now |
|---|---|---|
| `assault.reroll` (#101 called it `reroll_assault`; current key is `reroll`) | unreachable | **Reachable** — "Ork Reroll" matches by `name`. |
| `assault.fire` → `assault_fire` (#113) | unreachable | **Deleted** (ADR 0027) — the kind it named is a version of Extra Damage, not a rule. It never had an instance. |
| `assault.minor_acid` → `assault_minor_acid` (#113) | unreachable | **Deleted** (ADR 0027) — the kind it named is a version of Extra Damage, not a rule. It never had an instance. |
| `assault.poison` → `assault_poison` (#113) | unreachable | **Deleted** (ADR 0027) — the kind it named is a version of Extra Damage, not a rule. It never had an instance; "Stench" grants Poison[6] inline and could route through `assault_extra_damage` instead. |
| `assault.cunning_assault_defense` | unreachable | **Reachable** — "Cunning Assault Defense" matches once the spelling drift is reconciled. |
| `assault.gear_disruption` → `assault_gear_disruption` (#113) | unreachable | **Reachable** — the Gear Disruption clauses inside assault Extra Damage labels are instances of it (ADR 0027). Still distinct from `range_gear_disruption`: the assault form counts hits. |
| `assault.pre_assault_retreat` | unreachable | **Reachable, but wrong slot** — "Pre-Assault Retreat" is a unit label; the rule's own comment already calls for moving it to `[unit]`. |
| `unit.hide` | unreachable | Still unreachable — no unit label named "Hide" exists (the actual "Hidden" label points at `tokens.hidden` instead, a different rule entirely). `unit.hide`'s `terrain` variable looks orphaned; flag for a decision on whether it's dead or meant to converge with Hidden. |
| `unit.insanity_field` | unreachable | Still unreachable by exact label — Horror's "Terror" label carries the insanity-field text in free prose instead (the exact case #101 flagged). Decision 9's atmospheric-name instance shape is the natural fix, but that's a design decision for a grilling ticket, not settled here. |
| `unit.fear` | unreachable | **Reachable, confirmed wrong slot** — moves to `[assault]` per the owner's comment. |
| `range_.fire` → `range_fire` (#113) | unreachable | **Deleted** (ADR 0027) — the kind it named is a version of Extra Damage, not a rule. It never had an instance. |
| `range_.minor_acid` → `range_minor_acid` (#113) | unreachable | **Deleted** (ADR 0027) — the kind it named is a version of Extra Damage, not a rule. It never had an instance. |
| `range_.poison` → `range_poison` (#113) | unreachable | **Deleted** (ADR 0027) — the kind it named is a version of Extra Damage, not a rule. It never had an instance. |
| `range_.limited_ammo` | unreachable | **Reachable** — "Ammo" matches once the wording drift is reconciled. |
| `range_.gear_disruption` → `range_gear_disruption` (#113) | unreachable | **Reachable** — the Gear Disruption clauses inside range Extra Damage labels are instances of it (ADR 0027). |

**7 of the 15 become reachable outright** (reroll, cunning_assault_defense,
limited_ammo — by wording drift; pre_assault_retreat, fear — by slot fix; the two
Gear Disruption rules — by reading the Extra Damage labels as instances). **6 are
deleted** rather than made reachable: ADR 0027 supersedes #113's "four rule pairs"
consequence, because the kinds an Extra Damage applies are a namespace, not
Specials — every one of those six rules had zero instances and none was ever
written by hand. #113's other half stands: the assault forms count hits and the
range forms are flat, which is why Extra Damage is two rules and not one.
**2 stay genuinely orphaned** (`unit.hide`, `unit.insanity_field`) pending design
decisions outside this ticket's scope.

## Missing-rule-text count (decision 2 stub countdown)

**47** distinct ids need a TODO stub, counting each suffix-collapsed family once —
`officer` (Darkelf Officer/Officer/Officer 2), `enormous`, `heads`, `illusion`,
`movement`, `pet`, `phoenix`, `regeneration`, `repairing`, `setup`, `side_weapon`,
`spawn`, `stacking_limit`, `tow`, `transfer`, `vulnerability`, `fog` (model-slot
sense), `escape_artist`, `not_yet_dead`, `angle`, `bonus`, `counter_attack`,
`cunning_deflection`, `damage_on_deflect`, `fly_by`, `lands`, `overrun`,
`penalty`, `retreat`, `size`, `stench`, `weakest_armor`, `crew_damage`, `area`,
`break`, `drag`, `focus_fire`,
`improved_aim`, `indirect_fire`, `insanity`, `multiple_shots`, `multipurpose`,
`order`, `range`, `recoil`, `sniper`, `type`.

This is an **upper bound**: several of these are suspected duplicates of each
other pending the judgement calls below (Multiple Shots/Burst, Cunning
Deflection/Cunning Assault Defense) — each confirmed duplicate removes one id
from the count rather than adding a stub.

The count went **up** by two even though Extra Damage became a written rule:
`extra_damage` leaves the countdown, and `weakest_armor`, `crew_damage` and
`break` join it. That is the countdown working — four labels were hiding under
one id, and three of them have no rule text yet.

## Open judgement calls

Per the ticket's instruction, these are flagged rather than settled:

1. **`enhanced_accuracy`'s to-hit value is fixed at `+1` in `to_hit.toml`, but race data needs +1, +3, and +5** (three "bad at long range + enhanced accuracy" compound instances differ only in this number). The rule needs a variable, not a constant.
2. **"Great Shot: +2 to hit" text-matches `excellent_shot`'s value (+2), not `superb_shot`'s (+3)**, despite the superficial word "Great" suggesting the bigger bonus. Confirm which id it should map to before treating it as a clean spelling-only match.
3. **Compound To Hit values need the instance-args shape from #112** to express "id A or id B, conditional" and "id A plus a bespoke clause" — flagging that the census surfaced real cases needing that shape, not asking to resolve the shape here.
4. ~~Four rule pairs in `special.toml` (`fire`, `minor_acid`, `poison`, `gear_disruption`) look like multi-slot merge candidates~~ — **settled by [#113](https://github.com/hssmalo/steampunkfantasy/issues/113)**, then half-superseded by **ADR 0027**: fire, minor acid and poison are not rules at all but the kinds Extra Damage applies, and their six rules are deleted. Gear disruption stays a rule, and stays two rules, for #113's reason.
5. **`unit.hide` looks orphaned.** No label named "Hide" exists; "Hidden" (a different label) already resolves cleanly to `tokens.hidden`. Is `unit.hide` dead, or does something still need to reference it?
6. **`unit.insanity_field` stays unreachable by exact label** — Horror's "Terror" label carries insanity-field content in free prose instead. The natural fix is decision 9's atmospheric-name instance shape (an instance of `terror` with a local name/version), but that's a modeling decision for a grilling ticket, not this census.
7. **Possible label duplicates, name closeness only — not confirmed:**
   - "Cunning Deflection" vs "Cunning Assault Defense" (assault) — same ability, two names, or genuinely distinct?
   - "Multiple Shots" (range) vs "Burst" (range) — both describe firing N times; duplicate or distinct?
8. **Naming collisions with concepts this map is about to formalize** (not duplicates, just names that will be confusing once the referenced concept exists):
   - Assault "Angle" and "Size" both collide by name with `to_hit.toml`'s `[angle]`/`[size]` sections, which mean something unrelated (to-hit modifiers by firing angle / unit size category).
   - Range "Order" collides by name with the future `orders` ref namespace (decision 7) — it means "this weapon's firing-order restriction," not a unit order.
   - Unit "Fog" and Model "Fog" mean two different things (impassable-hex chase rule vs to-hit-penalty-doubling), which decision 3's multi-slot mechanism resolves structurally — but pick display names that don't require reading the slot to disambiguate.
9. **Camouflage's args use `[terrain]`, but `to_hit.toml#unit_ability.camouflage`'s note says "when unit is in the given terrain"** — consistent, but Take Cover/Elusive key off `[speed]` while Camouflage keys off `[terrain]`; worth confirming the `unit_ability` shape accepts either as its "condition" variable rather than being speed-only.
10. ~~**Cunning Assault Defense/Defence spelling**~~ — **settled**: the repo standardizes on American English, so the rule id and name became `cunning_assault_defense` / "Cunning Assault Defense", matching the label the race files already use.
11. **Regeneration composes `Heal[...]` in every occurrence's free text but has no rule of its own** — is it meant to become a formal wrapper rule (`regeneration` referencing `heal`), or stay bespoke prose that happens to mention Heal?
