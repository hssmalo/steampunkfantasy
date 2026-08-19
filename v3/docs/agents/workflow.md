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

## Comments in source code

Comments are read long after the work that produced them is forgotten. Write
them for that reader.

- **Never refer to transient context**: no implementation plans, issue or PR
  numbers, branch names, "for now", "as discussed", "new behavior", or
  before/after comparisons with the code that was just replaced. Anything that
  stops being true the minute the issue is merged doesn't belong in the source
  — that context goes in the commit message, the PR description, or the issue.
- **Do refer to durable context**: ADRs in `docs/adr/` (by number) and the
  vocabulary defined in `CONTEXT.md`. Use the glossary's terms rather than
  synonyms.
- **Keep comments short and focused** — a line or two explaining *why*, right
  next to the code it explains. No multi-paragraph comments: if an explanation
  needs paragraphs, it's a design decision and belongs in an ADR, which the
  comment can then point at.
- Don't restate what the code already says.

## Wrapping up

- When the implementation is done, push the commits to a **new PR**. Open it
  **ready for review, not as a draft** — `gh pr create` (no `--draft`). A plan
  or issue that says to open a draft is overridden by this default unless the
  human asks for a draft explicitly.
- **Don't clean anything up** (worktree, branch, scratch files) until told to —
  the PR is reviewed before merging.
- The human squash-merges the PR at the end.
