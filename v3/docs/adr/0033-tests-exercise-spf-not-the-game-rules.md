# Tests exercise `spf`, not the game rules

The suite is 1306 tests and runs in 38 seconds. Speed was never the problem.

The problem is what the tests are *about*. Rebalancing a Unit's cost, renaming a
Model, rewording a Special's prose, adding an Equipment — the ordinary work of
writing a wargame — turned tests red. Not because anything broke, but because a
test had written the old value down. The suite had quietly become a second copy
of the game data, and the second copy has to be edited every time the first one
is. A test suite that taxes the activity the project exists to support is
working against it.

## Decision

**Tests exercise `spf`'s behavior. The linters own the data.**

> No test may fail because a TOML file under `races/`, `armies/`, or `rules/`
> was updated.

Deleting or renaming a file may break a test — that is a structural change, and
noticing one is signal. Updating a *value* may not.

The corollary turned out to be the larger cull:

> Tests may verify that the templating mechanism works, but must never assert on
> the content of a production template.

No `\usepackage` checks, no table-of-contents assertions, no heading structure,
no column specs, no header or footer markers. Templates are presentation and are
meant to be edited freely. Rendering behavior is tested through the toy
templates in `tests/fixtures/templates/`, or one tier down on the view model.

`docs/agents/testing.md` is the operational form of this decision.

## Why the linters are trusted with the data

Because the rule hands the data to them, they have to be worth handing it to,
and they already are. `just check` runs `spf race lint`, `spf rules lint` and
`spf render lint`, then loads and renders the whole committed corpus through
`spf race show` and `spf rules ...` for every Race and every registry. An
invalid edit does not reach a test; it is caught before the suite starts.

So a test pinning a value that a linter already validates is not a second
opinion — it is the same check, restated in a place that costs an edit to
maintain. That is friction with no signal behind it.

Where a linter genuinely cannot catch something, the answer is a new lint rule,
not a test. Rules live in one place then, and they run over the whole corpus
instead of over the one Race a test happened to name.

## The trade-off we accept

Less regression coverage over the real data. A change to `spf` that renders the
real Races wrongly while rendering synthetic ones correctly will not be caught
by the suite.

We take it for two reasons. The corpus is still exercised on every run of `just
validate` and `just render-site`, which load and render every Product in every
Format. And coverage that fires on every legitimate rules edit is not coverage —
it is noise, and noise is answered by editing the expected value until the test
goes green, which is precisely the failure mode where a real regression walks
through.

## The goldens did their job, then outstayed it

[ADR-0032](0032-a-variant-is-shared-instance-prose.md) credits the golden files
with making a 189-site migration reviewable in one commit whose output was
"byte-for-byte unchanged". That is the *correct* use of a golden, and it is the
argument for keeping the mechanism.

What went wrong is that the goldens that migration produced were never deleted.
A golden proves that a specific change altered no output; kept past that change,
it becomes a fixture pinning every byte of a document, and it goes red whenever
the game rules or a template legitimately move. The 18 committed goldens had no
regeneration mechanism at all — every one was hand-maintained.

So goldens are now **generated on demand** into a gitignored `goldens/`, by
`just golden-snapshot` and `just golden-diff`, and deleted when the refactor
that needed them lands. Same tool, with the lifetime it should always have had.

## Consequences

- Roughly 120 tests are removed or converted to synthetic data.
- 18 golden files and 7602 lines of expected output are deleted.
- LaTeX compilation is no longer verified by `just check`. It is still exercised
  by `just render-site`, which builds every Product to PDF.
- `tests/conftest.py` gains shared synthetic builders, so "make this test
  synthetic" is not an invitation to hand-roll a seventh minimal `RaceConfig`.
- `just test-friction` mechanically enforces the rule: it mutates lint-clean
  TOML values and reports every test that a legitimate edit would break. It is
  on-demand rather than part of `just check`, because the property only changes
  when someone writes a test.
