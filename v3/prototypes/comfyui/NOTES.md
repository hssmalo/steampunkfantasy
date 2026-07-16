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
| 1 | Local ComfyUI needs **no auth at all** | ComfyUI has no built-in authentication | 🟡 partly confirmed — run A |
| 2 | Local is **free**: credits only apply to *API Nodes* (hosted models called from inside a workflow), not to the HTTP API itself | `docs/research/comfyui.md` §5 | ✅ confirmed — run A |
| 3 | The **same** HTTP client drives both (each with its **own** workflow); cloud speaks the same `/api/*` surface, differing only by `base_url` + `X-API-Key` | Comfy Cloud docs: "compatible with local ComfyUI's API" | ⬜ untested |
| 4 | ~~Cloud exposes a checkpoint we can also install locally~~ **Retired by the scope decision** — different checkpoints per environment is now the design, not a risk. Each workflow need only run on *its own* server. | — | ⬛ n/a |
| 5 | `SaveImage` embeds the workflow in PNG `tEXt` by default, so an asset carries its own recipe | ComfyUI `nodes.py` | ⬜ untested |
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

> _Fill this in when the runs come back, then delete the prototype._

- **Is local free and open?** …
- **Does one client serve both?** …
- **Do local and cloud share a checkpoint?** …
- **Decision:** …
