# Workflows

A **Workflow** is a ComfyUI API-format graph (JSON) naming the nodes and models
one image generation runs. The Image Asset Service submits one per configured
**Environment** (`assets.image.comfyui.env`), patching *only* the positive
prompt and a per-job seed into it — everything else (model, steps, cfg, LoRAs,
negative prompt) runs exactly as authored.

Each Environment has two Workflows: one for generating, one for **Refinement**
(`spf assets refine`). A refine Workflow uses an instruction-edit model
(Qwen-Image-Edit) and takes one extra patch point — the init image.

## Files

- **`cloud.json`** — committed. Submitted to Comfy Cloud when `env = "cloud"`.
  A Qwen-Image (Apache-2.0) graph, reconciled against Cloud's model inventory.
- **`cloud-refine.json`** — committed. The Refinement graph for Comfy Cloud,
  on Qwen-Image-Edit-2511 (+ its matching 4-step Lightning LoRA).
- **`local.example.json`** — committed reference, the same Qwen-Image export.
- **`local.json`** — **git-ignored, per-machine.** Used when `env = "local"`.
- **`local-refine.json`** — **git-ignored, per-machine.** The local Refinement
  graph. A missing file is fine until you actually run a Refinement, which then
  fails with a clean error rather than breaking `spf assets image`.

## Running locally

Copy `local.example.json` to `local.json` if you run this exact Qwen setup:

```sh
cp workflows/local.example.json workflows/local.json
```

Or drop your own ComfyUI export at `local.json` — in ComfyUI use
**Save (API Format)**, *not* the plain Save (that exports UI format, which the
Service cannot run). The graph must have exactly one sampler (`KSampler` /
`KSamplerAdvanced`) whose `positive` input links to a text node.

## Authoring a refine Workflow

Everything above applies, plus the following. Each one produces a graph that
looks fine in the ComfyUI canvas and then misbehaves under the Service, so
they are worth checking deliberately.

- **Exactly one `LoadImage`.** Qwen-Image-Edit's stock template ships two or
  three, wired for its multi-reference mode; delete the extras. The Service
  patches the sole `LoadImage` and rejects a graph with any other number.
- **Set the output resolution explicitly.** Refine output size comes from the
  `VAEEncode` of the scaled init image, not from an `EmptySD3LatentImage`. Use
  **`ImageScale` at `width=1328, height=1328`**, matching `cloud.json`. The
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
  from `cloud.json`. The Service never patches the negative prompt, so it is
  tuned here or not at all.
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
