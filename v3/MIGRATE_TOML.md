# Migrating Legacy Race TOML Files

This guide covers the changes needed to bring a legacy race TOML file into the current validated format. Run `uv run spf race show <race>` after each step to see remaining errors.

## 1. Remove the race namespace prefix

Legacy files nest all sections under `[race.units.*]`, `[race.models.*]`, and `[race.equipment.*]`. The schema expects top-level tables.

```toml
# Before
[ork.units.troll]
[ork.models.grunt]
[ork.equipment.ork_musket]

# After
[units.troll]
[models.grunt]
[equipment.ork_musket]
```

This is a mechanical find-and-replace across the whole file.

## 2. Convert every `special` from list to dict

All `special` fields changed from `list[str]` to a `dict[<Literal>, str]`. Each list
item must become a key-value pair in a TOML subtable, keyed by a valid literal from
`src/spf/schemas/type_aliases.py`. There are **five** distinct special fields, each
with its own literal type:

| Location | TOML subtable | Literal type |
|---|---|---|
| Unit | `[units.X.special]` | `UnitSpecial` |
| Model (model-level trait) | `[models.X.special]` | `ModelSpecial` |
| Model (grants unit ability) | `[models.X.unit_special]` | `UnitSpecial` |
| Assault (unit/model/equipment) | `[...assault.special]` | `AssaultSpecial` |
| Range (equipment) | `[equipment.X.range.special]` | `RangeSpecial` |

```toml
# Before
[units.grunt]
special = ["Forward Position[2]", "Cannot use ranged weapons"]

# After
[units.grunt]
[units.grunt.special]
"Forward Position" = "[2]"
"Fire Order" = "Cannot use ranged weapons"
```

**Key mapping guidelines:**
- Strip the parameter from the key: `"Forward Position[2]"` → key `"Forward Position"`, value `"[2]"`
- Use the ability name before the colon as the key: `"Regeneration[3]: Heal[...]"` → key `"Regeneration"`, value `"[3]: Heal[...]"`
- Combine related items under one key where they describe the same ability (dict keys must be unique — two list items that map to the same key must be merged into one value)
- If no existing literal fits, add a new one to the appropriate type in `type_aliases.py`

**Model `special` vs `unit_special`:** a trait the model has itself (e.g. `"good shot: +1 to hit"` → `ModelSpecial` `"To Hit"`) goes under `[models.X.special]`. A trait the model *grants to its whole unit* (e.g. `"unit gains psychic resistance 2 while an elite is alive"`, `"Unit gains: Repair[...]"`, endurance tokens → `"Protection"`) goes under `[models.X.unit_special]` keyed by `UnitSpecial`.

**Legacy equipment-level `special`:** `EquipmentConfig` has no top-level `special` field. Distribute each item into `unit_special`, `model_special`, `assault.special`, or `range.special` by what it affects (e.g. armor/endurance the unit gains → `unit_special`; a reload-after-assault note on a gun → `range.special` `"Ammo"`).

Any entry with no specials needs no subtable (the field defaults to an empty dict). An empty `special = []` inside a `range` block should simply be deleted.

Always ask if a key is ambiguous or is missing from the literal type. It's possible to add new literals, but only do so if the user confirms.

## 3. Fix `size` casing

`size` must match the `Size` literal exactly. All values are Title Case.

| Wrong | Correct |
|---|---|
| `"huge"` | `"Huge"` |
| `"medium"` | `"Medium"` |
| `"small"` | `"Small"` |
| `"large"` | `"Large"` |
| `"lagre"` | `"Large"` |

## 4. Fix `DamageTableName` keys

Damage table keys must be **lowercase**. The valid names are: `regular`, `critical`, `crew`, `psychic`, `inner`.

```toml
# Before
[units.foo.damage_tables]
Regular = [...]
Critical = [...]
psycic = [...]   # also a typo

# After
[units.foo.damage_tables]
regular = [...]
critical = [...]
psychic = [...]
```

## 5. Fix `ModelType` casing in model `type` arrays

All model type values must match the `ModelType` literal. Common corrections:

| Wrong | Correct |
|---|---|
| `"infantry"` | `"Infantry"` |
| `"cavalry"` | `"Cavalry"` |
| `"elite"` | `"Elite"` |
| `"bio"` | `"Bio"` |
| `"grunt"` | `"Grunt"` |
| `"walks"` / `"Walks"` | `"Walking"` |
| `"tracks"` / `"Track"` | `"Tracked"` |
| `"mechanical"` | `"Mechanical"` |
| `"bio crew"` | `"Bio Crew"` |
| `"vehicle"` | `"Vehicle"` |
| `"monster"` | `"Monster"` |

See `src/spf/schemas/type_aliases.py` for the full list.

Ask the user if you come across a new `ModelType`.

## 6. Fix `EquipmentHolder` casing in `equipment_limit` and `requires`

Equipment limit strings and requires holder keys must use Title Case:

```toml
# Before
equipment_limit = ["hands:2", "independent:∞", "shared:1"]
requires = [["type:infantry", "type:grunt"], ["hands:1"]]

# After
equipment_limit = ["Hands:2", "Independent:∞", "Shared:1"]
requires = [["type:Infantry", "type:Grunt"], ["Hands:1"]]
```

Valid holders: `Hands`, `Independent`, `Shared`, `Grenades`, `Mechanical Tentacles`, `Specialization`, `Tentacles`.

Note: `type:X` values in `requires` must also match `ModelType` casing (see step 5).

## 7. Fix the `race` field casing in models and equipment

The `race` field must be the lowercase race name.

```toml
# Before
race = "Ork"

# After
race = "ork"
```

## 8. Add missing required fields

### `shaken` on units
`UnitConfig.shaken` is required and is now a structured `ShakenConfig` subtable, **not** a
string. Parse the legacy sentence into fields:

```toml
# Before
shaken = "Movement set to slow. Movement order: [-,-,flee]. May not fire weapons"

# After
[units.X.shaken]
speed = "slow"                     # Speed literal (see below); required
movement_order = ["-", "-", "flee"]  # MovementOrder list; required
# fire_order = "Normal"            # optional; defaults to "Can't use weapons".
                                   # Set it only when the unit CAN fire while shaken.
# comment = "..."                  # optional free text for any leftover clause
```

Fields:
- `speed` — the Speed the unit drops to (from "Movement/Speed set to X"). Must be a valid
  `Speed` literal. If the legacy text gives no speed, use the unit's own movement speed and
  confirm with the user. Note the `Speed` spellings: it's `fast_flying` / `slow_flying` /
  `still_flying` (not `flying_fast`). The same literals key `orders.movement` /
  `orders.fire` and must be corrected there too.
- `movement_order` — the `[-,-,flee]`-style order as a list of strings.
- `fire_order` — defaults to `"Can't use weapons"`. Only set it when the unit may still fire
  (e.g. `"Normal"`, or a rule like `"Fire one less weapon system per shaken token."`).
- `comment` — any remaining clause (e.g. `"May not deploy units while shaken"`).

### `equipment` on models
`ModelConfig.equipment` is required. Models with no equipment need:

```toml
equipment = []
```

### `equipment_limit` on models
`ModelConfig.equipment_limit` is required. Vehicle/weapon models without explicit limits need at least:

```toml
equipment_limit = ["Independent:∞"]
```

## 9. Fix `ap` field types in assault configs

`ap` must be `int` or the string `"N/A"`. String integers and dashes are not valid:

```toml
# Before
ap = "2"   # string integer
ap = "-"   # meaning N/A

# After
ap = 2
ap = "N/A"
```

If `ap` varies by arc (e.g. `"10 (from front), else 2"`), use the primary value as an integer and document the variation in the `special` dict (see step 2).

## 10. Fix `replaces` field

`replaces` must be a single model name string, not a list:

```toml
# Before
replaces = ["ork_infantry"]

# After
replaces = "ork_infantry"
```

## 11. Convert `special.append` in equipment assault/range configs to a dict

Equipment `assault.special` and `range.special` are now `dict[<Literal>, str]`, not a
`Stacker`. The numeric stat fields (`strength`, `deflection`, `damage`, `ap`, …) are still
`Stacker`s and keep their `.add` / `.replace` / `.extend` keys — but any `special.append`
(or `special = [...]`) must become a keyed subtable:

```toml
# Before
[equipment.wheeled_shieldwall.assault]
deflection.add = [1, 0, 0, 0]
special.append = "-1 in assault strength if speed is not still"

# After
[equipment.wheeled_shieldwall.assault]
deflection.add = [1, 0, 0, 0]

[equipment.wheeled_shieldwall.assault.special]
"Penalty" = "-1 in assault strength if speed is not still"
```

## 12. Fix movement order `all` entries

Each element of a movement/fire order list must itself be a list:

```toml
# Before
all = ["As unit it came from"]

# After
all = [["As unit it came from"]]
```

## 13. Handle `default.*` movement entries

TOML keys like `default.slow = ["-", "-", "Flee"]` create a nested dict structure that the schema cannot parse. Comment them out until the schema gains support for default orders:

```toml
# default.slow = ["-", "-", "Flee"]
```

## 14. Set `upgrade_all` on every equipment with a `cost`

`EquipmentConfig` requires that `upgrade_all` is set **if and only if** `cost` is set. Any
priced equipment that lacks `upgrade_all` fails validation with:

> `'upgrade_all' must be set if and only if 'cost' is set`

`upgrade_all` is a pricing rule: `true` charges the `cost` once per unit; `false` charges it
per model (cost × number of models in the unit). Free equipment (no `cost`) must **not** set
it.

```toml
[equipment.heavy_musket]
cost.cp = 8
upgrade_all = true   # or false for per-model pricing
requires = [["Hands:2"], ["type:Infantry"]]
```

This is a game-balance decision — confirm the intended value (or a per-category default) with
the user rather than guessing.

## Verification

After migrating, run the full check:

```bash
uv run spf race show <race>
uv run pytest
uv run pyright
uv run ruff check src/
```

Finally, add the race to the `validate` recipe in the `justfile` (a
`uv run spf race show <race> > /dev/null` line) so `just validate` / `just check` guard it
against regressions. The race then also shows up in `uv run spf race list`.
