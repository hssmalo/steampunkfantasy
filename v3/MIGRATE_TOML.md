# Migrating Legacy Race TOML Files

This guide covers the changes needed to bring a legacy race TOML file into the current validated format. Run `uv run spf show-race <race>` after each step to see remaining errors.

## 1. Remove the race namespace prefix

Legacy files nest all sections under `[race.units.*]`, `[race.models.*]`, and `[race.equipments.*]`. The schema expects top-level tables.

```toml
# Before
[ork.units.troll]
[ork.models.grunt]
[ork.equipments.ork_musket]

# After
[units.troll]
[models.grunt]
[equipments.ork_musket]
```

This is a mechanical find-and-replace across the whole file.

## 2. Convert unit `special` from list to dict

`UnitConfig.special` changed from `list[str]` to `dict[UnitSpecial, str]`. Each list item must become a key-value pair in a TOML subtable. The key must be a valid `UnitSpecial` literal (see `src/spf/schemas/type_aliases.py`).

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
- Combine related items under one key where they describe the same ability
- If no existing `UnitSpecial` literal fits, add a new one to `type_aliases.py`

Units with no specials need no subtable (the field defaults to an empty dict).

Always ask if the key is ambiguous or is missing from `UnitSpecial`. It's possible to add new literals, but only do so if the user confirms.

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

## 7. Fix the `race` field casing in models and equipments

The `race` field must be the lowercase race name.

```toml
# Before
race = "Ork"

# After
race = "ork"
```

## 8. Add missing required fields

### `shaken` on units
`UnitConfig.shaken` is required with no default. Units without a shaken rule need an explicit empty string:

```toml
shaken = ""
```

### `equipments` on models
`ModelConfig.equipments` is required. Models with no equipment need:

```toml
equipments = []
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

If `ap` varies by arc (e.g. `"10 (from front), else 2"`), use the primary value as an integer and document the variation in the `special` list.

## 10. Fix `replaces` field

`replaces` must be a single model name string, not a list:

```toml
# Before
replaces = ["ork_infantry"]

# After
replaces = "ork_infantry"
```

## 11. Fix `special.append` in equipment assault configs

`Stacker[list[str]].append` expects a list, not a string:

```toml
# Before
special.append = "Cunning assault[1 for 2]"

# After
special.append = ["Cunning assault[1 for 2]"]
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

## Verification

After migrating, run the full check:

```bash
uv run spf race show <race>
uv run pytest
uv run pyright
uv run ruff check src/
```

Finally, add the race to the list of working TOML files in AGENTS.md
