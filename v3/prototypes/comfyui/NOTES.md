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
| 1 | Local ComfyUI needs **no auth at all** — `POST /api/prompt` just works | ComfyUI has no built-in authentication | ⬜ untested |
| 2 | Local is **free**: credits only apply to *API Nodes* (hosted models called from inside a workflow), not to the HTTP API itself | `docs/research/comfyui.md` §5 | ⬜ untested |
| 3 | The **same workflow JSON** runs on both, so local vs cloud is just `base_url` + `X-API-Key` | Comfy Cloud docs: "compatible with local ComfyUI's API" | ⬜ untested |
| 4 | **Cloud exposes a checkpoint we can also install locally** — the "two model inventories" risk. *This is the one that can sink the design.* | unverified in research | ⬜ untested |
| 5 | `SaveImage` embeds the workflow in PNG `tEXt` by default, so an asset carries its own recipe | ComfyUI `nodes.py` | ⬜ untested |
| 6 | Same seed → same bytes on the same machine (`--twice`) | inferred, not confirmed | ⬜ untested |

The probe is built as **one script, not two**, precisely because hypothesis 3 is
the thing we're testing — two scripts would assume it away.

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
