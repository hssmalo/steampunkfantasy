# Workflows

A **Workflow** is a ComfyUI API-format graph (JSON) naming the nodes and models
one image generation runs. The Image Asset Service submits one per resolved
**Environment** and **Profile**, patching *only* the positive prompt and a
per-job seed into it — everything else (model, steps, cfg, LoRAs, negative
prompt) runs exactly as authored.

Each **Profile** is a named pair of Workflows: one for generating, one for
**Refinement** (`spf assets refine`). A refine Workflow uses an instruction-edit
model (Qwen-Image-Edit) and takes one extra patch point — the init image.

## Files

Workflows live under `workflows/<env>/`, one directory per Environment:

- **`workflows/cloud/`** — committed. Submitted to Comfy Cloud when
  `env = "cloud"`.
- **`workflows/local/`** — **gitignored, per-machine.** Used when
  `env = "local"`.
- **`workflows/examples/`** — committed reference. Never scanned for
  Profiles; not a valid Environment.

Within an env directory, a Profile is the filename stem of a `*.json` file.
The generate Workflow is `<profile>.json`; the refine Workflow is
`<profile>-refine.json`. For example, the `qwen` Profile under `cloud` is:

```
workflows/cloud/qwen.json           # generate
workflows/cloud/qwen-refine.json     # refine
```

The default Profile is configured per-env (`assets.image.comfyui.local.profile`
and `assets.image.comfyui.cloud.profile`). Override with `--profile` or
`SPF_COMFYUI_PROFILE`.

## Listing what is here

`spf assets profiles` lists every Profile each Environment offers, marks the
one that Environment is configured to use, and flags any missing its refine
Workflow:

```console
$ spf assets profiles
local  (selected)  not set up (no workflows in workflows/local/)
cloud
    krea2  workflows/cloud/krea2.json  (no refine workflow)
  * qwen   workflows/cloud/qwen.json
```

Because Profiles are discovered rather than declared, this is the only way to
see what is actually available. It exits non-zero when a *configured* Profile
does not resolve, which is why `just validate` runs it; an Environment with no
directory is reported and skipped, so a fresh clone passes.

## Adding a Profile

1. Export the graph from ComfyUI using **Save (API Format)**, *not* the plain
   Save (that exports UI format, which the Service cannot run).
2. Drop it into `workflows/<env>/<name>.json` (generate) and
   `workflows/<env>/<name>-refine.json` (refine).
3. Select it with `--profile <name>` or set it as the default in config.
4. No config edit is needed for the Service to discover it.

## Running locally

Copy `workflows/examples/qwen.json` to both locations if you run this exact
Qwen setup:

```sh
mkdir -p workflows/local
cp workflows/examples/qwen.json workflows/local/qwen.json
```

Then author a refine graph at `workflows/local/qwen-refine.json`. A missing
refine file is fine until you actually run a Refinement, which then fails with
a clean error rather than breaking `spf assets image`.

The graph must have exactly one sampler (`KSampler` / `KSamplerAdvanced`)
whose `positive` input links to a text node.

## Authoring a refine Workflow

Everything above applies, plus the following. Each one produces a graph that
looks fine in the ComfyUI canvas and then misbehaves under the Service, so
they are worth checking deliberately.

- **Exactly one `LoadImage`.** Qwen-Image-Edit's stock template ships two or
  three, wired for its multi-reference mode; delete the extras. The Service
  patches the sole `LoadImage` and rejects a graph with any other number.
- **Set the output resolution explicitly.** Refine output size comes from the
  `VAEEncode` of the scaled init image, not from an `EmptySD3LatentImage`. Use
  **`ImageScale` at `width=1328, height=1328`**, matching `cloud/qwen.json`. The
  stock template's `FluxKontextImageScale` takes no parameters and silently
  caps at ~1 MP (it gave 1024×1024), and `ImageScaleToTotalPixels` at the
  equivalent 1.76 MP gave 1360×1360 — its `resolution_steps` does not round
  the way the name suggests. `crop: "center"` forces the exact size, so a
  non-square init image would be cropped; if that ever matters, `ImageResizeKJ`
  with `keep_proportion` + `divisible_by: 16` is the node that handles it.
- **Wire a `SaveImage`.** The stock template only previews, so the graph runs
  fine in the UI and then returns a completed job with no images — which
  surfaces as a `ComfyUIError` about producing no images.
- **Author the negative prompt in.** The template's negative encoder is empty,
  which silently drops the standing guardrail. Copy the stock Qwen negative
  from `cloud/qwen.json`. The Service never patches the negative prompt, so it
  is tuned here or not at all.
- **Match the LoRA's generation to the UNet's.** A 2509 Lightning LoRA on a
  2511 UNet loads without erroring and quietly degrades the output, which at
  4 steps / cfg 1 reads as "the edit model is bad."
- Title the two `TextEncodeQwenImageEditPlus` nodes (Positive / Negative).
  They are structurally identical and otherwise only tellable apart by chasing
  links. Cosmetic — the Service is title-independent.

Note that the positive encoder in an edit graph
(`TextEncodeQwenImageEditPlus`) names its input `prompt`, where a generate
graph's `CLIPTextEncode` names it `text`. The Service accepts either.

API-format JSON is **export-only**: editing a graph in a text editor is often
easier than in the Cloud UI, but the result generally will not load back onto
the canvas.

## Licensing

For any model whose output we might sell, prefer **Apache-2.0 weights**
(Qwen-Image, FLUX.1 schnell). Avoid **FLUX.1 dev** (non-commercial weights)
and **FLUX.1 Krea [dev]** (inherits dev's non-commercial license). Since
Profiles carry no metadata by design, this constraint lives here in the README
rather than in code.
