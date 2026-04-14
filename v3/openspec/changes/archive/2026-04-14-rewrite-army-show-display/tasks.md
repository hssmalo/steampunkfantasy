## 1. Rewrite print_army

- [x] 1.1 In `src/spf/armies/io.py`, replace the `print_army` function body with a f-string bullet list: bold army name, unit bullets, model sub-bullets with inline equipment in parentheses
- [x] 1.2 Use `Cost.__str__()` for the total cost line (replace manual `MP={cost.mp} CP=...` interpolation)
- [x] 1.3 Remove the `from rich.table import Table` import from `io.py`

## 2. Verify & Polish

- [x] 2.1 Run `uv run spf army show demo` and confirm output matches expected format (bold name, bullet list, equipment in parens, cost line)
- [x] 2.2 Run `uv run pytest` — confirm all tests pass
- [x] 2.3 Run `uv run ruff check src/` and `uv run ruff format src/` — fix any issues
- [x] 2.4 Run `uv run pyright` — confirm no type errors
- [x] 2.5 Run `uv run typos` — confirm no spelling issues
