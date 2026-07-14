# Implementation Workflow

For non-trivial features and fixes, follow this workflow:

## Planning

- Store implementation plans in the local `.scratch/` folder (gitignored).
- When a plan is done, archive it by moving it to `.scratch/done/`.

## Implementation

- Do the implementation with the **tdd** skill (red-green-refactor).
- Work in a **separate git worktree on a separate branch**, not the main
  checkout.
- Make a commit after each red-green cycle. Individual commit messages can be
  short and specific.

## Wrapping up

- When the implementation is done, push the commits to a **new PR**.
- **Don't clean anything up** (worktree, branch, scratch files) until told to —
  the PR is reviewed before merging.
- The human squash-merges the PR at the end.
