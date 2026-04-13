## Context

`races/ork.toml` was written in an older format where each section is prefixed with the race name (e.g. `[ork.units.troll]`). The current `RaceConfig` Pydantic schema expects top-level `[units]`, `[models]`, and `[equipment]` tables without any race prefix. Additionally, the schema changed `UnitConfig.special` from `list[str]` to `dict[UnitSpecial, str]`, requiring all unit specials to be expressed as TOML inline tables or subtables.

The schema also enforces strict Literals for `Size`, `ModelType`, `DamageTableName`, and `RaceName` — several values in ork.toml are wrong-cased or misspelled.

## Goals / Non-Goals

**Goals:**
- Make `uv run spf show-race ork` succeed without validation errors
- Extend `UnitSpecial` with two new literal values required by ork's rules
- Fix all casing, typos, and structural issues found in ork.toml

**Non-Goals:**
- Correcting game-rule text or descriptions
- Making ork a fully playable army (requires separate work)
- Updating other race files

## Decisions

### Section prefix removal
All `[ork.units.*]`, `[ork.models.*]`, and `[ork.equipment.*]` headers become `[units.*]`, `[models.*]`, and `[equipment.*]`. This is a mechanical rename throughout the file.

### Unit special conversion
`special = ["item1", "item2"]` list entries become TOML subtables:
```toml
[units.xxx.special]
"Key" = "value"
```
The full UnitSpecial key mapping for each unit (agreed with user):

**Troll**:
- `"Forward Position"` = `"[1]"`
- `"Regeneration"` = `"[3]: Heal[3, self, 1st Healing]. While unconscious, you gain improved regeneration which gives Heal[3, self, 2nd Healing] in addition to the normal regeneration. The Troll does no action while unconscious, but regains conscious in end phase: remove unconscious in Healing 2 phase"` (unconscious text merged in)
- `"Resistance"` = `"Acid [5+], Poison [2]"` (combined)
- `"Hans Sverre's second favorite rule"` = `"May have a maximum of 1 unconscious token"`
- `"Fire Order"` = `"Always fire: The troll Always fires its Troll Gatling Gun in forward arc at friendly or enemy units, both in the first and second fire phase. Only exception is if it unconscious"`
- `"To Hit"` = `"Terrible Shot: -2 to hit with ranged weapons"`
- `"Hans Sverre's favorite rule"` = `"Out of ammo: At the end of the game, the troll runs out of ammo"`

**Champion**:
- `"Hans Sverre's favorite rule"` = `"Has same orders available as the unit base it awakened from, and the same weapons as the last surviving model of the unit base"`

**Warg Rider**:
- `"Fire Order"` = `"only available if given ranged weapons"`

**Battlewagon**:
- `"Transport"` = `"[2]: may transport up to 2 infantry. unload all infantry in any movement phase: place up to 1 infantry in the same hex as the ending hex of the battlewagon, and the rest in an adjacent hex. Enter assault if occupied by en enemy. Put the infantry in either slow or still. Treat all movement order up to this point as - for the unloaded infantry."`

**Grunt**:
- `"Forward Position"` = `"[2]"`
- `"Fire Order"` = `"Cannot use ranged weapons"`

**Ork WereWarg**:
- `"Take Cover"` = `"[still][-2]"`
- `"Regeneration"` = `"[2] = Healing[2, self, 2nd Healing]. Instead of Healing normal effect, use 2 healing points to revive a fallen model, but at a cost of +1 to future damage token. Regeneration works even if all models are killed, and only stops if unit is permanently destroyed."`
- `"Resistance"` = `"Poison [2]. When all models are killed, treat unit as still for to-hit penalties."`

**BioEngineered Ork**: special was commented out — omit the subtable entirely (defaults to empty dict).

**Speedhead, HammerHead, Ork Char B1**: no unit-level specials in the original — omit the subtable.

### New UnitSpecial literals
Add to `type_aliases.py`:
- `"Regeneration"` — ork-specific regeneration mechanic
- `"Hans Sverre's second favorite rule"` — ork troll unconscious token limit

### Casing fixes
| Field | Wrong | Correct |
|---|---|---|
| `size` | `"huge"`, `"medium"` | `"Huge"`, `"Medium"` |
| `DamageTableName` | `"Regular"`, `"Critical"`, `"psycic"` | `"regular"`, `"critical"`, `"psychic"` |
| `ModelType` | `"grunt"`, `"bio crew"`, `"Walks"`, `"Mechancical"`, `"Track"`, `"Ork"` (race) | `"Grunt"`, `"Bio Crew"`, `"Walking"`, `"Mechanical"`, `"Tracked"`, `"ork"` |
| `race` | `"Ork"` (capital O in models) | `"ork"` |

### Missing fields
- `UnitConfig.shaken` is required (no default). Units missing it: `troll`, `champion`, `warg_rider`, `speedhead`, `hammerhead`, `battlewagon`, `grunt`, `bioengineered_ork`, `ork_char_b1`. Add `shaken = ""` (empty string) for those with no shaken rule specified.
- `ModelConfig.equipment` is required. `warg_rider` model is missing it — add `equipment = []`.
- `hammerhead` model has `equipment_limit` (wrong key) — rename to `equipment_limit`.

### ap field fixes
`ap` must be `int | "N/A"`. Model assault `ap` values that are strings like `"2"`, `"3"`, `"-"` must become integers or `"N/A"`. The value `"-"` means N/A → use `"N/A"`. For hammerhead's `"10 (from front), else 2"`: set `ap = 10` and append `"ap 2 (from non-front arcs)"` to the `special` list in `[models.hammerhead.assault]`.

## Risks / Trade-offs

- The `shaken = ""` placeholder is syntactically valid but semantically empty — these units genuinely have no shaken rule defined in the source. This is acceptable for now.
- The hammerhead `ap = 10` with `"ap 2 (from non-front arcs)"` in `special` preserves the directional nuance while satisfying the type constraint.
- Several ModelType values in the original (`"Walks"`) don't match any current Literal. `"Walking"` is the closest valid value.
