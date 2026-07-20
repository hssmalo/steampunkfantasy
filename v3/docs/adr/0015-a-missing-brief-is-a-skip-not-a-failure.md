# A missing Brief is a skip, not a failure

ADR 0014 made Brief-less Targets *visible* in `spf assets list` and left their
interaction with generation explicitly out of scope. That interaction was
broken: `_generate_image` exited 1 on the first Target with no Brief, so
`spf assets image dwarf --missing` — which selects every Target without an
Asset, and on dwarf that is all of them — printed one name and stopped. On a
partly-briefed race it generated up to the first gap and abandoned the rest of
the batch, GPU time already queued.

With 39 of 101 Targets unbriefed, the state that aborts the run is the
*ordinary* state of this repo, not an exceptional one.

## Warn and skip, uniformly

**Decision: a Target with no Brief is warned about on stderr and skipped. The
rule does not vary with the selector or with how many Targets were selected.**

The originating issue proposed a narrower rule — warn on multi-Target runs, but
keep the hard error when the user names a single Target, since "the user asked
for that specific one." Rejected. It makes the exit code depend on something
the user is not thinking about:

- Branching on the *count* (`len(selected) > 1`, which the progress heading
  already used) means `spf assets image dwarf --missing` hard-errors on the day
  one Target is left to fill and warns on the day two are. The contract would
  flip as a side effect of curating, which is the one thing that should not
  change it.
- Branching on the *selector* is stable, but still asks a reader to hold two
  behaviors and a rule for choosing between them. The distinction buys nothing:
  a curator who names an unbriefed Target learns the same fact from a warning
  as from an error, and nothing downstream depends on the difference.

One rule, one sentence in `--help`.

## Always exit 0

**Decision: skipping every selected Target is still a successful run.**

Reserve non-zero for a broken world — ComfyUI unreachable, a malformed Workflow
file, an unknown unit name. A gap in authored data is a worklist item
that `spf assets list` already reports; making it an exit code puts the repo's
normal condition permanently in the failure channel, where it drowns the
signal.

This does change the contract for callers: a script running
`spf assets image $race && …` will now proceed where it used to stop. That is
the intended correction — it used to stop on a *partial* batch too, which no
caller wanted.

## Service errors still abort the batch

**Decision: the `OSError`/`ComfyUIError` exit in `_generate_image` is left
exactly as it is.**

This looks asymmetric with the rule above, and deliberately is. A missing Brief
is a per-Target fact about *authored data*, knowable before anything is spent
and carrying no information about the next Target. A Service failure is
evidence about *the world*, and the likeliest explanation for one is the
condition that will fail the remaining nineteen — continuing would spend the
run producing a wall of identical errors.

If a genuinely transient mid-batch failure is ever observed, the answer is a
consecutive-failure threshold, not making this symmetric. Nobody has seen one
yet, so it is not built.

## `--missing` keeps meaning "no promoted Asset"

**Decision: the selector is unchanged. It is not narrowed to "no Asset *and*
has a Brief".**

Narrowing it would make `spf assets image dwarf --missing` quietly select
nothing instead of warning twenty times, which is tempting and wrong. One flag
would then answer two questions, and the curator could no longer distinguish
"nothing is missing" from "everything missing is blocked" — precisely the
distinction ADR 0014 built the ✗ marker to preserve. The warnings *are* the
blocked worklist, surfaced at the moment someone tried to act on it.

## Partition before generating

**Decision: `image()` splits the selection into briefed and Brief-less before
the generation loop, rather than skipping inline as it walks.**

Same argument ADR 0014 made for the listing marker: the shape of the batch
should be on screen before GPU time is spent on it. Skipping inline would
scatter the warnings through several minutes of generation output, so you would
learn what was skipped only once the run was over and the decision to run it
was long past.

It also leaves `_generate_image` meaning exactly "generate one Target", with no
reporting branch inside it, and makes the existing multi-Target progress
heading honest — it counted Targets that could never generate.

Its `SystemExit(1)` on an empty Brief stays as the genuine error path. The
caller no longer reaches it; a runtime `assert` in its place was rejected as
production code asserting something the type system cannot express anyway.

## Consequences

- **`Nothing to generate.` is printed when every selected Target is skipped**,
  on stdout. Exiting 0 in silence would read as a crash rather than as an
  outcome. It is not printed after a partial batch, where the generated output
  speaks for itself.
- **One warning line per Target, not a grouped list.** A fully-unbriefed race
  under `--all` therefore produces a column of warnings. That is accepted: it
  matches how the rest of this CLI reports, stays greppable, and the volume is
  itself a fair signal about the race.
- **Warnings go to stderr, generation output to stdout**, so a caller piping
  the run still gets seeds and promote hints uncontaminated.
- **ADR 0010's cross-reference was updated.** It contrasted `refine` against
  the old "hard error" rule, which no longer exists under that name.
