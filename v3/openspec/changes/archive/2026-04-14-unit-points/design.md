## Context

`src/spf/armies/data.py` already has `total_cost(army, race_config)` which sums unit base costs, upgrade model costs, and upgrade equipment costs across all units. `src/spf/armies/io.py` has `print_army()` which prints each unit as a bullet line using `unit.config.name`. The points formula requested is `mp + cp + xp + 3 * ip`.

## Goals / Non-Goals

**Goals:**
- Add `unit_cost(unit, race_config)` to `data.py` that returns the `Cost` for a single unit.
- Refactor `total_cost` to delegate to `unit_cost` (avoids duplication).
- Add `unit_points(cost)` helper (or inline) that converts a `Cost` to an `int` via `mp + cp + xp + 3 * ip`.
- Update `print_army()` to append ` (N pts)` to each unit name line.

**Non-Goals:**
- No per-model point display.
- No point budget validation.
- No changes to total cost display format.

## Decisions

### D1: `unit_cost` as a standalone function in `data.py`
Keep the points logic in the same module as `total_cost`. The existing function is refactored to call `unit_cost` per unit, which keeps the two functions consistent and avoids duplicating the cost-accumulation logic.

Alternative considered: inline the per-unit cost in `print_army` directly — rejected because business logic belongs in `data.py`, not the display layer.

### D2: `unit_points` as a small helper in `data.py`
A one-liner `def unit_points(cost: t.Cost) -> int: return cost.mp + cost.cp + cost.xp + 3 * cost.ip` encodes the formula in one place. `print_army` calls `unit_cost` then `unit_points`.

Alternative: put the formula in `io.py` — rejected for the same separation-of-concerns reason as D1.

### D3: Display format `(N pts)`
Keep it minimal and consistent with the existing equipment parentheses style already used for model lines. No extra padding or alignment needed.

## Risks / Trade-offs

- [Risk] `unit_cost` logic must stay in sync with `total_cost` refactor → Mitigation: `total_cost` delegates to `unit_cost`, so there is one source of truth.
- [Risk] `Cost` fields could be `None` or missing → Mitigation: `Cost` is a dataclass with defaults; `_add_cost` already handles `None` second argument; no new risk introduced.
