# PROTOTYPE — ComfyUI probe (throwaway)

**Delete this whole directory once the verdict below is filled in and folded into
an ADR or issue.** It is not production code, has no tests, and imports nothing
from `spf` on purpose.

## The question

Can **one** stdlib-only client drive **both** a local ComfyUI and Comfy Cloud,
with nothing changing but a base URL and an auth header?

And the sub-question that decides whether local is even viable for contributors:
**is calling a local ComfyUI "from outside" genuinely free** — no account, no API
key, no credits?

Background research: [`docs/research/comfyui.md`](../../docs/research/comfyui.md).

## What we expect to find (the hypotheses under test)

| # | Hypothesis | Source | Status |
|---|---|---|---|
| 1 | Local ComfyUI needs **no auth at all** | ComfyUI has no built-in authentication | 🟡 partly confirmed — run A |
| 2 | Local is **free**: credits only apply to *API Nodes* (hosted models called from inside a workflow), not to the HTTP API itself | `docs/research/comfyui.md` §5 | ✅ confirmed — run A |
| 3 | The **same workflow JSON** runs on both, so local vs cloud is just `base_url` + `X-API-Key` | Comfy Cloud docs: "compatible with local ComfyUI's API" | ⬜ untested |
| 4 | **Cloud exposes a checkpoint we can also install locally** — the "two model inventories" risk. *This is the one that can sink the design.* | unverified in research | ⬜ untested |
| 5 | `SaveImage` embeds the workflow in PNG `tEXt` by default, so an asset carries its own recipe | ComfyUI `nodes.py` | ⬜ untested |
| 6 | Same seed → same bytes on the same machine (`--twice`) | inferred, not confirmed | ⬜ untested |

The probe is built as **one script, not two**, precisely because hypothesis 3 is
the thing we're testing — two scripts would assume it away.

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

The failure itself is not a finding about ComfyUI, it's a finding about *setup*:
**ComfyUI ships with zero models.** It is an execution engine, not a bundle. An
empty `models/checkpoints/` means `CheckpointLoaderSimple` has no name to offer
and the probe correctly refuses to submit a workflow that could only 400.

Fix, before re-running:

```bash
cd ComfyUI/models/checkpoints
curl -L -O https://huggingface.co/stabilityai/stable-diffusion-xl-base-1.0/resolve/main/sd_xl_base_1.0.safetensors
# ~6.9 GB, then RESTART ComfyUI — it caches the model list
```

SDXL is chosen here for its *boringly canonical filename*, not its merits: the
design needs local and cloud to share a checkpoint **filename**, so a standard
name maximises the chance Cloud already has it. It is not necessarily the model
we would ship with (see licensing in the research doc — FLUX.1 schnell and
Qwen-Image are Apache-2.0 and cleaner for a game we might sell). The probe tests
plumbing, not art direction; pick the model later.

**Sequencing note for the next run:** ideally get Cloud's checkpoint inventory
*first* (`probe.py cloud` prints it even if generation fails), then have
contributors download exactly the file Cloud already has, under exactly that
name. That turns hypothesis 4 from a coin-flip into a deliberate choice.

## Run it

**Local** (contributors with a real GPU). Start ComfyUI first; default bind is
`127.0.0.1:8188`, and at least one checkpoint must be installed.

```bash
python3 prototypes/comfyui/probe.py local
python3 prototypes/comfyui/probe.py local --twice     # also checks reproducibility
python3 prototypes/comfyui/probe.py local --checkpoint sd_xl_base_1.0.safetensors
```

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
