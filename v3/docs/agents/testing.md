# Testing

What the test suite is for, and what belongs somewhere else. Read this before
adding a test. The reasoning behind it is in
[ADR-0033](../adr/0033-tests-exercise-spf-not-the-game-rules.md).

## The rule

> **No test may fail because a TOML file under `races/`, `armies/`, or `rules/`
> was updated.**

The tests exercise `spf`. The linters own the data. Writing game rules is the
activity this project exists to support, and a suite that goes red when someone
rebalances a Unit is taxing it.

Corollaries:

- A test failing because a TOML file was **deleted or renamed** is fine. Those
  are structural changes, and a test noticing one is doing its job.
- An **invalid** TOML edit must be caught by a linter, never by a test. If you
  find an invalid edit that only a test catches, the fix is a new lint rule in
  `spf race lint` / `spf rules lint` — not a test that pins the valid value.
- Reading real data is not itself forbidden. Deriving an expected value from
  real data at runtime is fine: `tests/frontends/cli/test_race.py` compares CLI
  output against a live `races.get_race("goblin")` call, and stays green through
  any goblin edit. **Hardcoding** a value that came out of a TOML file is not.

## Never assert on the content of a production template

Tests may verify that the **templating mechanism** works: that a file was
written, to the right path, with the right Product and Format selected, and that
bad input raises.

Tests must **never** assert on what a template under `templates/latex/**` or
`templates/markdown/**` produces. No `\usepackage{...}` checks, no
table-of-contents assertions, no section or heading structure, no table
environments, no column specs, no header or footer markers. A template is
presentation; it is meant to be edited freely, and a test that pins its output
makes every layout tweak a test-fixing exercise.

To test rendering behavior, render through the toy templates in
`tests/fixtures/templates/latex/_test/` and
`tests/fixtures/templates/markdown/_test/`. They hold no game content and no
formatting worth pinning, so editing a production template cannot break them.
`tests/render/test_render.py` is the worked example.

When the behavior you want is one tier down — what the renderer *decided*, not
how it was typeset — assert on the view model instead of on rendered text.

The consequence is deliberate and worth stating plainly: **`just render-site`
is the only thing that exercises the real templates.** Nothing in `just check`
will notice a template that stopped compiling or started laying a page out
wrongly. Run `just render-site` and look at the output before a release, and
after any edit under `templates/`.

## No committed expected-output files

There are no golden files in the repository, and none should be added.

A golden is a refactoring tool, not a fixture. It is worth exactly one thing:
proving a change altered no output. So it is generated on demand for the
duration of a refactor and deleted afterwards.

```console
just golden-snapshot   # Render every product into the gitignored goldens/
just golden-diff       # Re-render and diff against that snapshot
```

**Snapshotting is step one of any output-affecting refactor.** Take the snapshot
before touching anything, `just golden-diff` as you go, and delete `goldens/`
when the work lands. `goldens/` is gitignored; nothing in it is ever committed.

Both recipes drive `spf render` over the whole committed corpus — every Race
Overview, Army Reference, Order Card deck and Army Pack, plus the Rulebook —
in Markdown and LaTeX. The binary Formats derive from those two, and a PDF
stamps a build time that would differ on every run. `golden-diff` prints a
unified diff per file that moved and exits non-zero if any did.

The distinction is easy to over-read, so state it plainly:

- **Banned:** committed *expected output* — a file a test byte-compares against.
- **Fine:** committed *input fixtures* — the toy templates above, hand-built
  JSON or TOML a test feeds in.

An input fixture must not depend on real data. A fixture army referencing real
dwarf keys and loading with `validate=True` looks synthetic and is not: a rename
in `races/dwarf.toml` breaks it. Build such fixtures from the synthetic builders
below.

## Real-data smoke checks live in `just validate`

"Does the committed corpus still load and render" is a `just validate` question.
Do not add pytest tests that sweep every Race or every Army. They pin nothing,
they grow linearly with the game, and they re-run on every inner loop.

The recipe is file-driven: it loads every `races/*.toml` and every
`armies/**/*.json` on disk, so a new Race or Army is covered the moment it is
committed, with no list to keep in step.

## Prefer synthetic fixtures

`tests/conftest.py` provides shared builders for synthetic Races, Registries and
Armies. Use them rather than hand-rolling another minimal `RaceConfig`, and
rather than reaching for `races.get_race(...)`. Name what you build with the
`CONTEXT.md` vocabulary — Race, Unit, Model, Equipment, Holder, Special
Instance.

What they are:

| Builder | Gives you |
|---|---|
| `synthetic_race(units=…, models=…, equipment=…, spawns=…)` | A `RaceConfig`: by default a costed and an uncosted Unit of one Model, which declares a Holder and carries a Default Equipment, with an Upgrade Equipment on the shelf |
| `synthetic_unit()` / `synthetic_model(holders=…)` / `synthetic_equipment()` / `synthetic_assault()` | One record each, every unnamed field filled in |
| `synthetic_registry(specials=…, records=…)` | A `Registry` over ids you invent |
| `synthetic_special(slots=…)` | One Special rule |
| `synthetic_army(race, units=…, nick=…)` | An unresolved `ArmyList` |
| `write_race_toml(directory, race)` | A Race on disk, for a test that needs one there |

Every builder takes the fields a Race file writes and validates them, so
`synthetic_unit(name="Mob", cost=None)` is the whole of an uncosted Unit.

Two fixtures wrap the common cases: `armies_dir` points `config.paths.armies`
at `tmp_path`, and `install_registry` puts a Registry behind the load-time gate.

### Inventing Special ids

A Race's Special ids are resolved against `rules/` when it loads (ADR 0024), so
a synthetic Race could otherwise only use ids the committed registry happens to
declare — which is what used to force a test wanting a Special on every Holder
to read a real Race. Install a Registry of your own instead:

```python
def test_something(install_registry: InstallRegistry) -> None:
    install_registry(synthetic_registry(specials={"countdown": None}))
    race = synthetic_race(units={"squad": synthetic_unit(specials={"countdown": [{"text": "Three rounds."}]})})
```

A `None` rule permits every Slot; pass `synthetic_special(slots=[...])` to
narrow one. The gate is not disabled — an id the installed Registry does not
declare is still rejected.

Existing exemplars worth reading:

- `tests/test_display.py` — the smallest use of the builders.
- `tests/armies/test_specials.py` — builds Instances, Equipment, Models and
  Units, and says in its docstring why it avoids real Race data.
- `tests/lint/test_collect.py`

## How to check you got it right

```console
just test-friction   # Mutate lint-clean TOML values; report tests that break
```

Run it when you add or change a test that touches real data. It edits one value
at a time in the committed corpus, skips anything the linters reject, runs the
suite, and reports every test that a legitimate rules edit would have broken.
Findings are bugs in the tests, not in the data.

Because every mutation costs a full pytest run, the default sweep samples one
value per allowlisted field name, spread across files. `--per-field N` widens
it, `--full` mutates everything, and `--list` prints the chosen values without
running anything.

It is deliberately **not** part of `just check`: it roughly doubles suite
runtime, and the property it guards only changes when someone writes a test.
