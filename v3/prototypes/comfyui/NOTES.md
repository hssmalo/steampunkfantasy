# PROTOTYPE — ComfyUI probe (throwaway)

**Delete this whole directory once the verdict below is filled in and folded into
an ADR or issue.** It is not production code, has no tests, and imports nothing
from `spf` on purpose.

## Scope decision (2026-07-15) — read this first

The goal is to **generate images in both environments**, local and cloud. It is
**not** to reproduce anything across them:

- **No cross-environment reproducibility is wanted** — not even approximately. The
  same request may (will) yield different images locally and in the cloud, and
  that is fine.
- **Local and cloud may use different checkpoints** — indeed different *workflows*
  entirely. Each environment names whatever model it has.

So the thing we're building is **one HTTP client** plus **per-environment config**
(`base_url`, optional `api_key`, and *its own* `workflow_path` + model). It is
*not* "one workflow JSON that must run in both places." That reframes two of the
hypotheses below (3 and 4) from load-bearing risks down to don't-cares — see the
status column.

## The question

Can **one** stdlib-only client drive **both** a local ComfyUI and Comfy Cloud,
each pointed at its own workflow + model via config?

And the sub-question that decides whether local is even viable for contributors:
**is calling a local ComfyUI "from outside" genuinely free** — no account, no API
key, no credits?

Background research: [`docs/research/comfyui.md`](../../docs/research/comfyui.md).

## What we expect to find (the hypotheses under test)

| # | Hypothesis | Source | Status |
|---|---|---|---|
| 1 | Local ComfyUI needs **no auth at all** | ComfyUI has no built-in authentication | ✅ confirmed — run B (end-to-end submit + poll + fetch, no key) |
| 2 | Local is **free**: credits only apply to *API Nodes* (hosted models called from inside a workflow), not to the HTTP API itself | `docs/research/comfyui.md` §5 | ✅ confirmed — run A |
| 3 | The **same** HTTP client drives both (each with its **own** workflow); cloud speaks the same `/api/*` surface, differing only by `base_url` + `X-API-Key` | Comfy Cloud docs: "compatible with local ComfyUI's API" | ✅ confirmed — run E (same client + graph generated on Cloud, `base_url`+key the only change) |
| 4 | ~~Cloud exposes a checkpoint we can also install locally~~ **Retired by the scope decision** — different checkpoints per environment is now the design, not a risk. Each workflow need only run on *its own* server. | — | ⬛ n/a |
| 5 | `SaveImage` embeds the recipe in PNG `tEXt` by default, so an asset carries its own recipe | ComfyUI `nodes.py` | ✅ confirmed — run B (`prompt` chunk present) |
| 6 | Same seed → same bytes on the same machine (`--twice`) — *local convenience only, not a cross-environment goal* | inferred, not confirmed | ⬜ untested |

Hypothesis 3 is now about the **client and API surface** being shared, not the
workflow. The probe stays **one script, not two**, because a single client
driving both backends is exactly that shared surface — two scripts would assume
it away. Per-environment *workflows* are expected and supported via `--workflow`.

## Results log

### Run A — local, 2026-07-15, contributor's GPU box

```json
{"works_without_api_key": true, "checkpoints": [], "verdict": "FAILED",
 "error": "server has NO checkpoints installed"}
```

**The headline finding, and it's the one we most wanted: `works_without_api_key:
true`.** A stock local ComfyUI answered an unauthenticated request from a
separate process. No account, no API key, no credits. **Hypothesis 2 is
confirmed** — the paid surface (API Nodes) is opt-in *by node choice inside a
workflow*, not a toll gate on the HTTP API. Driving a local ComfyUI "from
outside" is free.

**Hypothesis 1 is only *partly* confirmed, and the distinction matters.** What we
actually proved is that `GET /api/system_stats` needs no key. The run died before
it ever reached `POST /api/prompt`, so *submission* over an unauthenticated
connection is still strictly unproven. Nothing suggests it will differ (ComfyUI
has no auth layer at all, for any route), but it is not measured. Promote this to
✅ only once a run gets past phase 3.

The `"checkpoints": []` was **almost certainly a false negative from the probe,
not an empty box** — see the correction below. The v1 probe only ever asked
`CheckpointLoaderSimple` what it had.

### Correction — the contributor's real model is Qwen-Image, which has no checkpoint

They exported their working setup (kept as
`prototypes/comfyui/samples/qwen_image_api.json`). It reveals the v1 probe was
**looking in the wrong drawer**:

- Their model is **Qwen-Image**, a *UNET-split* model. It loads via
  `UNETLoader` + `CLIPLoader` + `VAELoader` naming three separate files
  (`qwen_image_2512_fp8_e4m3fn.safetensors`, `qwen_2.5_vl_7b_fp8_scaled.safetensors`,
  `qwen_image_vae.safetensors`). There is **no `CheckpointLoaderSimple` and no
  checkpoint file at all** — so `models/checkpoints/` is legitimately empty while
  the box is fully model-equipped. They likely never needed the SDXL download.
- Their graph uses **`ComfySwitchNode`** (a 4-step-LoRA toggle). That is *not* a
  core node. It runs locally but is the textbook custom-node portability risk:
  the same JSON will fail on Comfy Cloud unless Cloud has that node pack. This is
  exactly what hypothesis 3/4 need to find out.

**What this changed in the probe (v2):** the checkpoint-only inventory check is
replaced by a general **preflight** that asks the server, for *every* node: do
you have this node class, and every model file it names? It detects split-loader
models and unknown/custom nodes alike, and reports the full available list for
each loader input so a local run and a cloud run can be diffed directly. Prompt
and seed are now patched by *following links from the sampler*, so the one script
drives both the built-in graph and any exported one. Verified offline against
both the built-in SDXL graph and the real Qwen export.

**Still worth doing (SDXL as a portable baseline).** The built-in graph uses core
nodes + one checkpoint on purpose: it's the clean test of "same workflow, both
backends." SDXL's *boringly canonical filename* maximises the chance Cloud has
the identical name. It isn't necessarily the model we'd ship (FLUX.1 schnell and
Qwen-Image are Apache-2.0 and cleaner for a game we might sell — see the research
doc); the probe tests plumbing, not art direction.

```bash
# only if you want the portable SDXL baseline; a Qwen box doesn't need it
cd ComfyUI/models/checkpoints
curl -L -O https://huggingface.co/stabilityai/stable-diffusion-xl-base-1.0/resolve/main/sd_xl_base_1.0.safetensors
# ~6.9 GB, then RESTART ComfyUI — it caches the model list
```

**Sequencing note for the next run:** get Cloud's inventory *first*
(`probe.py cloud` prints it even when generation fails), then decide which
workflow to test. The Qwen export is the more revealing cloud test precisely
because of `ComfySwitchNode` — if Cloud rejects it, we've learned the real
portability boundary; if it accepts it, even better.

### Run B — local, 2026-07-16, contributor's GPU box, Qwen export end-to-end

```json
{"works_without_api_key": true, "unknown_node_classes": [],
 "poll_route_that_worked": "/history/{id}", "seconds_to_first_image": 626.6,
 "png_text_keys": ["prompt"], "png_embeds_workflow": true, "verdict": "OK"}
```

The full loop ran against `samples/qwen_image_api.json`: preflight (every node
class + all four model files present, no unknown classes, no combo mismatches) →
`POST /api/prompt` → poll → fetch → a real PNG. **This closes hypothesis 1**: the
run reached and passed `POST /api/prompt` with no API key, so unauthenticated
*submission* — not just `system_stats` — is now measured, not just inferred.

Three findings the design should carry forward:

- **Poll route is bare `/history/{id}`** — not `/api/jobs/{id}` or
  `/api/history/{id}`. Research was unsure; this is the one that answered. The
  real client should try `/history/{id}` first.
- **PNG carries a `prompt` tEXt chunk, no separate `workflow` chunk.** For an
  API-submitted job that is exactly right — the *executable* graph is embedded
  (its recipe), not the UI-layout `workflow` blob a manual Save would add.
  Hypothesis 5 confirmed in the form that matters.
- **`seconds_to_first_image: 626.6` (~10.5 min).** Almost certainly cold-start
  VRAM load of the fp8 Qwen UNET + CLIP + VAE, not steady state — but **unverified**.
  Open question for the next local run: is a *second* generation in the same
  server session dramatically faster? If ~10 min is steady state, local batch
  generation needs rethinking. This is the one number that could still bite us.

Note this export uses `LoraLoaderModelOnly` (a **core** node), not the
`ComfySwitchNode` from the earlier sample — so `unknown_node_classes` is empty and
this graph is more portable than feared. But **local cannot test portability**
(the contributor's server has every node); that remains a cloud-only question for
hypothesis 3.

### Run C — cloud, 2026-07-16, built-in SDXL graph — probe bug, informative

```json
{"backend": "cloud", "works_without_api_key": true, "verdict": "FAILED",
 "error": "HTTP 404 on /api/object_info/CheckpointLoaderSimple -- \"This
           endpoint is not available on Comfy Cloud. Use /api/object_info instead.\""}
```

**Not a Cloud incompatibility — a leftover per-class call in the probe.** Cloud
reached, answered `/api/system_stats`, and returned a *helpful* 404 naming the
supported route. Everything else (including preflight) already used the bulk
`/api/object_info`; only `resolve_builtin_checkpoint` still hit the per-class
`/api/object_info/CheckpointLoaderSimple`. **Fixed** — it now uses bulk
`/api/object_info` (which local supports too, so the probe stays single-client).
Re-run needed.

Two real signals already, though:

- **Cloud speaks the same `/api/*` surface** — same base routes, differing only
  in that it drops the per-node-class `object_info` sub-route and *tells you the
  replacement*. This is exactly the compatibility hypothesis 3 needs; strong
  early sign one client can drive both.
- **`works_without_api_key: true` on Cloud** — `GET /api/system_stats` answered
  with **no** `X-API-Key`. So Cloud's *stats* endpoint is public. Don't overread
  it: submission almost certainly still needs the key (the subsequent authed
  `object_info` call returned 404, not 401, so the key is valid and accepted).
  But flag it — worth confirming on the re-run whether `/api/prompt` rejects an
  unauthenticated submit.

### Run D — cloud, 2026-07-16, built-in SDXL — full client loop works, bad ckpt pick

```json
{"backend": "cloud", "works_without_api_key": true, "unknown_node_classes": [],
 "patched_steps": true, "patched_seed_into": "5", "verdict": "FAILED",
 "error": "job FAILED ... value_not_in_list: ckpt_name
           'dynamicrafter/controlnet/dc_sketch_encoder_fp16.safetensors'"}
```

**This all but closes hypothesis 3.** With the bulk-`object_info` fix, the *same
stdlib client* drove Cloud through every phase: reachable → preflight (81
checkpoints enumerated) → `/api/prompt` **accepted** (job queued) → poll surfaced
the job record → patching applied (`patched_steps`, `patched_seed_into`). The only
failure was on Cloud's *execution* side, and it was our fault, not Cloud's:

- The probe picked `names[0]`, which on Cloud is
  `dynamicrafter/controlnet/dc_sketch_encoder_fp16.safetensors` — a **ControlNet
  encoder, not a base checkpoint**. Cloud *advertises* it in `object_info` but
  rejects it for `CheckpointLoaderSimple` at run time (`value_not_in_list`).
- **Finding worth carrying forward:** on Cloud, **membership in `object_info` ≠
  loadable**. Our preflight marked it `available: true` (it *is* in the list), so
  preflight can't fully vet Cloud checkpoints — only execution can. Local didn't
  show this because a contributor's box only lists what it can actually load.
- **Fixed:** `resolve_builtin_checkpoint` now prefers a real SDXL base
  (`sd_xl_base_1.0.safetensors`, which **is** in Cloud's list), falling back
  through a small known-good list. Re-run needed.

Also confirmed in the inventory: Cloud carries `sd_xl_base_1.0.safetensors`,
`flux1-schnell-fp8.safetensors`, and `flux1-dev-fp8.safetensors` — so our clean
Apache-2.0 candidate (FLUX.1 schnell) is available cloud-side.

### Run E — cloud, 2026-07-16, built-in SDXL — SUCCESS, real image end-to-end

```json
{"backend": "cloud", "works_without_api_key": true, "verdict": "OK",
 "ckpt": "sd_xl_base_1.0.safetensors", "seconds_to_first_image": 10.3,
 "poll_route_that_worked": "/api/jobs/{id}", "png_text_keys": ["prompt"]}
```

**Hypothesis 3 confirmed.** The *same* stdlib client and the *same* built-in graph
that we run locally generated a real SDXL image on Comfy Cloud, with nothing
changed but `base_url` and the `X-API-Key` header. Submit → poll → fetch → PNG,
all green.

Two facts the real client must carry:

- **Poll route differs by backend.** Cloud answered on `/api/jobs/{id}`; local
  answered on `/history/{id}`. Neither backend serves the other's route, so the
  client genuinely needs to try both (the probe's try-all-three poll is not
  over-engineering — it's required).
- **Cloud is the fast path: 10.3 s** for an SDXL image, versus local's ~626 s
  cold-start on the Qwen box. This matches the hardware analysis — the contributor
  with the real GPU is the local case; this machine is the cloud case.

`png_text_keys: ["prompt"]` on Cloud too — the recipe-embedding behaviour (H5) is
identical across both backends.

## Run it

**Local** (contributors with a real GPU). Start ComfyUI first; default bind is
`127.0.0.1:8188`.

```bash
# Built-in portable SDXL graph (needs a checkpoint installed):
python3 prototypes/comfyui/probe.py local
python3 prototypes/comfyui/probe.py local --twice     # also checks reproducibility
python3 prototypes/comfyui/probe.py local --checkpoint sd_xl_base_1.0.safetensors

# Your OWN exported workflow — no download, drives what already works for you.
# In ComfyUI: "Save (API Format)" (NOT plain Save), then:
python3 prototypes/comfyui/probe.py local --workflow my_export.json
```

The probe patches only the positive prompt and seed, following links from the
`KSampler`; everything else (model, steps, cfg, LoRA switches) stays exactly as
you saved it. Pass `--prompt "..."` to change the test prompt.

**Cloud** (needs a paid tier — API access is excluded from the free tier).

```bash
export COMFY_CLOUD_API_KEY=...      # platform.comfy.org/profile/api-keys
python3 prototypes/comfyui/probe.py cloud
```

No dependencies. Stdlib `urllib` + `json` only — if this ever *needs* a
dependency, that itself is a finding about the real implementation.

## What it reports

Each run writes `findings-<backend>.json` next to the script. **Send that file
back** — it captures everything without anyone having to narrate what happened:

- `works_without_api_key` — hypotheses 1 & 2
- `checkpoints` — the full inventory of that server (hypothesis 4: compare the
  local list against the cloud list; **if they share no checkpoint filename, the
  one-workflow-everywhere design leaks**)
- `poll_route_that_worked` — research was genuinely unsure whether it's
  `/api/jobs/{id}`, `/api/history/{id}` or `/history/{id}`; the probe tries all
  three and records which answered
- `seconds_to_first_image` — the practical number for a `count=4` batch
- `png_embeds_workflow` + `png_text_keys` — hypothesis 5
- `reproducible_same_seed` — hypothesis 6, only with `--twice`

It also drops the generated `out-<backend>-N.png` files so you can look at them.

## Known-good plumbing

The client was driven end-to-end against a stub server mimicking ComfyUI's routes
(title-based node patching, submit, poll, fetch, PNG chunk parse all verified).
So a failure against a real server is a finding about *ComfyUI*, not a typo in
the probe — please report it rather than working around it.

## Verdict

_All load-bearing hypotheses settled by runs A–E (2026-07-15/16). Ready to fold
into an ADR/issue and delete this prototype._

- **Is local free and open?** **Yes, proven end-to-end.** A stock local ComfyUI
  answered an unauthenticated request and ran a full generation with no account,
  no API key, no credits (runs A + B). The paid surface (API Nodes) is opt-in *by
  node choice inside a workflow*, not a toll gate on the HTTP API.
- **Does one client serve both?** **Yes (H3 confirmed, run E).** One stdlib-only
  client drove local *and* Cloud through submit → poll → fetch → PNG, changing
  only `base_url` + the `X-API-Key` header. Two backend differences the real
  client must handle:
  1. **Poll route differs** — Cloud `/api/jobs/{id}`, local `/history/{id}`; try
     both.
  2. **Cloud drops the per-class `/api/object_info/{class}` route** (use bulk
     `/api/object_info`, which both support), and on Cloud *object_info
     membership ≠ loadable* — some advertised names 400 at execution. Vet Cloud
     checkpoints by execution, not by the advertised list.
- **Do local and cloud share a checkpoint?** **Don't care — retired by the scope
  decision.** Each environment names its own model. For the record they *could*
  overlap (Cloud carries `sd_xl_base_1.0`, `flux1-schnell-fp8`, `flux1-dev-fp8`),
  but the design does not require it.
- **Performance shape:** Cloud ~10 s/image (SDXL); local ~626 s first image on the
  contributor's Qwen box — almost certainly cold-start VRAM load, **steady-state
  still unmeasured** (the one open number; take a `--twice` local run if it
  matters before shipping).
- **Decision:** **ComfyUI is viable for both environments.** Build one HTTP client
  (stdlib is sufficient — the probe needed no dependency) with per-environment
  config: `base_url`, optional `api_key`, and each environment's own
  `workflow_path` + model. Backend-specific: poll-route fallback, bulk
  object_info only. Model licensing for anything we might ship → **FLUX.1 schnell
  or Qwen-Image (both Apache-2.0)**; avoid FLUX.1 dev (non-commercial) and SD 3.5
  ($1M tripwire) — see `docs/research/comfyui.md`.
