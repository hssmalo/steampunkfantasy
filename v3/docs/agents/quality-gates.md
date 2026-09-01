# Quality Gates

The project uses uv and Python 3.13+. Quality gates (Pytest, Ruff, Pyright, and
Typos) are run through [`just`](https://github.com/casey/just). Prefer the `just`
recipes over the underlying commands:

```console
just            # Run all quality gates (same as `just check`)
just check      # fmt-check, lint, spell, lint-data, test, typecheck — stops on first failure

just fmt        # Auto-format with ruff
just fmt-check  # Check formatting without writing changes
just lint       # Lint with ruff
just typecheck  # Type-check src/ and tests/ with pyright
just spell      # Spell-check with typos
just spell-fix  # Fix spelling errors with typos
just test       # Run the test suite quietly (accepts extra pytest args, e.g. `just test -k foo`)
just fix        # Auto-fix lint issues, then reformat
just lint-data  # Lint every corpus: load failures, illegal Army builds, style findings (spf lint all)

just test-friction  # Mutate lint-clean TOML values; report the tests that break

just golden-snapshot  # Render every document into the gitignored goldens/
just golden-diff      # Re-render and diff against that snapshot
```

`just test-friction` and the two golden recipes are on-demand and deliberately
outside `just check` — see [`testing.md`](testing.md).

## Tests depend only on tracked files

A test may read the real filesystem only for files **git tracks** — `races/`,
`rules/`, `configs/spf.toml`, `workflows/cloud/`, `workflows/examples/`. Those
are byte-identical on every machine, so they carry real signal.

Anything gitignored or per-machine — `workflows/local/`, `.envrc`, a local
ComfyUI install — must never be a precondition. A test that depends on one
passes or fails on how the machine happens to be set up: green for whoever
wrote it, red in a fresh clone or worktree, and green again for anyone whose
shell exports a different default. Point such a test at `tmp_path` instead
(see `_install_workflows` in `tests/assets/test_image.py`).

Whether the committed config and the committed data actually agree is a
separate question, and it belongs in `just lint-data` — where `spf lint assets`
checks it — not in the test suite.

## Releases

`spf` is calendar-versioned (`YYYY.MM.PATCH`), with `pyproject.toml`'s
`[project].version` as the single source of truth — rendered documents and
`spf --version` read it from the installed package metadata.

```console
just release    # Bump the CalVer version with bumpver, re-lock, commit, tag, and push
```

`just release` is run **locally by a human**, never from CI: it commits, tags,
and pushes in one step. The release config lives in `bumpver.toml` at the
*repository root* rather than in `v3/pyproject.toml`, and the recipe runs from
there — bumpver looks for `.git` in its working directory and merely warns,
then skips committing, when it does not find one.

Pass `--dry` through (`just release --dry`) to preview the version transition.
Be aware that `--dry` only prints the file diffs: it exercises neither the
commit/tag/push nor the `uv lock` pre-commit hook.

**Run `just check` before committing.** The underlying tools (`uv run pytest`,
`uv run ruff`, `uv run pyright`, `uv run typos`) can still be invoked directly
when needed.
