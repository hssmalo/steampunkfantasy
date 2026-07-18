# Asset listing reports coverage, driven by a Kind-declared Target set

ADR 0008 settled curation as a generate → refine → promote loop. What it left
open is how a curator finds the next thing to work on. With 8 races, 101
**Targets** and 19 committed Assets, "what's left?" is not answerable by
looking at the filesystem — the missing things are, by definition, not there.

```console
$ spf assets list goblin
Goblin
  Image
  - goblin                   Goblin                   ✗
  - goblin_infantry          Goblin Infantry          ✓
  - giant_snake_cavalry      Giant Snake Cavalry      ✗
  …
  Unknown
  - gigant_snake_cavalry.png
```

## Coverage, not inventory

**Decision: the Race TOML drives the rows; the filesystem annotates them.**

A directory listing answers "what files do I have?", which `ls` already does.
The curator's question is the complement — which Targets have nothing yet — and
that is only answerable from the source of truth for what *should* exist. So
`spf assets list` walks the Targets a Kind declares for a Race and checks each
against the two stores, rather than walking the stores and reporting what it
finds.

This inverts `race things`: the **key** is the primary column and the human
name is dimmed beside it, because a coverage row exists to be copied into the
next `spf assets image` or `promote` command.

Rejected: a filesystem inventory (cannot answer "what's missing", and a Target
renamed in TOML looks like a covered Target rather than a problem); a summary
count per race (the owner explicitly chose full detail — ~120 lines, ~82%
uncovered — because the detail *is* the worklist).

## The Target set is declared per Kind

**Decision: a `Kind.targets` field, `frozenset[TargetLevel]`, alongside
`subdir` and `extension`.** Image declares `{"race", "unit"}`; Lore will
declare `{"race"}` and Model `{"unit", "model"}` when they register.

The `Kind` record already holds the layout knowledge that varies per kind, and
which levels a kind depicts is exactly that sort of fact. Declaring it there
means the listing code, and the `--all` / `--missing` selectors built on the
same seam, never change when a Kind lands.

The field is **required, with no default**. A registry field that silently
defaults is one a future Kind author forgets to set, and the failure mode is a
Kind that reports coverage of the wrong things.

Rejected: hardcoding the race/unit fork in the listing command (would need
rewriting the moment `model` registers, and inverts the registry's purpose).

## Two seams, split on whether they touch disk

**Decision: `targets()` is pure TOML; `survey()` touches the filesystem.**

`spf assets image --all` needs the Target set but has no business scanning the
Asset store to get it. Splitting the two keeps that path free of disk access
and makes the pure half trivially testable.

## Consequences

- **A Target renamed in TOML strands its files as Orphans.** The `Unknown`
  section exists so this is visible rather than silent — it is how the real
  `gigant_snake_cavalry.png` typo surfaced.
- **Coverage of a Race whose TOML fails to validate is not reported at all**,
  per ADR 0004: `list_races(validate=True)`, silent omission. Silence is right
  for the sweep, but *naming* such a Race is a request that cannot be answered,
  so the explicit path reports it on stderr and exits 1 rather than raising a
  `ValidationError` traceback.
- `list` **exits 0 whenever it reports coverage.** A missing Asset is a normal
  state, not a failure; only an unanswerable request exits non-zero.
- **Out of scope:** fuzzy "did you mean" suggestions on Orphans; status filters
  (`--missing` / `--promoted`) on `list`.
