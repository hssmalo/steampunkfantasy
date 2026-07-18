# The Image Asset service is ComfyUI, driven by one stdlib client across local and cloud

ADR 0006 established that the **Image** Asset kind is backed by a per-kind
`Service`, and ADR 0008's amendment fixed its protocol
(`generate(source, count, *, seed=None)`). This ADR settles **which provider**
backs it: **ComfyUI**, replacing the flaky Pollinations endpoint that
`PollinationsService` currently wraps. We drive it through **one HTTP client**
that talks to either a **local ComfyUI** (a contributor's own GPU box) or **Comfy
Cloud**, selected by per-environment config — `base_url`, an optional API key, and
each environment's own workflow file and model.

**Why:** Pollinations proved unreliable, and ComfyUI gives us a provider we
control on both ends. A prototype (runs A–E, 2026-07-15/16; see the amendment for
the throwaway's fate) measured the two things that mattered. First, **a local
ComfyUI is genuinely free to call "from outside"** — a stock server answered an
unauthenticated request and ran a full generation with no account, key, or
credits; ComfyUI's paid surface ("API Nodes") is opt-in *by node choice inside a
workflow*, not a toll gate on the HTTP API. Second, **one stdlib-only client
drives both backends** — the same client and the same graph generated an image
locally and on Comfy Cloud with nothing changed but the base URL and an
`X-API-Key` header. That makes ComfyUI serve both audiences at once: contributors
with a GPU run it locally for free, and contributors without one (the machine this
was scoped on has no usable GPU) use Comfy Cloud's paid tier at ~10 s/image.

We explicitly **do not require reproducibility across environments** — not even
approximately. Local and cloud may use different checkpoints and different
workflows; the same request may yield different images in each, and that is fine.
The goal is only to *generate images in both*.

## Consequences

- **`ComfyUIService` replaces `PollinationsService`** as the Image kind's
  `Service`, keeping the `generate(source, count, *, seed=None)` seam untouched.
  Its per-`count` sub-seed derivation (ADR 0008 amendment) carries over directly:
  ComfyUI takes a seed per job the same way the Pollinations URL did.
- **Config is per-environment, not per-workflow.** The Service is constructed with
  `base_url`, an optional `api_key`, and *this environment's own* `workflow_path`
  + model. There is no single workflow JSON that must run everywhere — an explicit
  non-goal. A workflow only has to be valid on the one server it targets.
- **Stdlib is sufficient.** The prototype drove both backends end-to-end on
  `urllib` + `json` alone. Reaching for an HTTP dependency in the real Service
  would itself be a signal worth questioning.
- **Two backend differences the client must handle**, both measured:
  1. **Poll route differs** — Comfy Cloud answers on `/api/jobs/{id}`, local on
     `/history/{id}`. Neither serves the other's route; the client tries both.
  2. **`object_info` is bulk-only on Cloud** — Cloud 404s the per-class
     `/api/object_info/{class}` route (use bulk `/api/object_info`, which both
     support), and on Cloud *membership in `object_info` ≠ loadable*: some
     advertised checkpoint names 400 at execution. Vet Cloud models by execution,
     not by the advertised list.
- **Licensing constrains the shippable model, not the plumbing.** For any model
  whose output we might sell, prefer **FLUX.1 schnell** or **Qwen-Image** (both
  Apache-2.0). Avoid **FLUX.1 dev** (non-commercial weights) and **SD 3.5** ($1M
  revenue tripwire). Comfy Cloud's inventory carries `flux1-schnell-fp8`, so the
  clean choice is available cloud-side. Full analysis:
  [`docs/research/comfyui.md`](../research/comfyui.md).
- **One performance number stays open:** local first-image latency was ~626 s on
  the contributor's Qwen box versus ~10 s on Cloud, but that local figure is
  almost certainly cold-start VRAM load, not steady state. Worth a `--twice`-style
  measurement before leaning on local for batch generation; it does not block the
  provider decision.
- **Out of scope, unchanged from ADR 0006:** how a Rendering embeds the Image, and
  anything past a committed Asset. This ADR only swaps the provider behind
  `generate`.

## Amendment (2026-07-16) — the shipped configuration

Implementing the Service (see
[`docs/plans/comfyui-image-service.md`](../plans/comfyui-image-service.md))
locks in these concrete choices:

- **Environment selector is TOML-only.** `assets.image.comfyui.env` is the sole
  selector, defaulting to `local`; switching to Comfy Cloud is a one-line TOML
  edit. No CLI flag, no env-var override.
- **Named Environment blocks.** `[assets.image.comfyui.local]` and
  `[…​.cloud]`, each with `base_url`, `workflow`, and `api_key_env` (the *name*
  of the env var holding the key, read lazily at generate time; empty ⇒ no auth
  header).
- **`workflows/` layout.** `cloud.json` is committed; `local.example.json` is a
  committed reference; `local.json` is per-machine and gitignored. Resolved
  under a new `paths.workflows`.
- **Qwen-Image (Apache-2.0) for both Environments.** `cloud.json` and
  `local.example.json` are the same Qwen-Image export, reconciled against
  Cloud's inventory by filename if needed. This **supersedes the "prefer FLUX.1
  schnell / SDXL" framing above** for the *shipped* choice, while staying
  consistent with this ADR's licensing guidance — Qwen-Image is Apache-2.0.
- **Patch only prompt + seed.** The runtime Service never patches model names,
  steps, cfg, LoRAs, or the negative prompt; those stay exactly as authored.

## Amendment (2026-07-16) — the prototype is retired

The throwaway probe under `prototypes/comfyui/` (a stdlib client plus a research
doc and decision log) existed only to answer the questions above. With every
load-bearing hypothesis settled and recorded here, it has been **deleted**. Its
findings live on in this ADR; the primary-source research it referenced remains at
[`docs/research/comfyui.md`](../research/comfyui.md).

## Amendment (2026-07-18) — the patch set grew for Refinement

[ADR 0010](0010-refinement-of-candidates.md) adds **Refinement**, which submits
a second Workflow per Environment through this same client. Two sentences above
are now narrower than the code:

- **The patch set is prompt + seed + the sole `LoadImage`.** "Patch only prompt
  + seed" still describes *generate* exactly. A Refinement patches one further
  input: the filename of the uploaded init image, on the graph's one
  `LoadImage`. Model names, steps, cfg, and LoRAs remain untouched in both
  operations. (The negative prompt did too when this was written; the amendment
  below overturns that.)
- **The positive node's prompt input is `text` *or* `prompt`.** Following the
  sampler's `positive` link and setting `text` was correct for every generate
  graph, where the encoder is `CLIPTextEncode`. Qwen's edit encoder,
  `TextEncodeQwenImageEditPlus`, declares the same input as `prompt`. That is
  the node's schema, not an authoring choice, so the client tries both keys.

Nothing else about this ADR changes. In particular the single-`_request` seam
still holds: the init-image upload is `multipart/form-data` built on the
stdlib, inside `_request`, rather than a new HTTP dependency.

## Amendment (2026-07-18) — the Negative Prompt is authored, not embedded

Issue 50 overturns this ADR's "Patch only prompt + seed" and the amendment
above's "the negative prompt remain[s] untouched in both operations". The patch
set is now **prompt + negative prompt + seed + the sole `LoadImage`**.

- **The Negative Prompt lives in `prompts/image-negative.txt`** and is
  **required** — a missing file is a hard error, not a fallback to the
  Workflow's authored value. (The amendment below makes that path configured
  rather than hardcoded; the default is unchanged.)
- **It replaces, it does not append.** Whatever the Workflow authors on its
  negative encoder is overwritten wholesale, exactly as the positive already
  is. The point is that the effective Negative Prompt is readable in one
  version-controlled file rather than being a function of a committed Workflow
  and a gitignored per-machine one.
- **One file serves both operations and both Environments.** ADR 0010's reason
  for a Refinement dropping the positive preamble does not extend to a
  constraint on output quality.
- **An unpatchable negative is a hard error**, symmetric with the positive.
  This rejects guidance-distilled Workflows that wire `negative` to a
  `ConditioningZeroOut` — notably FLUX.1 schnell, named above as the
  licensing-clean Cloud option. Neither shipped Environment does this today;
  the first Workflow that needs it decides then, loudly, rather than us
  shipping a silent skip that would hide real misconfigurations meanwhile.

Model names, steps, cfg, and LoRAs remain untouched. The single `_request` seam
and the stdlib-only constraint are unaffected.

**The seeded text is English, and it holds.** The Workflows' embedded negatives
were Chinese; the file was seeded with an English translation rather than the
verbatim original, which carried a real risk — the Chinese string was the only
negative ever validated against Qwen-Image, and this ADR renounces
cross-environment reproducibility, so there was no cheap A/B to settle it.
Discharged on 2026-07-18: the owner ran several generations and Refinements
under the English file and judged it to work well. That is a spot-check, not a
measurement — nobody compared the two strings head to head — so it is grounds
for keeping English, not for asserting the translation is equivalent.

## Amendment (2026-07-18) — both prompt files are configured, not hardcoded

Issue 50 first shipped the Negative Prompt as a hardcoded basename under
`paths.prompts`, following the precedent of the positive preamble. Review
rejected that precedent rather than extending it: **both** prompt files are now
named by config, under `[assets.image]`.

```toml
[assets.image]
prompt = "{paths.prompts}/image.txt"
negative_prompt = "{paths.prompts}/image-negative.txt"
```

- **They follow the Workflow keys' pattern**, interpolating under a `paths.*`
  root exactly as `ComfyUIEnvConfig.workflow` does under `paths.workflows`.
  A prompt file and a Workflow file are the same kind of thing — an authored
  input the Service reads by path — so they are configured the same way.
- **They sit in `[assets.image]`, not in an Environment block**, because one
  pair serves both Environments and both operations. Putting them per-Environment
  would invite exactly the drift this issue set out to remove.
- **Neither key has a default.** A missing one fails at config load, not at
  generate time — the same bargain `refine_workflow` already makes.
- **The positive was retrofitted for symmetry.** Making the negative
  configurable while the positive stayed a string literal would have left the
  more-edited of the two files the less-reachable one. This is scope beyond
  issue 50, taken deliberately: the hardcoding had never been examined as a
  decision, only inherited.

The shipped default paths are unchanged, so no existing checkout moves a file.

Nothing else about this ADR changes.
