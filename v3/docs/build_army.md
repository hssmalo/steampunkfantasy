# Building Armies

The `spf.armies.build` module provides an API for assembling army lists in code. See
[`armies/build_scripts/showcase_goblin.py`](../armies/build_scripts/showcase_goblin.py)
for a complete working example.

## Overview

Army construction uses two tiers of types:

- **Build tier** (`ArmyList`, `ArmyUnit`, `ArmyModel`) — the assembly layer. All methods
  return new instances; nothing is mutated in place.
- **Resolved tier** (`Army`, `Unit`, `Model`) — the self-contained result. Call
  `ArmyList.resolve(race_config)` when the army is complete. After that, no `race_config`
  is needed for any further computation.

Typically, you only instantiate `ArmyList` and resolve to get an `Army`. The unit and model classes are created when you call the different methods shown below.

## Setup

```python
from spf import races
from spf.armies import ArmyList

cfg = races.get_race("goblin")
army = ArmyList("goblin", "Goblin Raiders", ())
```

## Adding Units

`add_unit(unit_name, race_config)` appends a unit in its default configuration — all model
slots filled with the unit's default models and no equipment upgrades applied.

```python
army = army.add_unit("goblin_infantry", cfg)
```

Units and models are referenced by `(name, occurrence_index)` keys. The first
`goblin_infantry` unit is `("goblin_infantry", 0)`, the second is `("goblin_infantry", 1)`,
and so on. The first `goblin_infantry` model within that unit is `("goblin_infantry", 0)`.

`add_unit` raises `ValueError` if the unit name is not found in the race config.

## Upgrading Model Types

Some units allow individual model slots to be replaced with a more powerful variant. The
replacement model's `replaces` field must match the name of the model being replaced.

### Upgrading a single model slot

```python
# Replace the first goblin_infantry model in unit 0 with elite_goblin_infantry
army = army.upgrade_unit(
    ("goblin_infantry", 0),   # unit key
    ("goblin_infantry", 0),   # model key within that unit
    "elite_goblin_infantry",
    cfg,
)
```

### Upgrading all model slots at once

When all models in a unit are the same type, `upgrade_full_unit` handles them in one call:

```python
army = army.upgrade_full_unit(("goblin_infantry", 0), "elite_goblin_infantry", cfg)
```

Both methods raise `ValueError` if the upgrade model cannot replace the target model.

## Adding Equipment

Equipment upgrades are added at the model level. Only equipment with a point cost and
whose requirements are satisfied by the model can be applied.

### Upgrading a single model

```python
# Add a gear_bow to the first model in unit 0
army = army.upgrade_model(
    ("goblin_infantry", 0),  # unit key
    ("goblin_infantry", 0),  # model key
    "gear_bow",
    cfg,
)
```

### Upgrading all models at once

```python
army = army.upgrade_all_models(("goblin_infantry", 0), "gear_bow", cfg)
```

Both methods raise `ValueError` if the equipment has no cost or its requirements are not
satisfied by the model.

## Duplicating and Removing Units

`duplicate_unit` appends a copy of an existing unit — including all upgrades applied so
far. Chain it to create multiple identical copies:

```python
# Build one elite unit, then make three copies
army = (
    army.add_unit("goblin_infantry", cfg)
    .upgrade_full_unit(("goblin_infantry", 0), "elite_goblin_infantry", cfg)
    .upgrade_all_models(("goblin_infantry", 0), "gear_bow", cfg)
    .duplicate_unit(("goblin_infantry", 0))
    .duplicate_unit(("goblin_infantry", 0))
    .duplicate_unit(("goblin_infantry", 0))
)
```

`delete_unit` removes a unit by key:

```python
army = army.delete_unit(("goblin_infantry", 2))
```

## Finding Available Options

Before upgrading, you can query what options are valid for a given model slot.

### Available model replacements

```python
from spf.armies import available_models

options = available_models(army, ("goblin_infantry", 0), ("goblin_infantry", 0), cfg)
for model in options:
    print(model)  # e.g. "elite_goblin_infantry"
```

Returns a list of names of models whose `replaces` field matches the current model.

### Available equipment upgrades

```python
from spf.armies import available_equipment

options = available_equipment(army, ("goblin_infantry", 0), ("goblin_infantry", 0), cfg)
for equipment in options:
    print(equipment) # e.g. "clockwork_wings", "poison_dagger", ...
```

Returns equipment that has a point cost and whose requirements are satisfied by the
model's current state. Note that default equipment (the model's base loadout) does **not**
consume equipment slots — slots are only counted against upgrades. This means a model with
a default two-handed weapon still has all its hand slots free for the first upgrade.

## Validation

Each build method validates its operation immediately and raises on failure, so invalid
armies cannot be constructed through the normal API.

For armies that are loaded from disk or constructed outside the normal flow,
`validate_army` checks the entire army at once and returns a list of error strings:

```python
from spf.armies import validate_army

errors = validate_army(army, cfg)
if errors:
    for error in errors:
        print(error)
```

An empty list means the army is valid.

## Resolving, Saving, and Printing

When the army is complete, resolve it to obtain a self-contained `Army` object:

```python
resolved = army.resolve(cfg)
```

After resolving, `cfg` is no longer needed. To display the army:

```python
from spf.armies import io

io.print_army(resolved)       # full army view
io.print_army_rules(resolved) # rules-reference view
```

To save and reload:

```python
io.save_army(army, "showcase/goblin")        # saves ArmyList to JSON
resolved = io.load_army("showcase/goblin")   # loads and resolves in one step
```

## Calculating Cost

Resolved armies, units, and models all expose a `cost()` method returning a `Cost` object:

```python
total = resolved.cost()
print(total)             # formatted string, e.g. "2mp 4cp"
print(total.to_points()) # integer point value

for unit in resolved.units:
    print(unit.name, unit.cost())
```

`Cost` has fields `mp`, `cp`, `xp`, and `ip` (manpower, craft, experience, and industry
points). `.to_points()` converts these to a single integer using the formula
`mp + cp + xp + 3 * ip`.
