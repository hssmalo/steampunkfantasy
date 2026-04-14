## Why

Players need to know how many points each unit costs when building or reviewing an army list, so they can balance their forces within point limits. The current display shows total army cost but not per-unit points, making it tedious to evaluate individual unit value.

## What Changes

- Add a `unit_cost(unit, race_config)` function to `src/spf/armies/data.py` that returns the total `Cost` for a single unit (unit base cost + upgrade model costs + upgrade equipment costs).
- Add a `unit_points(unit, race_config)` function (or inline calculation) that converts a unit's total `Cost` to a single integer: `mp + cp + xp + 3 * ip`.
- Update `print_army()` in the army display module so each unit name line shows its point value in parentheses, e.g. `- Goblin Warriors (12 pts)`.

## Capabilities

### New Capabilities

- `unit-cost`: Function to compute the total cost and points value for a single army unit.

### Modified Capabilities

- `army-display`: Unit name lines now include point value in parentheses.

## Impact

- `src/spf/armies/data.py`: new `unit_cost` function; existing `total_cost` can delegate to it.
- Army display module (`print_army`): reads unit points and appends to unit bullet line.
- No schema changes, no new dependencies, no breaking API changes.

## Non-goals

- No per-model point breakdown in the display.
- No point limit validation or enforcement.
- No changes to how total army cost is calculated or displayed.
