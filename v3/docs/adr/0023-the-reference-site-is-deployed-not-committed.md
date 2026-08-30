# The reference site is deployed, not committed

Issue #110 asked to publish the generated gameplay reference so players can
reach it without cloning the repository or running `spf` themselves, with the
wording "only commit actual changes" — implying the rendered files would live
in git, updated when they change.

That wording does not survive contact with what rendering actually produces.

## PDFs are not byte-reproducible

Rendering `general-rules --format pdf` twice from identical input, back to
back, produced files differing at byte 102274: pdflatex stamps a creation time
and a document `/ID` into every PDF it writes, and neither is disabled by
anything the templates control. "Only commit actual changes" assumes a diff
can tell a real content change from build noise; here it cannot, so every
merge to master would show binary churn on files whose content did not
change. `SOURCE_DATE_EPOCH` and a fixed `/ID` can suppress this for some
LaTeX toolchains, but pinning it is a build-hygiene project of its own and out
of scope for #110 — recorded here so a future "fix" doesn't reach for
commit-back without first re-reading this paragraph.

## Decision

**The reference site is built by CI on every push to `master` and deployed to
GitHub Pages as a build artifact. Nothing rendered is committed to git.**

`master` is the trigger because of the site's own contract:

> Everything on the site was generated from current source data on the last
> green master.

A player who finds a stat wrong can always check it against `master` at that
moment — there is no lag, no cached branch, no "which commit was this built
from" question to answer, because the answer is always "the one currently on
master".

## The Site contract excludes the legacy root PDFs

The repository root already holds a pile of hand-made PDFs (`rules.pdf`,
`cheatsheet.pdf`, `quickrules.pdf`, and others) of unknown vintage, predating
the render pipeline. The contract above is exactly why they cannot ride along:
a hand-made file sitting next to a generated one on the same site breaks the
guarantee invisibly, and a player looking at the page has no way to tell
which is which. If one of them is still worth keeping, the fix is to make it
a Product — an authored, rendered thing the pipeline can vouch for — not to
staple it onto the deploy. `cheatsheet.md` becoming a Product is deferred, not
rejected (see Deferred, below).

The `2025` tournament pack and `armies/demo.json` are excluded for a different
reason: publishing a live tournament roster is an editorial call the build
should not make unilaterally, and the demo army is a fixture, not a real one.

**The tournament-pack half of that paragraph is superseded by ADR 0028**,
which publishes the packs an authored Site Index names: an archived tournament
is history rather than a live claim, and the editorial call is now written
down by a human instead of made by the build. `armies/demo.json` stays
excluded for the reason above.

## Whole-site failure policy

ADR 0022 decided that an Army Pack fails to build entirely if any Army in its
Index fails to load or validate, rather than silently omitting the broken
one — "a silently missing competitor is worse than a build that refuses."
**That reasoning is extended from one Product to the whole site: if any file
fails to render, the whole deploy step is skipped and the previously-published
site is left standing.**

A stale-but-complete site degrades safely — a player sees rules that are a
few commits behind, notices nothing broken. A partial publish silently drops
a page a player relies on, with nothing on the page itself saying so. The
asymmetry is why "fail loud, publish nothing" beats "publish what built."

## Alternatives rejected

**Commit the rendered files back to `master`.** Rejected primarily for the
non-determinism above: every merge would show binary diffs in files whose
actual content is unchanged, and there is no way to tell real content churn
from build noise without pinning `SOURCE_DATE_EPOCH` — which is not attempted
here. Secondarily, it makes every merge to `master` also a build step,
coupling an unrelated concern (does this PR's rules text look right) to
whether pdflatex happened to succeed that day.

**A `gh-pages` branch holding the built site.** This is the same
binary-churn objection as commit-back, just relocated to a second branch
instead of `master`. Accepting the churn there while rejecting it on
`master` would be an inconsistent application of the same argument — if
non-determinism disqualifies commit-back, it disqualifies committing the
output anywhere.

**GitHub Releases**, one per version-tagged snapshot. A reasonable idea for
letting a player pin to "the rules as of tournament X", but it answers a
different question than #110 asked (a stable, always-current reference site)
and needs no design decision to add later — deferred, not rejected.

## Consequences

- `.github/workflows/docs.yml` triggers on `push` to `master` only; no PR
  preview builds for now (GitHub's PR-comment file attachment is browser-only,
  and the realistic CI-side alternative is an artifact-zip download, not a
  preview — not worth the YAML for what it buys).
- The published URL (`https://hssmalo.github.io/steampunkfantasy/`) is
  treated as stable once live: it gets pasted into chat and printed on paper,
  same as the render paths it mirrors exactly (`output/army-rules/showcase-elf.pdf`
  is `/army-rules/showcase-elf.pdf` on the site, with zero mapping logic to
  drift).
- A failed deploy leaves the previous build live and must be noticed by a
  human — this only works if failed-Action notifications are actually on,
  which is why the setup wizard has a step confirming that account-level
  setting explicitly rather than assuming it.
