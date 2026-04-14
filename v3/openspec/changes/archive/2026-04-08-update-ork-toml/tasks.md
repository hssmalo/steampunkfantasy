## Tasks

- [x] Task 1: Extend UnitSpecial with new literals — add `"Regeneration"` and `"Hans Sverre's second favorite rule"` to `UnitSpecial` Literal in `src/spf/schemas/type_aliases.py`
- [x] Task 2: Remove `ork.` namespace prefix — replace all `[ork.units.`, `[ork.models.`, `[ork.equipment.` headers in `races/ork.toml`
- [x] Task 3: Convert unit special lists to dict subtables — replace `special = [...]` on each unit with `[units.xxx.special]` TOML subtable using key mappings from design.md
- [x] Task 4: Fix size field casing — `"huge"` → `"Huge"`, `"medium"` → `"Medium"` on affected units
- [x] Task 5: Fix damage table name casing — `Regular` → `regular`, `Critical` → `critical`, `psycic` → `psychic`
- [x] Task 6: Fix ModelType casing and spelling — correct all `type` arrays per model (see design.md mapping table)
- [x] Task 7: Fix race field casing in models — `race = "Ork"` → `race = "ork"` for hammerhead and battlewagon
- [x] Task 8: Add missing `shaken` fields to units — add `shaken = ""` to all units that lack it
- [x] Task 9: Fix missing and incorrect model fields — add `equipment = []` to warg_rider model; rename `equipment_limit` → `equipment_limit` on hammerhead model
- [x] Task 10: Fix `ap` field types in model assault configs — string integers → int, `"-"` → `"N/A"`, hammerhead `"10 (from front), else 2"` → `ap = 10` plus special string
- [x] Task 11: Verify — `uv run spf show-race ork`, `uv run pytest`, `uv run pyright`, `uv run ruff check src/`

### Task detail

#### Task 1
`src/spf/schemas/type_aliases.py` — add to `UnitSpecial` Literal:
- `"Regeneration"`
- `"Hans Sverre's second favorite rule"`

#### Task 2
`races/ork.toml` — mechanical find-and-replace:
- `[ork.units.` → `[units.`
- `[ork.models.` → `[models.`
- `[ork.equipment.` → `[equipment.`

#### Task 3
`races/ork.toml` — convert specials for each unit:

**troll** (remove `special = [...]`, add subtable):
```toml
[units.troll.special]
"Forward Position" = "[1]"
"Regeneration" = "[3]: Heal[3, self, 1st Healing]. While unconscious, you gain improved regeneration which gives Heal[3, self, 2nd Healing] in addition to the normal regeneration. The Troll does no action while unconscious, but regains conscious in end phase: remove unconscious in Healing 2 phase"
"Resistance" = "Acid [5+], Poison [2]"
"Hans Sverre's second favorite rule" = "May have a maximum of 1 unconscious token"
"Fire Order" = "Always fire: The troll Always fires its Troll Gatling Gun in forward arc at friendly or enemy units, both in the first and second fire phase. Only exception is if it unconscious"
"To Hit" = "Terrible Shot: -2 to hit with ranged weapons"
"Hans Sverre's favorite rule" = "Out of ammo: At the end of the game, the troll runs out of ammo"
```

**champion** (remove `special = [...]`, add subtable):
```toml
[units.champion.special]
"Hans Sverre's favorite rule" = "Has same orders available as the unit base it awakened from, and the same weapons as the last surviving model of the unit base"
```

**warg_rider** (remove `special = [...]`, add subtable):
```toml
[units.warg_rider.special]
"Fire Order" = "only available if given ranged weapons"
```

**battlewagon** (remove `special = [...]`, add subtable):
```toml
[units.battlewagon.special]
"Transport" = "[2]: may transport up to 2 infantry. unload all infantry in any movement phase: place up to 1 infantry in the same hex as the ending hex of the battlewagon, and the rest in an adjacent hex. Enter assault if occupied by en enemy. Put the infantry in either slow or still. Treat all movement order up to this point as - for the unloaded infantry."
```

**grunt** (remove `special = [...]`, add subtable):
```toml
[units.grunt.special]
"Forward Position" = "[2]"
"Fire Order" = "Cannot use ranged weapons"
```

**ork_werewarg** (remove `special = [...]`, add subtable):
```toml
[units.ork_werewarg.special]
"Take Cover" = "[still][-2]"
"Regeneration" = "[2] = Healing[2, self, 2nd Healing]. Instead of Healing normal effect, use 2 healing points to revive a fallen model, but at a cost of +1 to future damage token. Regeneration works even if all models are killed, and only stops if unit is permanently destroyed."
"Resistance" = "Poison [2]. When all models are killed, treat unit as still for to-hit penalties."
```

**bioengineered_ork**: remove the commented-out `#special = [...]` lines entirely.

#### Task 4
`races/ork.toml` — fix `size`:
- troll: `"huge"` → `"Huge"`
- champion, warg_rider, grunt, ork_werewarg, bioengineered_ork: `"medium"` → `"Medium"`

#### Task 5
`races/ork.toml` — fix damage table keys:
- `ork_char_b1`: `Regular` → `regular`, `Critical` → `critical`
- `warg_rider`: `psycic` → `psychic`

#### Task 6
`races/ork.toml` — fix model `type` arrays:
- `grunt`: `["bio", "grunt", "walks"]` → `["Bio", "Grunt", "Walking"]`
- `ork_infantry`: `["infantry", "walks"]` → `["Infantry", "Walking"]`
- `ork_elite_infantry`: `["elite", "infantry", "walks"]` → `["Elite", "Infantry", "Walking"]`
- `ork_werewarg`: `["infantry", "walks", "elite", "werewarg"]` → `["Infantry", "Walking", "Elite", "Monster"]`
- `champion`: `["elite", "infantry", "walks"]` → `["Elite", "Infantry", "Walking"]`
- `warg_rider`: `["bio", "cavalry", "elite", "Walks"]` → `["Bio", "Cavalry", "Elite", "Walking"]`
- `hammerhead`: `["vehicle", "mechanical", "bio crew", "tracks"]` → `["Vehicle", "Mechanical", "Bio Crew", "Tracked"]`
- `battlewagon`: `["vehicle", "mechanical", "bio crew", "tracks"]` → `["Vehicle", "Mechanical", "Bio Crew", "Tracked"]`
- `bioengineered_ork`: `["bio", "infantry", "walks"]` → `["Bio", "Infantry", "Walking"]`
- `elite_bioengineered_ork`: `["bio", "infantry", "walks", "elite"]` → `["Bio", "Infantry", "Walking", "Elite"]`
- `ork_char_b1`: `["Mechancical", "Bio Crew", "Vehicle", "Track"]` → `["Mechanical", "Bio Crew", "Vehicle", "Tracked"]`
- `speedhead`: `["Mechanical", "Bio Crew", "Vehicle", "Track"]` → `["Mechanical", "Bio Crew", "Vehicle", "Tracked"]`
- `troll`: `["monster", "walks"]` → `["Monster", "Walking"]`

#### Task 7
`races/ork.toml` — fix `race` field in models:
- `hammerhead`: `race = "Ork"` → `race = "ork"`
- `battlewagon`: `race = "Ork"` → `race = "ork"`

#### Task 8
`races/ork.toml` — add `shaken = ""` to units: troll, champion, warg_rider, speedhead, hammerhead, battlewagon, grunt, bioengineered_ork, ork_char_b1

#### Task 9
`races/ork.toml`:
- `warg_rider` model: add `equipment = []`
- `hammerhead` model: `equipment_limit` → `equipment_limit`

#### Task 10
`races/ork.toml` — fix all `ap` values in `[models.*.assault]`:
- `"2"` or `"3"` strings → integers `2`, `3`
- `"-"` → `"N/A"`
- hammerhead: `"10 (from front), else 2"` → `ap = 10`, and add `"ap 2 (from non-front arcs)"` to `special` list

#### Task 11
Verify:
```bash
uv run spf show-race ork
uv run pytest
uv run pyright
uv run ruff check src/
```
