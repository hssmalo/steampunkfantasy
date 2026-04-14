## Context

`Cost` is a Pydantic `StrictModel` in `src/spf/schemas/type_aliases.py` with four `int` fields: `mp`, `cp`, `xp`, `ip`. Cost arithmetic is currently scattered:

- `_add_cost(a, b)` in `armies/data.py` adds two `Cost` objects field-by-field and handles `None`
- Scaling by model count is done inline with four manual multiplications
- The points formula `mp + cp + xp + 3 * ip` is computed inline in `unit_points`

Adding dunder methods to `Cost` centralises all arithmetic in the model itself.

## Goals / Non-Goals

**Goals:**
- `Cost + Cost` via `__add__` / `__radd__` (enabling `sum([c1, c2, ...], start=Cost())`)
- `Cost * int` and `int * Cost` via `__mul__` / `__rmul__`
- `cost.to_points()` encapsulating the canonical formula
- Remove `_add_cost` from `data.py` and simplify all call sites

**Non-Goals:**
- Subtraction, division, or comparison operators — not needed today
- `Cost * Cost` — no meaningful use case
- Changes to serialisation, TOML format, or CLI output

## Decisions

### Decision: Implement on the Pydantic model directly

**Chosen:** Add `__add__`, `__radd__`, `__mul__`, `__rmul__`, and `to_points()` as methods on the `Cost` class itself.

**Alternative considered:** A standalone module of free functions (e.g. `cost_add(a, b)`). Rejected because it doesn't reduce call-site complexity — callers still need to import and call a separate function. Dunder methods make `Cost` a first-class numeric type and enable Pythonic idioms like `sum()`.

### Decision: `__add__` returns `Cost`, not `Cost | None`

The existing `_add_cost` handles a `None` second argument (treating it as zero). The new `__add__` will only accept `Cost` operands; `None` handling moves to the call sites (which already have `if equip.cost is not None` guards). This keeps the operator semantically clean.

### Decision: `to_points()` owns the formula

`mp + cp + xp + 3 * ip` is a domain rule that belongs on `Cost`, not scattered across call sites. Centralising it means the formula can be changed in one place.

## Risks / Trade-offs

- **Pydantic model mutation** → `Cost` is immutable (`StrictModel`); all operators return new instances. No mutation risk.
- **`sum()` start value** → Python's `sum()` defaults `start=0`, so callers must pass `sum(costs, start=Cost())` or `sum(costs, Cost())`. This is slightly verbose but explicit and safe. The `__radd__` override handles `0 + Cost` so that `sum()` works without the explicit start on Python ≥ 3.8 (where `0 + Cost` calls `Cost.__radd__`).

## Migration Plan

1. Add methods to `Cost` in `type_aliases.py`
2. Replace `_add_cost(a, b)` call sites with `a + b` (or `a + b` with `None` guard removed where applicable)
3. Replace inline multiplications with `cost * num_models`
4. Update `unit_points` to call `cost.to_points()`
5. Delete `_add_cost`
6. Run tests — no behaviour change expected
