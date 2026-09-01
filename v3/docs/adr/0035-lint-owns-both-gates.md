# `spf lint` owns both gates

`spf lint <corpus>` loads its own corpus. A file that will not load is a
**Load finding** printed by the same command that would have linted its style,
and a file that yields a Load finding yields no other kind. There is no `spf
validate` command and no `just validate` recipe; `just check` runs one
data recipe, `lint-data`, which is `spf lint all`.

## What was wrong with keeping them apart

`races.list_races(validate=True)` **silently swallowed** the `ValidationError`
and dropped the Race from the list. So a broken `races/ork.toml` made `spf race
lint` print nothing and exit **0**. The failure was caught only because a
separate recipe ran `spf race show ork` a few lines earlier in the same `just
check`.

The two halves were load-bearing on each other without saying so. The swallowed
exception was a bug waiting for the day someone deleted the `validate` recipe —
and the recipe was a hand-maintained list of nineteen commands, one per Race and
per registry, that no new Race was added to automatically.

## Why merging preserves the no-double-report principle

ADR 0016 said a broken Race must be reported **once, at its cause**, and put the
style linter downstream of a separate hard gate so the two could not both speak.
That principle survives here unchanged; only its enforcement moves. Where ADR
0016 said "another command owns that failure", this says "this same command
already reported it" — which is a stronger guarantee, because it no longer
depends on recipe ordering.

The cascade is the same rule applied one level out: a broken Race suppresses
every Army of that Race, because the Army's failure *is* the Race's failure seen
from downstream. `spf lint armies` runs the cheap per-Race load probe to know
which; inside `spf lint all` the probe result is shared, so the Races load once
(ADR 0034 — registry loading is about a second per process, and the old recipe
paid it nineteen times).

## Why the corpus-loading command is not separate

Issue #172 asked for a *specific* command that loads and validates everything in
one process, alongside the moved lint subcommands. That command would have been
a hard gate wearing a soft gate's name, and it would have recreated the coupling
above: two commands, neither correct alone, whose contract lives in the order of
a `justfile`.

One command per corpus, owning both gates, is what makes the single-process win
the issue asked for real without splitting responsibility for one file across
two commands.

## Why `pack.toml` and `site.toml` sit under `render`

They live under `armies/`, but they are not Army data — they are the authored
indexes that say what the site publishes and in what order (ADR 0028). `spf lint
armies` is about `armies/**/*.json`: a player's Army against its Race's
catalogue. Grouping by *what a file is an input to* rather than by which
directory it happens to sit in keeps each command's corpus describable in one
sentence.

## Why Build findings are a third kind

An Army that loads fine but replaces a Model its Race does not list is neither a
Load finding nor a Style finding. The file read perfectly, so calling it `load`
would be a lie; and it is illegal rather than untidy, so calling it style would
put a real defect in the tier reserved for tidiness.

`build` is its own rule column, and it is *referential legality against the
catalogue only*: `replaces` legality, an Upgrade Equipment having a Cost,
`requires` groups satisfiable. **There is no budget or points check here, and
none should be added** — an Army's Points are the designer's business, not the
loader's.

## Consequences

- `spf race lint`, `spf rules lint` and `spf render lint` are gone, with no
  aliases. `spf render lint --tlmgr` becomes `spf render tlmgr`, which never
  was a lint: it prints what the manifest declares rather than checking it.
- None of the five subcommands takes an argument. `spf lint races 2>&1 | grep
  ork` covers the authoring loop the old optional Race name served, and
  whole-corpus-in-one-process is the point.
- Findings are collected across every corpus and printed before a single
  `SystemExit(1)`. Collect-all, never fail-fast: a broken Race must not hide a
  broken Army.
- `CONTEXT.md`'s **Hard gate** and **Soft gate** entries are replaced by **Load
  finding**, **Build finding** and **Style finding**. `load` and `build` are
  literally the words the terminal prints, so the glossary and the output share
  one vocabulary.
- Army `.py` build scripts are **not** linted. Executing arbitrary Python is a
  different risk and a different failure mode from "does this data load"; the
  `.json` they produce is committed, and that is covered.
