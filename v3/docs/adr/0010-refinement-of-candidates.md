# Refinement edits a Candidate by instruction, as an optional Service capability

ADR 0008 settled curation as a decoupled generate → promote flow, and ADR 0009
put ComfyUI behind `generate`. Both leave one gap: when a Candidate is *nearly*
right — the pose works, the hat is leather and should be brass — the only
recourse is re-rolling the whole batch and hoping. This ADR settles
**Refinement**: applying a verbatim **Correction** to one existing Candidate,
producing new Candidates under a derived **Lineage** name.

```console
$ spf assets refine goblin image goblin_infantry --from 2 "make the hat brass instead of leather"
Wrote candidates/goblin/images/goblin_infantry.2.1.png
Wrote candidates/goblin/images/goblin_infantry.2.2.png

$ spf assets promote goblin image goblin_infantry --pick 2.1
```

## Instruction-edit, not classic img2img

**Decision: an instruction-edit model (Qwen-Image-Edit), not
`LoadImage → VAEEncode → KSampler(denoise=x)`.**

Classic img2img is global, not local: every pixel is re-derived and `denoise`
is the only dial. Around 0.2–0.35 it changes texture while keeping structural
flaws; at 0.75+ it removes the flaw by redrawing the whole picture, background
included. Spatial references ("the ork on the left") carry almost no weight.
That is *re-roll with a nudge* — the exact thing Refinement exists to avoid.

Instruction-edit models are trained on `(image, instruction, edited image)`
triples: the prompt *is* the instruction, and unspecified regions are held
stable by design. Qwen-Image-Edit is also Apache-2.0 (satisfying ADR 0009's
licensing constraint) and the sibling of the Qwen-Image checkpoint both
Environments already run.

**This was confirmed by execution, not adopted on paper.** A spike
(2026-07-18) ran real Corrections against real Candidates on Comfy Cloud and
got pointed, local edits with background and composition held. A classic-img2img
fallback was specified in case the spike failed; it was never exercised.

The vetted Cloud stack, recorded because "advertised in `object_info`" is not
the same as "loadable" (ADR 0009):

| Role | Filename                                                       |
| ---- | -------------------------------------------------------------- |
| UNet | `qwen_image_edit_2511_fp8mixed.safetensors`                     |
| LoRA | `Qwen-Image-Edit-2511-Lightning-4steps-V1.0-bf16.safetensors`   |
| CLIP | `qwen_2.5_vl_7b_fp8_scaled.safetensors` (as `cloud.json`)       |
| VAE  | `qwen_image_vae.safetensors` (as `cloud.json`)                  |

**The LoRA's generation must match the UNet's.** A 2509 Lightning LoRA on a
2511 UNet loads without erroring and quietly degrades the output, which at
4 steps / cfg 1 reads as "the edit model is bad."

## The Correction is the whole positive prompt, verbatim

**Decision: nothing from `prompts/image.txt`, nothing from the race TOML, no
wrapper.** Edit models are trained on instructions; feeding one a scene
description alongside pulls it toward re-rendering rather than editing.

This follows from the choice above and stands or falls with it — under classic
img2img, prompt replacement would be actively wrong, since a bare "remove one
arm" gives the sampler nothing to reconstruct from at high denoise.

Consequently `refine` never looks up a description, and the "no description ⇒
hard error" rule that `spf assets image` enforces does not apply to it.

**The negative prompt stays unpatched** (ADR 0009), so a Correction is always a
*positive* statement. This is not a limitation to work around: the negative
prompt is a **standing guardrail** authored once into the Workflow JSON and
applied to every generation and Refinement alike. Tuning it is a
workflow-authoring change with no code involved.

## Refinement is an optional Service capability

**Decision: a second, optional protocol (`Refiner`) — not a widened
`generate`.** `Service.generate` stays exactly as ADR 0008/0009 fixed it, so
the Lore and Model kinds never grow an image concept they cannot use.
`spine.refine` checks the Kind's Service against the protocol and raises a
clean `TypeError` naming the Kind, never an `AttributeError`.

Rejected: widening `generate` with `init: bytes | None` (ripples an image
concept through every Kind); putting `refine` only on the concrete service and
calling it from the CLI (puts the candidate-writing loop in the CLI, where it
gets duplicated the moment anything else needs it).

## Lineage-derived Candidate naming

**Decision: a Refinement derives a new `name`.** Refining Candidate `2` of
`goblin_infantry` generates under the name `goblin_infantry.2`, yielding
`goblin_infantry.2.1.png`, `.2.2.png`, …

This is the existing `<name>.<index>.<extension>` layout with a derived name,
so it needs **zero** changes to the persistence loop or the layout rule.
Originals are never clobbered — which is the whole point, since falling back
when a nudge came out worse is the common case. Chaining follows the same rule
(`2.1` refines to `2.1.1`), and the derivation reads straight off the filename,
so **no provenance sidecar exists**. `promote --pick` and `refine --from` share
one validated dotted-index type.

Rejected: overwriting the same sequence (destroys the source being refined
from); appending as `goblin_infantry.4` (makes index numbers shift meaning
between runs, breaking `--from`/`--pick` as stable coordinates).

## The init image is always uploaded

**Decision: `POST /api/upload/image`, then patch the returned filename into the
graph's sole `LoadImage`.** The file in `candidates/` is the sole source of
truth.

Rejected: referencing ComfyUI's server-side outputs. `LoadImage` reads from
`input/` while generations land in `output/`, so the annotated-path form works
locally at best. It would also require persisting ComfyUI's
`filename`/`subfolder` per Candidate, and has no referent at all when refining
a week-old Candidate, or one generated in `local` while now on `cloud`. That is
two mechanisms plus new provenance state to save one HTTP call on a ~1–2 MB
payload.

The upload name is derived from the blob's digest, so refining the same
Candidate twice reuses one server-side file rather than accumulating
`foo (1).png`.

## Consequences

- **Each Environment gets a second Workflow key**, `refine_workflow`. The key
  is always present in config; the file it points at is optional until a
  Refinement is actually run, so a missing local refine graph surfaces as a
  clean error at refine time rather than breaking `spf assets image`.
- **A refine Workflow must have exactly one `LoadImage`.** Qwen-Image-Edit's
  stock template ships two or three, for a multi-image reference mode that is
  out of scope here. This is an authoring rule, documented in
  `workflows/README.md`, not a code concession.
- `--count` / `--seed` work exactly as for generate: N variants of the one
  Correction at different sub-seeds.
- **Out of scope:** multi-image reference edits; inpainting and masks; refining
  an already-promoted Asset (Refinement is closed over the candidates store);
  Refinement for the Lore and Model kinds (the protocol makes it possible,
  nothing implements it).
