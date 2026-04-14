## Why

`Cost` is a core data type but lacks arithmetic operations, forcing ad-hoc helper functions (`_add_cost`) and manual field-by-field multiplication throughout the codebase. The points formula (`mp + cp + xp + 3 * ip`) is also duplicated rather than owned by `Cost` itself.

## What Changes

- Add `__add__` and `__radd__` to `Cost` to support `a + b` and `sum([...], start=Cost())` syntax
- Add `__mul__` and `__rmul__` to `Cost` to support `cost * n` and `n * cost` syntax
- Add `to_points()` to `Cost` to encapsulate the canonical points formula
- Remove the private `_add_cost` helper from `armies/data.py` in favour of `+`
- Simplify manual field-by-field multiplication sites to use `cost * n`
- Update `unit_points` to delegate to `cost.to_points()`

## Non-goals

- No changes to the four cost dimensions (`mp`, `cp`, `xp`, `ip`) or their meaning
- No new CLI commands or display changes
- No changes to TOML format or serialisation

## Capabilities

### New Capabilities

- `cost-arithmetic`: Arithmetic operators (`+`, `*`) and `to_points()` on the `Cost` class

### Modified Capabilities

- `unit-cost`: `unit_points` requirement updated to delegate to `cost.to_points()`

## Impact

- `src/spf/schemas/type_aliases.py` — adds methods to `Cost`
- `src/spf/armies/data.py` — removes `_add_cost`, simplifies `unit_cost` and `total_cost`, updates `unit_points`
- Existing tests for `unit_cost` and `unit_points` continue to pass unchanged
