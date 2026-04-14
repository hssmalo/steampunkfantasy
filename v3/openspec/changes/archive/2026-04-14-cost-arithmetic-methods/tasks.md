## 1. Extend Cost with arithmetic methods

- [x] 1.1 Add `__add__(self, other: Cost) -> Cost` to `Cost` in `src/spf/schemas/type_aliases.py`
- [x] 1.2 Add `__radd__(self, other: int | Cost) -> Cost` to support `sum(costs, Cost())`
- [x] 1.3 Add `__mul__(self, n: int) -> Cost` to `Cost`
- [x] 1.4 Add `__rmul__(self, n: int) -> Cost` to `Cost`
- [x] 1.5 Add `to_points(self) -> int` to `Cost` implementing `mp + cp + xp + 3 * ip`

## 2. Simplify cost arithmetic in armies/data.py

- [x] 2.1 Replace every `_add_cost(a, b)` call site with `a + b` (handling `None` with the existing `if equip.cost is not None` guards)
- [x] 2.2 Replace the inline four-field multiplication in `unit_cost` with `equip.cost * num_models`
- [x] 2.3 Update `unit_points` to call `unit_cost(...).to_points()` instead of the manual formula
- [x] 2.4 Delete the `_add_cost` helper function

## 3. Tests

- [x] 3.1 Write unit tests for `Cost.__add__` (including identity, commutativity with `__radd__`, and `sum()` usage)
- [x] 3.2 Write unit tests for `Cost.__mul__` and `__rmul__` (including multiply-by-zero)
- [x] 3.3 Write unit tests for `Cost.to_points()` (including zero cost)
- [x] 3.4 Verify existing `unit_cost` and `unit_points` tests still pass without modification

## 4. Quality checks

- [x] 4.1 Run `uv run pytest` — all tests pass
- [x] 4.2 Run `uv run ruff check src/` and `uv run ruff format src/` — no issues
- [x] 4.3 Run `uv run pyright` — no type errors
- [x] 4.4 Run `uv run typos` — no spelling errors
