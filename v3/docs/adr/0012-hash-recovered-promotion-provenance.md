# Promotion provenance is recovered by digest, not recorded

A Survey (ADR 0011) can say a Target has an Asset and three Candidates waiting.
The question it cannot answer from filenames alone is the one that stops a
curator re-picking what they already picked: *which* of those Candidates is the
Asset?

```console
$ spf assets list goblin --candidates
  - goblin_infantry          Goblin Infantry          ✓        7 candidates
      1  2  2.1  3  4  4.1←promoted  4.3
```

## Compare digests at display time

**Decision: derive provenance by hashing, rather than recording it at promote
time.**

`CONTEXT.md` states plainly that Lineage reads off the filename and *no
provenance is recorded anywhere else* (ADR 0010). `promote` is a
`shutil.copyfile`, so the Asset is byte-identical to the Candidate it came
from — the fact is already on disk, just not written down. Deriving it keeps
that documented statement true, invents no sidecar or manifest format, and
leaves the promote path untouched.

Rejected: a provenance sidecar written at promote time (survives candidate
cleanup, but contradicts a documented decision and expands the one path that
must stay a copy); reporting nothing (simplest, but leaves the single most
actionable signal on the floor).

## All matches are reported, never one guessed

**Decision: when several Candidates are byte-identical to the Asset, show every
one.**

Seeds are deterministic, so a re-run with the same seed produces identical
bytes under a different Lineage. Picking one to display would be a coin flip
presented as a fact. Showing both is honest about what the digest can and
cannot establish.

## Consequences

- **Provenance degrades to a plain `✓` once Candidates are cleaned.** It is a
  convenience, never an authority — nothing else may depend on it.
- **Cost is hashing the Candidate store**, so it runs only under
  `--candidates`. The default listing never hashes a file.
- Because `candidates/` is gitignored, this output is machine-dependent by
  design.
