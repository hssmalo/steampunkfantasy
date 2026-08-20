# Quality Gates

The project uses uv and Python 3.13+. Quality gates (Pytest, Ruff, Pyright, and
Typos) are run through [`just`](https://github.com/casey/just). Prefer the `just`
recipes over the underlying commands:

```console
just            # Run all quality gates (same as `just check`)
just check      # fmt-check, lint, validate, lint-races, spell, test, typecheck — stops on first failure

just fmt        # Auto-format with ruff
just fmt-check  # Check formatting without writing changes
just lint       # Lint with ruff
just typecheck  # Type-check src/ and tests/ with pyright
just spell      # Spell-check with typos
just spell-fix  # Fix spelling errors with typos
just test       # Run the test suite quietly (accepts extra pytest args, e.g. `just test -k foo`)
just fix        # Auto-fix lint issues, then reformat
just validate   # Validate all the TOML files via the spf CLI
just lint-races # Lint race data for name and key consistency (spf race lint)
```

## Releases

`spf` is calendar-versioned (`YYYY.MM.PATCH`), with `pyproject.toml`'s
`[project].version` as the single source of truth — rendered documents and
`spf --version` read it from the installed package metadata.

```console
just release    # Bump the CalVer version with bumpver, re-lock, commit, tag, and push
```

`just release` is run **locally by a human**, never from CI: it commits, tags,
and pushes in one step. Pass `--dry` through (`just release --dry`) to see the
version transition without touching anything.

**Run `just check` before committing.** The underlying tools (`uv run pytest`,
`uv run ruff`, `uv run pyright`, `uv run typos`) can still be invoked directly
when needed.
