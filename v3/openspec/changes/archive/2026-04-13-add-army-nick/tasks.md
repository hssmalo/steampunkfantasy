## 1. Data Model

- [x] 1.1 Add required `nick: str` field (no default) to the `Army` dataclass in `src/spf/armies/data.py`

## 2. Serialization

- [x] 2.1 Update `save_army` in `src/spf/armies/io.py` to include `nick` in the JSON output
- [x] 2.2 Update `load_army` in `src/spf/armies/io.py` to read `nick` via `data["nick"]` (no fallback)

## 3. Display

- [x] 3.1 Update `print_army` in `src/spf/armies/io.py` to render the rule header as `"<nick> — <Race> Army"`

## 4. Call Sites

- [x] 4.1 Update all `Army(...)` construction sites (tests, fixtures, etc.) to pass `nick`

## 5. Demo Army

- [x] 5.1 Add a `"nick"` field to `armies/demo.json`

## 6. Quality Checks

- [x] 6.1 Run tests: `uv run pytest`
- [x] 6.2 Run linter: `uv run ruff check src/`
- [x] 6.3 Run formatter: `uv run ruff format src/`
- [x] 6.4 Run type checker: `uv run pyright`
- [x] 6.5 Run spell checker: `uv run typos`
