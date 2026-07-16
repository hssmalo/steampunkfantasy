# Workflows

A **Workflow** is a ComfyUI API-format graph (JSON) naming the nodes and models
one image generation runs. The Image Asset Service submits one per configured
**Environment** (`assets.image.comfyui.env`), patching *only* the positive
prompt and a per-job seed into it — everything else (model, steps, cfg, LoRAs,
negative prompt) runs exactly as authored.

## Files

- **`cloud.json`** — committed. Submitted to Comfy Cloud when `env = "cloud"`.
  A Qwen-Image (Apache-2.0) graph, reconciled against Cloud's model inventory.
- **`local.example.json`** — committed reference, the same Qwen-Image export.
- **`local.json`** — **git-ignored, per-machine.** Used when `env = "local"`.

## Running locally

Copy `local.example.json` to `local.json` if you run this exact Qwen setup:

```sh
cp workflows/local.example.json workflows/local.json
```

Or drop your own ComfyUI export at `local.json` — in ComfyUI use
**Save (API Format)**, *not* the plain Save (that exports UI format, which the
Service cannot run). The graph must have exactly one sampler (`KSampler` /
`KSamplerAdvanced`) whose `positive` input links to a text node.
