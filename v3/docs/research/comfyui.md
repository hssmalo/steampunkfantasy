# ComfyUI as the image backend — research

**Date:** 2026-07-14. **Question:** can ComfyUI replace Pollinations behind our
existing `Service` seam, with *one* code path serving both a locally self-hosted
ComfyUI and a cloud-hosted one?

Everything below is checked against primary sources (ComfyUI's own `server.py`,
`nodes.py`, `comfy/sample.py`, `script_examples/`, docs.comfy.org, and the model
licence texts). Where a claim could not be traced to a primary source it is
listed under [Unverified / open questions](#unverified--open-questions) rather
than smoothed over.

---

## Bottom line

**Yes — "one seam, two backends" is viable, and it's better than we hoped.**
Comfy Org's own cloud (`https://cloud.comfy.org`) exposes an API that its docs
explicitly describe as *"compatible with local ComfyUI's API, making it easy to
migrate existing integrations"*
([Cloud API overview](https://docs.comfy.org/development/cloud/overview)). Both
local and cloud accept the **same API-format workflow JSON** at
`POST /api/prompt`, both return a `prompt_id`, both expose
`GET /api/jobs/{prompt_id}` and `GET /api/view?filename=…&subfolder=…&type=…`.
Local ComfyUI mirrors *every* route under an `/api` prefix (verified in
`server.py`, quoted below), so a single client hitting `/api/…` paths works
against both. The difference really is close to `base_url` + an auth header.

A client can be written with **pure stdlib `urllib` + `json`** — ComfyUI's own
official example (`script_examples/basic_api_example.py`) is exactly that. So we
keep the current Pollinations dependency profile.

**The single biggest risk is not the API — it's the workflow JSON.** A workflow
is a graph that references *specific model files by filename* and *specific node
classes*. `POST /prompt` validates against whatever the target server has
installed and rejects with `node_errors` if a checkpoint or custom node is
missing. So the same `workflow_api.json` will only run on both local and cloud if
both have the same checkpoint file under the same name. That's the coupling that
will actually bite us: **not "two base URLs" but "two model inventories."** Pin a
checkpoint that both a contributor's local install and the cloud have, keep the
workflow to *core nodes only* (no custom nodes), and the seam holds.

Second risk, specific to this developer's machine: **an integrated Intel Arc
(Xe-LPG) iGPU is a poor local host.** ComfyUI supports Intel XPU officially, but
"supported" ≠ "usable at speed with no dedicated VRAM." Plan for the local path
to be the *contributors-with-GPUs* path and the cloud path (or CPU, very slowly)
to be the fallback on this machine.

---

## 1. Local HTTP API — the actual route surface

Verified by reading
[`server.py`](https://github.com/comfyanonymous/ComfyUI/blob/master/server.py) on
`master`.

### Every route is mirrored under `/api`

This is the load-bearing fact for our design. From `server.py`:

```python
api_routes = web.RouteTableDef()
for route in self.routes:
    if isinstance(route, web.RouteDef):
        api_routes.route(route.method, "/api" + route.path)(route.handler, **route.kwargs)
self.app.add_routes(api_routes)
self.app.add_routes(self.routes)
```

So `POST /prompt` and `POST /api/prompt` are the *same handler*. **Write the
client against the `/api/…` forms** — those are the ones Comfy Cloud also serves.

### `POST /prompt` (= `POST /api/prompt`)

Request body keys (from the handler): `prompt` (required — the API-format graph),
`client_id` (optional, folded into `extra_data`), `extra_data` (optional
arbitrary metadata; also where a Comfy API key goes for Partner/API nodes),
`number` / `front` (queue priority), `prompt_id` (optional; server mints a UUID
if absent), `partial_execution_targets` (optional subset of nodes to run).

It **returns immediately** — it queues, it does not block:

```json
{"prompt_id": "1d2f…-uuid", "number": 3, "node_errors": {}}
```

On validation failure it returns **HTTP 400** with a body carrying `error` and
`node_errors`, keyed by node id, naming the offending input. This is how a
missing checkpoint file or an unknown `class_type` surfaces.

### `GET /history/{prompt_id}` (= `/api/history/{prompt_id}`)

```python
@routes.get("/history/{prompt_id}")
async def get_history_prompt_id(request):
    prompt_id = request.match_info.get("prompt_id", None)
    return web.json_response(self.prompt_queue.get_history(prompt_id=prompt_id))
```

Returns `{}` while the job is still queued/running, and once complete an entry
keyed by `prompt_id` containing `prompt`, `status`, and `outputs`. `outputs` is
`node_id -> {"images": [{"filename": …, "subfolder": …, "type": "output"}, …]}` —
exactly the dict `SaveImage` returns (see §4).

### `GET /view` (= `/api/view`)

Query params (verified in the handler): `filename` (required), `type` in
`input|temp|output` (default `output`), `subfolder`, plus optional `preview`
(`format;quality`, e.g. `webp;85`) and `channel` (`rgb|a|rgba`). Returns raw
bytes. Feed it the three fields straight out of `outputs`.

### Other routes we care about

- `POST /upload/image` — multipart, fields `image`, `type`, `subfolder`,
  `overwrite`; returns `{"name":…, "subfolder":…, "type":…}`. (Not needed for
  txt2img.)
- `GET /object_info` (and `/object_info/{node_class}`) — every node class with its
  `INPUT_TYPES`. This is the introspection endpoint: it tells you which
  checkpoints the server actually has, so it's the right pre-flight check for the
  "two model inventories" risk.
- `GET /queue`, `POST /queue` (`clear` / `delete`), `POST /interrupt`,
  `POST /free` (`unload_models`, `free_memory`), `GET /system_stats`.
- `GET /api/jobs` and `GET /api/jobs/{job_id}` — a newer, *normalised* job view
  (see §5); `GET /prompt` returns just `{"exec_info": {"queue_remaining": N}}`.

### Websocket vs polling

`GET /ws?clientId=…` streams `status`, `executing` (`{"node": id}`, with
`node: null` meaning "this prompt is done"), `executed`, `execution_error`,
`execution_cached`, plus binary `b_preview` frames.

**Polling `/history` is a legitimate, first-class pattern, not a hack.** Both are
official: ComfyUI ships
[`script_examples/basic_api_example.py`](https://github.com/comfyanonymous/ComfyUI/blob/master/script_examples/basic_api_example.py)
(pure `urllib`, fire-and-forget POST) and
[`script_examples/websockets_api_example.py`](https://github.com/comfyanonymous/ComfyUI/blob/master/script_examples/websockets_api_example.py)
(uses the third-party `websocket-client` package). Notably, even the websocket
example uses the socket *only as a completion signal* and then fetches results
over plain HTTP `/history/{prompt_id}` → `/view`. The websocket buys you live
progress; it buys you nothing for correctness.

**For us:** poll `/api/history/{prompt_id}` (or `/api/jobs/{prompt_id}`). Our
`generate()` is a blocking batch call in a CLI — nobody is watching a progress
bar. Progress reporting is the only thing we'd give up, and we can get coarse
progress for free by submitting N jobs and printing as each completes.

---

## 2. Workflow JSON — UI format vs API format

Two distinct serialisations
([official docs](https://docs.comfy.org/development/api-development/workflow-api-format)):

- **UI format** (`File → Save`) — the editable graph: node positions, sizes,
  colours, groups, links. **The `/prompt` endpoint does not accept this.**
  Posting it is one of the most common causes of a `node_errors` 400.
- **API format** (`File → Export (API)`) — flat dict, **keyed by node id as a
  string**, each value having `class_type` and `inputs`. Links are
  `["<source_node_id>", <output_index>]`.

Verbatim from ComfyUI's own example:

```json
{
  "3": {
    "class_type": "KSampler",
    "inputs": {
      "seed": 8566257, "steps": 20, "cfg": 8,
      "sampler_name": "euler", "scheduler": "normal", "denoise": 1,
      "model": ["4", 0], "positive": ["6", 0], "negative": ["7", 0],
      "latent_image": ["5", 0]
    }
  },
  "4": {"class_type": "CheckpointLoaderSimple",
        "inputs": {"ckpt_name": "v1-5-pruned-emaonly.safetensors"}},
  "5": {"class_type": "EmptyLatentImage",
        "inputs": {"batch_size": 1, "height": 512, "width": 512}},
  "6": {"class_type": "CLIPTextEncode", "inputs": {"text": "…", "clip": ["4", 1]}},
  "9": {"class_type": "SaveImage",
        "inputs": {"filename_prefix": "ComfyUI", "images": ["8", 0]}}
}
```

And the official way to patch it is… exactly what you'd guess:

```python
prompt["6"]["inputs"]["text"] = "masterpiece best quality man"
prompt["3"]["inputs"]["seed"] = 5
```

### Addressing nodes by something other than a numeric id

**There is no server-side mechanism for this.** The `/prompt` handler takes the
dict as-is; nothing resolves titles, and core ComfyUI has no "external input" /
named-parameter convention. (The named-input idea exists only in *third-party*
wrappers — ComfyDeploy's external-input custom nodes, RunComfy's "pick the parts
you want to tweak", fal's input/output nodes — and every one of those is a
proprietary custom node, which breaks portability to a plain local ComfyUI.)

The one thing core does give us: the API export includes a **`_meta` block with
the node's `title`**. The server ignores it, but *we* can use it client-side:

```python
def node_id(graph, title):           # resolve by title, fail loudly
    ids = [k for k, v in graph.items() if v.get("_meta", {}).get("title") == title]
    if len(ids) != 1:
        raise ValueError(f"expected exactly one node titled {title!r}, found {ids}")
    return ids[0]
```

**Recommendation:** ship a workflow JSON *in the repo* (e.g.
`prompts/image.workflow.json`), whose nodes we deliberately re-title
(`SPF Prompt`, `SPF Sampler`, `SPF Save`), and patch by title with a hard error if
a title is missing or ambiguous. That survives someone re-arranging or renumbering
the graph, and fails loudly rather than silently patching the wrong node — which
is what patching `["3"]` would do. It does *not* survive someone renaming a title,
but that's a visible, intentional act.

---

## 3. Determinism and seeds

`KSampler`'s `seed` input is an `INT` with `min: 0, max: 0xffffffffffffffff`
(from `nodes.py` `INPUT_TYPES`) — note the range is **64-bit**, much wider than
our current `2**31` bound. Noise comes from
[`comfy/sample.py`](https://github.com/comfyanonymous/ComfyUI/blob/master/comfy/sample.py):

```python
def prepare_noise(latent_image, seed, noise_inds=None):
    """
    creates random noise given a latent image and a seed.
    optional arg skip can be used to skip and discard x number of noise generations for a given seed
    """
    generator = torch.manual_seed(seed)
    ...
```

So: **one `torch.manual_seed(seed)` per job, then `torch.randn` called once per
batch element, consuming generator state.** Consequences:

- **`batch_size: N` from one seed → N *different* images.** Each batch index gets
  the next draw from the same seeded generator. It is *not* N copies of the same
  image.
- Fixed seed + fixed checkpoint + fixed workflow + same machine/torch/device →
  **reproducible**. This is the standard, relied-upon behaviour of the whole
  ComfyUI ecosystem.
- **Across machines / GPUs / torch versions it is NOT guaranteed.** The noise
  tensor from `torch.manual_seed` is stable, but the sampling math afterwards runs
  in fp16/bf16 on different kernels; CUDA vs XPU vs CPU will not produce
  bit-identical images. Treat determinism as *within one host*, which is all our
  `--seed` promise ("rerun with `--seed X` to reproduce") actually needs — but it
  does mean a teammate re-running our seed on their GPU may get a *slightly*
  different image. (Not verified: whether ComfyUI makes any cross-device
  reproducibility claim. I found none.)

### Which maps better onto our `Service` contract?

Our contract is: derive `count` sub-seeds from one base seed, return `count`
values. Two mappings:

| | N jobs, `batch_size: 1`, one sub-seed each | 1 job, `batch_size: N`, one seed |
|---|---|---|
| Matches `Service` docstring | **exactly** | no — one seed, N implicit variants |
| Candidate *i* reproducible alone | **yes** — resubmit its own sub-seed | no — must regen the whole batch |
| Peak VRAM | **low** (1 image at a time) | N× the latents — the thing that OOMs low-VRAM hosts |
| Speed | slower (per-job overhead, though the model stays loaded) | faster |
| Cloud concurrency | N jobs vs a 1–5 concurrent-job cap (see §5) | 1 job |

**Take the N-jobs mapping.** It's a literal match for the existing
`PollinationsService` shape (`rng.randrange` per candidate, one request each), it
keeps peak memory at one image — which matters enormously on a low-VRAM host — and
it makes a single candidate individually reproducible, which is exactly what the
generate→promote curation flow (ADR 0008) wants: "candidate 3 was good, give me
more like it." Submit all N up front (`/prompt` returns immediately), then poll;
you get pipelining for free without holding N images in VRAM at once.

---

## 4. PNG metadata — `SaveImage` embeds the recipe by default

From `nodes.py`, `SaveImage.save_images`:

```python
metadata = None
if not args.disable_metadata:
    metadata = PngInfo()
    if prompt is not None:
        metadata.add_text("prompt", json.dumps(prompt))
    if extra_pnginfo is not None:
        for x in extra_pnginfo:
            metadata.add_text(x, json.dumps(extra_pnginfo[x]))
```

with `INPUT_TYPES` declaring `"hidden": {"prompt": "PROMPT", "extra_pnginfo": "EXTRA_PNGINFO"}`.

- **Yes, on by default.** PNG **tEXt chunks**. Key **`prompt`** = the full
  API-format graph we POSTed. Key **`workflow`** = the UI-format graph, *but only
  if the caller supplied it* — `extra_pnginfo` is populated from
  `extra_data.extra_pnginfo` in the request. A pure-API client that doesn't send
  it gets a `prompt` chunk and no `workflow` chunk.
- **Disable with `--disable-metadata`** (help string: *"Disable saving prompt
  metadata in files."*) — a **server-side** flag, so it's the *operator's* choice,
  not ours per-request. We cannot rely on it being either on or off.
- **This is a genuine win for us.** A promoted asset carries its own recipe:
  seed, sampler, steps, checkpoint filename, full prompt text. It makes the
  committed `assets/` tree self-documenting in a way ADR 0006 (assets as curated
  source-of-truth) clearly wants.
- **Leak risk is real but modest.** The `prompt` chunk contains whatever is in the
  graph — including `ckpt_name`, LoRA filenames, and `filename_prefix`. It does
  **not** contain absolute filesystem paths *unless* a node input holds one (e.g.
  a `filename_prefix` of `/home/gahjelle/…`, or a custom node with a path input).
  Keep `filename_prefix` a bare relative string and there's nothing sensitive. If
  we'd rather not ship it at all, strip tEXt chunks on `promote` — that's a few
  lines and belongs on the deterministic side of the flow.

---

## 5. Comfy Cloud vs API/"Partner" Nodes — these are two different things

They get conflated constantly. They are unrelated, and only one of them matters
to our design.

### (a) Comfy Cloud — a hosted ComfyUI run by Comfy Org. **This is the one we want.**

- **It exists and it's first-party.** [comfy.org/cloud](https://comfy.org/cloud/),
  docs at
  [docs.comfy.org/development/cloud/overview](https://docs.comfy.org/development/cloud/overview).
- **Base URL `https://cloud.comfy.org`; auth is a single `X-API-Key` header**
  (keys from `platform.comfy.org/profile/api-keys`).
- **Same API.** The docs state it is *"compatible with local ComfyUI's API, making
  it easy to migrate existing integrations."* Concretely:

  ```bash
  curl -X POST "https://cloud.comfy.org/api/prompt" \
    -H "X-API-Key: $COMFY_CLOUD_API_KEY" \
    -H "Content-Type: application/json" \
    -d '{"prompt": '"$(cat workflow_api.json)"'}'
  ```

  → `{"prompt_id": …}`; poll `GET /api/job/{prompt_id}/status` →
  `{"status": "pending|in_progress|completed|failed|cancelled"}`; fetch details
  via `GET /api/jobs/{prompt_id}` (has `outputs`); download via
  `GET /api/view?filename=…&subfolder=…&type=output`, which **302-redirects to a
  signed URL** (so the client must follow redirects — `urllib` does by default).
- **The same body, the same API-format workflow JSON, the same `prompt_id`.** The
  only deltas: `X-API-Key` instead of nothing, and the status endpoint (`/api/job/
  {id}/status`) which I could not confirm exists on a local server. Local *does*
  have `GET /api/jobs/{job_id}` with the same `pending|in_progress|completed|
  failed|cancelled` status vocabulary (from `comfy_execution/jobs.py`), so
  **`/api/jobs/{id}` looks like the one endpoint that works on both** — prefer it
  over `/history`.
- **Pricing** ([comfy.org/cloud/pricing](https://comfy.org/cloud/pricing/)):
  Standard **$20/mo**, 4,200 credits, **1 concurrent workflow via API**; Creator
  **$35/mo**, 7,400 credits, 3 concurrent, own LoRAs; Pro **$100/mo**, 21,100
  credits, 5 concurrent, 1h runtime cap. Billed on **active GPU time only**.
  Hardware: RTX 6000 Pro (Blackwell), 96 GB VRAM. 900+ pre-installed models.
  **API access requires a paid tier — the free tier is excluded.**
  → Note the **concurrency cap of 1** on the cheapest tier. Our N-jobs-per-batch
  mapping still works (jobs queue; the cap throttles, it doesn't error), but a
  `count=4` batch on Standard is serialised.

### (b) API Nodes / "Partner Nodes" — hosted *models* called from *inside* a workflow. **Not what we want.**

- These are nodes ([docs](https://docs.comfy.org/tutorials/api-nodes/overview)) that
  make the ComfyUI server call an *external* commercial API — Flux, Ideogram,
  Recraft, OpenAI, Kling, Veo, Seedream, Runway, ElevenLabs, 40+ providers.
- **Auth:** a Comfy account login, or an `api_key_comfy_org` key placed in the
  request's `extra_data` — ComfyUI's own example shows exactly this:

  ```python
  # p["extra_data"] = {"api_key_comfy_org": "comfyui-87d01e28d…"}
  ```
- **Billing:** prepaid credits, **211 credits = 1 USD**
  ([price list](https://docs.comfy.org/tutorials/partner-nodes/pricing)) — e.g.
  Flux ≈ 6.33–16.88 credits/run (≈ $0.03–0.08), Recraft V4 Pro 52.75 credits/image
  (≈ $0.25).
- **Crucially: they DO change the workflow JSON.** A workflow using an API node
  has different `class_type`s than a local one. **A local-model workflow and an
  API-node workflow are NOT interchangeable** — they're different graphs. They
  also work *the same way on a local ComfyUI* (a local server happily calls the
  hosted model, if it has credits and network) and can be disabled entirely with
  `--disable-api-nodes`.

**The distinction that matters:** *Comfy Cloud* changes **where the workflow runs**
(and nothing about the JSON). *API Nodes* change **what the workflow is**. Our
"one seam, two backends" bet rides entirely on (a), and (a) genuinely delivers.
We should treat (b) as a *third*, separate option — a way to get a
better-than-SDXL model without owning a GPU — and if we ever want it, it's a
*different workflow file*, selected by config, not a different base URL.

---

## 6. Third-party hosted ComfyUI

The question was: which of these is "just a different base_url"? Answer: **almost
none of them.** Most wrap ComfyUI in a proprietary API.

| Provider | ComfyUI-native `/prompt`, `/history`, `/view`? | Bring your own workflow JSON? | Pricing shape |
|---|---|---|---|
| **Comfy Cloud** (Comfy Org) | **Yes** — `/api/prompt`, `/api/jobs/{id}`, `/api/view`; docs say "compatible with local ComfyUI's API" | Yes, API-format | Subscription $20/$35/$100 + credits, billed on active GPU time |
| **RunComfy** | **Partly** — has an **[instance proxy](https://docs.runcomfy.com/serverless/instance-proxy-endpoints)**: `POST /prod/v2/deployments/{deployment_id}/instances/{instance_id}/proxy/{comfy_backend_path}` with `Authorization: Bearer …`, explicitly forwarding to *"ComfyUI backend endpoints (e.g. `GET /object_info`, `POST /api/prompt`)"*. But the *primary* path is their own deploy-then-invoke serverless API | Yes — export API JSON, mark which inputs are tweakable | Not verified (see below) |
| **RunPod** (`runpod-workers/worker-comfyui`) | **No** — RunPod's serverless `/run` and `/runsync`. Workflow goes in `input.workflow` | Yes — API-format JSON in `input.workflow`; custom models/nodes via network volume or Docker image | Per GPU-second (RunPod serverless) |
| **Replicate** (`fofr/any-comfyui-workflow`) | **No** — Replicate's predictions API (`POST /v1/predictions`) | Yes — API-format JSON as the `workflow_json` input; [fixed list of supported weights/custom nodes](https://github.com/replicate/cog-comfyui) | ≈ **$0.02/run**, ~22 s on an L40S; billed per GPU-second |
| **Modal** | **You build it** — the [official example](https://modal.com/docs/examples/comfyapp) runs ComfyUI behind *your own* web endpoint (`/infer_sync`), but nothing stops you proxying the native API yourself | Yes — it's your container | Per GPU-second, scale-to-zero |
| **fal.ai** | **No** — `POST https://fal.run/fal-ai/comfy-server`, and it needs a **fal-specific** workflow format ("Save as fal format", with fal input/output nodes) | Yes, but *converted* — the fal format is not the vanilla API format | Per-request / per GPU-second |
| **ComfyDeploy** | Not verified (fetch failed) — believed proprietary REST + custom "external input" nodes | Yes, believed via their own custom nodes | Not verified |

**Reading:** the *only* provider where "local vs cloud = a different `base_url` +
an auth header" is straightforwardly true is **Comfy Cloud** — which is
convenient, since it's also the first-party one. RunComfy's instance proxy is the
one genuine runner-up, but it requires deploying first and threading a
deployment+instance id into the path, so the URL shape differs, not just the host.

For our seam this is fine: **design the client for the ComfyUI-native API
(local + Comfy Cloud), and treat any other provider as a future, separate
`Service` implementation** — which is exactly what the `Service` protocol is for.
The protocol already isolates us: swapping `PollinationsService` for
`ComfyUIService` touches one class.

---

## 7. Hardware — Intel Arc, WSL2, and this machine specifically

**Official support: yes, in principle.** ComfyUI's
[system requirements](https://docs.comfy.org/installation/system_requirements)
list *"Intel — Arc series with native PyTorch `torch.xpu` support"* alongside
NVIDIA/CUDA, AMD/ROCm and Apple/Metal. The README's install line:

```
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/xpu
```

(IPEX — Intel Extension for PyTorch — is the older path and is being wound down;
upstream `torch.xpu` is now the way.)

**But for an *integrated* Xe-LPG iGPU with no dedicated VRAM, the honest answer is
"officially supported, practically marginal."**

- The docs say **"Arc series"**. They say nothing about integrated Core Ultra
  graphics, and nothing about minimum VRAM, RAM, or WSL2. That's a documentation
  gap, not an endorsement.
- ComfyUI's README does claim *"smart memory management: can automatically run
  large models on GPUs with as low as 1GB vram with smart offloading"* — the
  offload machinery is real and good.
- Against that: there is an **open issue,
  [#9128 "XPU out of memory on Intel CPU although plenty of memory is available"](https://github.com/comfyanonymous/ComfyUI/issues/9128)**,
  reporting OOM on Core Ultra with Flux despite ample system RAM. And a
  [discussion](https://github.com/Comfy-Org/ComfyUI/discussions/14092) on the
  general pathology: once you spill into *shared* GPU memory, throughput collapses.
  An iGPU with no dedicated VRAM is *permanently* in that regime.
- **I could not find a primary-source benchmark for SDXL on Xe-LPG under WSL2.**
  See open questions. My expectation — flagged as expectation, not fact — is
  minutes, not seconds, per 1024×1024 SDXL image, if it runs at all.

**Low-VRAM levers ComfyUI gives you** (verified in `cli_args.py`):
`--lowvram`, `--novram` (*"when lowvram isn't enough"*), `--cpu` (*"to use the CPU
for everything (slow)"*), `--highvram`, `--gpu-only`, `--reserve-vram <GB>`.
Plus fp8 weights: the
[official Flux tutorial](https://docs.comfy.org/tutorials/flux/flux-1-text-to-image)
notes Flux is **12B params, ~23 GB** at full precision, recommends the fp16 T5
text encoder only *"when your VRAM is greater than 32GB"*, and offers
`t5xxl_fp8_e4m3fn` and fp8 checkpoints for low-VRAM machines. GGUF quantised
variants exist but are **community custom nodes (ComfyUI-GGUF), not core** — which
means using them breaks the "core nodes only" portability rule from §2. Don't.

**Practical read for us:** SDXL (~6.9 GB fp16 checkpoint) is the only realistic
local model on modest hardware; Flux dev is out of reach on the iGPU. Structure
this as: **contributors with real GPUs run local; this machine uses Comfy Cloud**
(or, for a smoke test, `--cpu` with a small model and infinite patience). The good
news is that this is precisely the scenario the two-backend design was built for.

---

## 8. Model licensing — which checkpoints can we pin if SPF is ever sold?

SteamPunkFantasy may eventually be sold, so this constrains the pin. Note the
critical distinction the licences themselves draw: **the licence on the *model
weights* is not the same as the licence on the *outputs*.**

| Model | Licence | Commercial use of **outputs**? | Commercial use of the **weights**? |
|---|---|---|---|
| **SDXL 1.0** | [CreativeML Open RAIL++-M](https://huggingface.co/stabilityai/stable-diffusion-xl-base-1.0/blob/main/LICENSE.md) | **Yes** | **Yes** — explicitly permits hosting/SaaS and redistribution, subject to the Attachment A use-based restrictions (which you must pass on downstream) |
| **FLUX.1 [schnell]** | **Apache 2.0** ([model card](https://huggingface.co/black-forest-labs/FLUX.1-schnell)) | **Yes** | **Yes** — fully permissive. 1–4 steps. |
| **FLUX.1 [dev]** | [FLUX.1 [dev] Non-Commercial License](https://huggingface.co/black-forest-labs/FLUX.1-dev/blob/main/LICENSE.md) | **Yes** — BFL disclaims ownership of Outputs and permits commercial exploitation of them, *except* to train competing models | **No** — the weights are restricted to a "Non-Commercial Purpose"; production/revenue-generating use of the model needs a paid BFL licence |
| **Stable Diffusion 3.5 Large** | [Stability AI Community License](https://stability.ai/community-license-agreement) | **Yes** | **Yes, conditionally** — free for commercial use only if you have **< $1M total annual revenue**; above that you need an Enterprise License |
| **Qwen-Image** | **Apache 2.0** ([model card](https://huggingface.co/Qwen/Qwen-Image)) | **Yes** | **Yes** — fully permissive; a strong, current, genuinely open option |

**Recommendation: pin SDXL 1.0 (Open RAIL++-M) or Qwen-Image / FLUX.1 [schnell]
(both Apache-2.0).** Apache-2.0 is the cleanest possible answer and both schnell
and Qwen-Image carry it.

**Avoid pinning FLUX.1 [dev] as the default.** The nuance is subtle and worth
stating precisely, because it's widely misreported: *outputs* from dev **can** be
sold — the licence explicitly permits commercial exploitation of Outputs. What is
forbidden is using the *weights* for a commercial purpose. Generating art for a
game you sell is a commercial use of the model, even if the resulting image is
fine to ship. **That's a lawyer question, not an engineering one**, and the whole
ambiguity evaporates if we pin an Apache-2.0 model. So pin one.

SD 3.5's Community License is *probably* fine for us today (we're well under $1M),
but it embeds a revenue tripwire into our asset pipeline, which is an odd thing to
build in on purpose.

---

## 9. Python dependencies — stdlib is enough

**Yes, a client can be pure stdlib.** ComfyUI's own official example is:

```python
import json
from urllib import request

def queue_prompt(prompt):
    p = {"prompt": prompt}
    data = json.dumps(p).encode('utf-8')
    req = request.Request("http://127.0.0.1:8188/prompt", data=data)
    request.urlopen(req)
```

That plus a poll loop on `/api/jobs/{prompt_id}` and a `GET /api/view` is the
entire client. `urllib` follows the 302 that Comfy Cloud's `/api/view` returns.
The *only* thing requiring a dependency is the websocket (`websocket-client` in
ComfyUI's own ws example) — and we established in §1 we don't need it.

**Is there an official Python client?** **No.** Comfy Org ships `comfy-cli` (an
install/environment manager, not a workflow client). Everything on PyPI —
`comfy-api-client`, `comfyui-api-client`, `comfy-ui-client`,
`comfy-api-simplified` — is community-maintained, single-author, and none is
blessed by Comfy Org. Depending on one buys us a thin wrapper over ~60 lines of
`urllib` and takes on abandonment risk.

**Verdict: keep it stdlib**, exactly like `PollinationsService`. This is a real,
concrete win — the ComfyUI migration costs us **zero** new dependencies.

---

## 10. Things that will trip us up (the ones nobody asks about)

- **`/prompt` returns immediately.** It queues and hands back a `prompt_id`. Our
  `Service.generate()` is synchronous and returns bytes, so *we* own the wait
  loop, the timeout, and the failure mode when a job never completes. Give it a
  hard timeout; an image that never arrives must raise, not hang a CLI forever.
- **Model provisioning is the real portability problem.** A workflow names its
  checkpoint by *filename* (`"ckpt_name": "sd_xl_base_1.0.safetensors"`). If a
  contributor's file is named differently, `/prompt` 400s with `node_errors`.
  Mitigation: (a) document the exact filename in the repo, (b) pre-flight
  `GET /api/object_info/CheckpointLoaderSimple` and check our pinned name is in
  the enum, failing with a *useful* message ("checkpoint X not installed on
  <server>; available: …") rather than a raw 400.
- **Custom nodes are a portability tarpit.** Any custom node in the workflow must
  be installed on *every* target, local and cloud. **Rule: core nodes only.** This
  also rules out ComfyUI-GGUF and every provider's proprietary "external input"
  nodes.
- **Errors surface in two different places.** *Validation* errors come back
  synchronously as a 400 + `node_errors` on `/prompt`. *Runtime* errors (OOM
  mid-sample, a bad tensor shape) appear only later — as `execution_error` on the
  websocket, or as a `failed` status / `execution_error` field in the job record.
  A polling client **must check the job status**, not merely wait for `outputs` to
  appear; otherwise a failed job looks identical to a slow one until the timeout.
- **Auth on a local server: there is none.** ComfyUI has no built-in
  authentication. `--listen 0.0.0.0` puts an unauthenticated remote-code-execution
  surface (custom nodes execute arbitrary Python) on the LAN. Default bind is
  `127.0.0.1`; keep it there, and put an SSH tunnel or reverse proxy in front if a
  contributor ever wants to share a box. `--enable-cors-header` and TLS flags exist
  but are not auth.
- **Output-file cleanup:** ComfyUI writes every generated image into its own
  `output/` directory *and* returns it via `/view`. Nothing prunes it. Our
  candidates store is separate (ADR 0008), so the server accumulates a duplicate
  of every candidate we ever generated, forever. Either point `--output-directory`
  somewhere disposable, or use a `SaveImage` `filename_prefix` we can sweep. (A
  `PreviewImage`/temp-dir variant would avoid the write entirely but the temp files
  are still on disk.) Worth a line in whatever runbook we write.
- **Cold starts on serverless hosts** (RunPod, Modal, Replicate) are real: the
  container must boot and load a multi-GB checkpoint into VRAM. Comfy Cloud
  sidesteps this by billing only active GPU time with models pre-installed, but I
  found no published cold-start number — see open questions.
- **Concurrency:** a local ComfyUI runs one job at a time from a FIFO queue —
  submitting our N candidate jobs up front is safe and pipelines nicely. Comfy
  Cloud caps concurrent API workflows at **1 / 3 / 5** by tier; excess jobs queue
  (up to 100). So `count=4` on the $20 tier is serialised, not rejected.
- **Seed range mismatch:** our `_SEED_BOUND = 2**31` is far below KSampler's
  `0xffffffffffffffff`. Harmless (a subset is still a valid seed space), but if we
  want the printed `--seed` to round-trip identically into a workflow, keep our own
  bound and don't let anything widen it silently.

---

## How this lands on our `Service` protocol

```python
def generate(self, source: str, count: int, *, seed: int | None = None) -> Sequence[bytes | str]
```

Fits **cleanly**, with one wrinkle:

- `source` (the composed prompt string) → patch into the `CLIPTextEncode` node's
  `inputs.text`, located by `_meta.title`.
- `count` → **N separate `/api/prompt` submissions**, `batch_size: 1` (see §3).
- `seed` → `random.Random(seed)` → N sub-seeds → each patched into that job's
  `KSampler.inputs.seed`. **Identical to the existing `PollinationsService`
  logic** — that code survives verbatim.
- Return `Sequence[bytes]` → the PNG bytes from `/api/view`. Also unchanged.
- Local vs cloud → one config knob (`base_url`, optional `X-API-Key`). Same code
  path. This is the whole payoff.

**Where it chafes:** the protocol has nowhere to put a *workflow*. A ComfyUI
service needs a workflow JSON as well as a prompt string, so it needs construction
parameters (`ComfyUIService(base_url, api_key, workflow_path, checkpoint)`) fed
from `config`. That's fine — `Kind.service` holds an *instance*, so the service can
carry whatever state it likes and `Service` stays a one-method protocol. No change
to `kinds.py`, `spine.py`, or the CLI. Nothing in the ADRs needs revisiting; ADR
0008's amendment (base seed → N sub-seeds) maps onto ComfyUI *better* than it maps
onto Pollinations, because ComfyUI's seed is a genuine, documented sampler input
rather than an opaque provider query param.

---

## Unverified / open questions

Listed honestly; none of these are blockers, but don't quote me on them.

1. **Does `GET /api/job/{prompt_id}/status` exist on a *local* server?** It's
   documented for Comfy Cloud. Local definitely has `/api/jobs/{job_id}` and
   `/history/{prompt_id}`. **Could not confirm** the singular `/api/job/{id}/status`
   route in local `server.py`. → Use `/api/jobs/{id}`, which I *did* verify on
   local, and test it against Cloud before committing to it.
2. **Does Comfy Cloud serve `/api/history/{prompt_id}` and the websocket?** Not
   documented. Assume not; poll `/api/jobs/{id}`.
3. **Can Comfy Cloud run an arbitrary checkpoint of our choosing?** It advertises
   "900+ pre-installed models" and LoRA import on the Creator tier, but I found no
   statement about arbitrary checkpoint upload or custom nodes. **This is the
   single most important thing left to check**, because it's the "two model
   inventories" risk from the bottom line: if Cloud's SDXL file has a different
   `ckpt_name` than our local one, the same workflow JSON does *not* run on both,
   and the seam leaks. Verify by hitting Cloud's `GET /api/object_info/CheckpointLoaderSimple`.
4. **Real-world speed of SDXL on an integrated Xe-LPG iGPU under WSL2.** No primary
   benchmark found. Only adjacent evidence: an open OOM issue on Core Ultra (#9128)
   and the known shared-memory-spill collapse. Needs an experiment, not more reading.
5. **Cross-machine / cross-GPU seed reproducibility.** The noise tensor is stable;
   the sampled *image* almost certainly isn't bit-identical across CUDA/XPU/CPU or
   torch versions. Found no official ComfyUI statement either way.
6. **RunComfy pricing** — their docs pages I fetched cover the API shape, not the
   rates. Not verified.
7. **ComfyDeploy's API shape** — the fetch failed; I did not verify it. Believed
   proprietary REST plus custom external-input nodes, but *unconfirmed*.
8. **fal.ai's "fal format"** — I have it second-hand that arbitrary workflows must
   be converted (input/output nodes, "Save as fal format"). Not confirmed against
   fal's own docs.
9. **Last-updated dates.** docs.comfy.org pages do not publish them, so I can't tell
   you how stale any given page is. All GitHub source quotes are from `master` as of
   **2026-07-14**. This ecosystem moves fast; re-verify §5 (Cloud) before building
   against it — it is the newest and most volatile surface here.
