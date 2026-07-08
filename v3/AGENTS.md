# Agent Guidance

**SteamPunkFantasy (spf)** is a tabletop hex-based wargame army management tool.
It reads information about races from TOML files in `races/` and
validates/displays them.

## Detailed guides

- **[`docs/agents/workflow.md`](docs/agents/workflow.md)** — implementation
  workflow: scratch-folder plans, TDD in a separate worktree, commit-per-cycle,
  and PR handling.
- **[`docs/agents/cli.md`](docs/agents/cli.md)** — using the `spf` CLI to inspect
  units, models, and equipment (and the legacy-TOML caveat).
- **[`docs/agents/quality-gates.md`](docs/agents/quality-gates.md)** — the `just`
  recipes for formatting, linting, type-checking, spell-checking, and tests. Run
  `just check` before committing.

## Agent skills

### Issue tracker

Issues are tracked as GitHub issues on `hssmalo/steampunkfantasy` via the `gh`
CLI; external PRs are not a triage surface. See `docs/agents/issue-tracker.md`.

### Triage labels

The five canonical triage roles map 1:1 to same-named labels. See
`docs/agents/triage-labels.md`.

### Domain docs

Single-context repo (`CONTEXT.md` + `docs/adr/` at the root, created lazily). See
`docs/agents/domain.md`.
