# Candidate indices append, and are never reused

Generating Candidates numbered them per run, always starting at `.1`. A second
run over the same Target therefore wrote over the first run's files:

```console
$ spf assets image goblin goblin_infantry --count 3
Wrote candidates/goblin/images/goblin_infantry.1.png (18.4s)
Wrote candidates/goblin/images/goblin_infantry.2.png (17.9s)
Wrote candidates/goblin/images/goblin_infantry.3.png (18.1s)
$ spf assets image goblin goblin_infantry --count 3   # the three above are gone
Wrote candidates/goblin/images/goblin_infantry.1.png (18.2s)
```

## Indices append past the highest existing Lineage

**Decision: a new Candidate takes one past the highest index already present
under its name, rather than restarting the count each run.**

This is worth an ADR rather than a silent fix because the old behavior was
*documented* — `generate` promised that "existing candidate files are
overwritten silently" — and because the fix changes what a Lineage means. The
loss it caused is unrecoverable and invisible: `candidates/` is gitignored, so
a Candidate a curator was still weighing is simply gone, with nothing on screen
saying so. Curation is the expensive human step in this pipeline; destroying
its inputs as a side effect of asking for more options is the wrong default.

## The maximum runs over the whole subtree

**Decision: the highest index is taken over the first component of *every*
Lineage under the name, not only over Candidates that still exist.**

A surviving `ork.4.1.png` reserves `4` even when `ork.4.png` itself was
deleted. Without this, a new Candidate landing on `4` silently **adopts** the
orphaned `ork.4.1` as its own Refinement: Lineage reads straight off the
filename and nothing else records provenance (ADR 0010), so
`promote --pick 4.1` would hand back an image derived from a parent that no
longer exists, with no signal that anything is wrong.

This is exactly the sort of rule a later contributor simplifies back out —
scanning only for `ork.*.png` and ignoring deeper Lineages looks equivalent and
is cheaper. It is not equivalent. The adoption hazard is the entire reason the
scan goes deep.

Rejected: gap-filling, reusing the lowest free index. It keeps numbers small
and tidy, but resurrecting a deleted `ork.4` is precisely the adoption case
above.

## Consequences

- **Numbers drift upward and are not a count.** A heavily curated Target
  reaches `ork.23` with three Candidates on disk. A Lineage is a coordinate;
  `spf assets list --candidates` is what says which actually exist.
- **Deleting Candidates never reclaims coordinates.** Cleaning up is safe —
  it can only ever free disk, never renumber what is left.
- **Concurrent generate runs would collide.** Two simultaneous
  `spf assets image` invocations compute the same maximum and write the same
  indices. `spf` is a single-user CLI and locking is not worth its cost, so
  this is accepted rather than solved.
