# Changing game data

Read this before editing anything that changes what the documents print. The
vocabulary is in [`CONTEXT.md`](../../CONTEXT.md) — **Golden**, **Changelog** —
and the reasoning is in
[ADR-0033](../adr/0033-tests-exercise-spf-not-the-game-rules.md).

## When this applies

> **A change is output-affecting and untested when nothing in `just check` will
> notice if it comes out wrong.**

That covers every edit under `races/`, `armies/` and `rules/` — the linters
prove such a file *loads*, never that it *reads* correctly — and it covers
`templates/` most acutely of all, since production templates are deliberately
exempt from assertions and `just render-site` is the only thing that exercises
them.

The property is what matters, not the directory. A change to `spf` that alters
rendered output is in scope too.

## The loop

Take a **Golden** before touching anything, then work one change at a time:

```console
just golden-snapshot          # Before you edit: the before-image
# ... make one change ...
just golden-diff              # What did that print?
just check && just lint-data  # The gates that do apply
git commit
just golden-accept            # Re-baseline, so the next diff shows only the next change
```

`just golden-accept` is the step people skip, and skipping it is what makes the
fourth change's diff arrive with the first three still in it. It is
mechanically `golden-snapshot`; the name is there so it reads right after a
review rather than as "start over".

A `diff` warns when the snapshot's baseline has drifted — a different commit, or
a tree that was dirty when the snapshot was taken. It is a warning, not a
refusal: committing a reviewed change moves HEAD on purpose.

### One change per commit

A commit collapsing forty rules judgments produces a diff nobody can review,
and the review is the entire point. Keep a commit to one judgment with its own
diff.

This is a default, not a rule. Eight instances of the same typo are one
judgment, not eight.

## Reading the diff

The diff answers a question the TOML cannot: **did this edit change what the
rules say?**

Re-spelling prose and changing a rule look identical in a source file, and
obviously different in the rendered line. Consolidating drifted prose onto a
shared variant is the case where this bites — a merge that looks
meaning-preserving can quietly drop a clause, a label, or a whole scoping
condition, and the rendered diff is where that becomes visible. Read every
changed line and ask whether the rule survived.

When the answer is that the rule *did* change:

- If it was intentional, it wants a **Changelog** line — `races/changelog.md` or
  `rules/changelog.md`, recording the reasoning rather than the mechanical edit.
- If it was not, that is the bug, and you found it in the only place it was
  ever going to show up.

A meaning-preserving re-spelling gets no Changelog line. That file is worth
reading precisely because it is short.

### Two expectations, one mechanism

The recipes do not care which kind of change you are making, but you should:

- A **refactor** — collapsing identical strings, moving code — expects the diff
  to be **empty**. Anything in it is a defect.
- A **data edit** expects the diff to hold **exactly** the prose meant to move.
  Anything else in it is a defect.

Say which one you are doing before you look, or the diff will agree with you
either way.

## Showing your work

Post the diff to the issue, with prose saying what you decided and why. In #165
this was the whole value: the diff shows *what* moved, and only you can say
whether the wording that won was the right one.

`golden-diff` prints in a shape that pastes straight into a comment — a counts
line and a fenced diff, Markdown only, truncated mechanically. Do not hand-edit
it. Add the judgment around it:

> **C11 — golden diff.** MERGE, pointed at `sniper.choose_model_after_aim`.
> Worth a second look: the site said "with an elven seeker arrow", the variant
> says "with the use of aim" — the site named the weapon, the variant names the
> mechanism.

Nothing posts this for you. A script could paste the diff and would only
automate the half that was never the hard part.

## The recipes

```console
just golden-snapshot            # Render the corpus into the gitignored goldens/
just golden-diff                # Re-render and report what moved
just golden-diff --format all   # ... including LaTeX; `latex` for LaTeX alone
just golden-accept              # Retake the snapshot over a reviewed change
```

Both text Formats are always rendered and always compared, so the verdict is
honest whatever you asked to see. Markdown is printed by default because both
Formats render the same view model — for a prose edit the LaTeX diff is the same
change in a noisier notation, so it is counted rather than shown. Reach for
`--format` when editing `templates/`, where the two genuinely differ.

Diffs carry no context lines, and are capped at 25 lines per file and 100 across
a run. A document that vanished or appeared is always reported, whatever its
Format.

## What this is not

None of it is wired into `just check`, and none of it should be. For a data edit
the diff is *expected* to be non-empty, so a gate would fail on every correct
change — and Lint has exactly one severity, `lint speaks ⇒ the build fails`,
which a golden diff cannot honor. It sits outside the gate deliberately, like
`just test-friction`.

`goldens/` is never committed. That rule, and why, is in
[`testing.md`](testing.md).
