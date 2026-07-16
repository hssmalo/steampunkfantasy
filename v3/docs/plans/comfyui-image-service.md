# Implementation plan — ComfyUI-backed Image Asset service

**Status:** ready to implement · **Author of decisions:** grilling session 2026-07-16
**Decision record:** [`docs/adr/0009-comfyui-image-service.md`](../adr/0009-comfyui-image-service.md)
**Background research:** [`docs/research/comfyui.md`](../research/comfyui.md)

Hand this document to a fresh implementation session. Every design fork is
already resolved (see **Decisions** below); the implementer's job is to execute,
test-first, not to re-litigate. Where a fact needs confirming against the live
Cloud server, it is called out as a **pre-implementation step**.

---

## 1. Goal

Replace the flaky Pollinations backend behind the **Image** Asset kind with
**ComfyUI**, driven by one stdlib HTTP client that talks to either a **local
ComfyUI** or **Comfy Cloud**, selected by committed config. The `Service` seam
(`generate(source, count, *, seed=None) -> Sequence[bytes]`) does not change; only
the provider behind it does.

**Scope constraint (fixed, do not widen):** we generate images in *both*
environments, but **cross-environment reproducibility is a non-goal**. Each
environment runs its own workflow against its own models. It is fine — expected —
that the same request yields different images locally and in the cloud. See ADR
0009 and the memory note `comfyui-both-envs-no-repro`.

## 2. Decisions (the design, already settled)

| # | Area | Decision |
|---|---|---|
| 1 | Env config | Named `[assets.image.comfyui.local]` and `[assets.image.comfyui.cloud]` blocks, each with `base_url`, `workflow`, `api_key_env`. |
| 2 | Env selector | The TOML `env` field **only** — no CLI flag, no env-var override. Committed default `env = "local"`. To switch, edit the TOML. |
| 3 | Workflow files | New committed `workflows/` dir. `cloud.json` committed. `local.json` gitignored (per-machine). `local.example.json` committed as a reference. |
| 4 | Patching | Locate nodes by **graph-follow from the sole sampler**. Patch **only** the positive prompt and the seed. Everything else (model, steps, cfg, LoRAs, negative prompt) stays exactly as authored. Fail loudly on 0 or >1 samplers, or if the sampler's positive input is not a text node. |
| 5 | Batch | `count` → **N sequential** `/api/prompt` submissions, `batch_size: 1`, one sub-seed per job. The `random.Random(seed)` → N sub-seeds logic is copied verbatim from `PollinationsService`. No concurrency. |
| 6 | Poll | **Try-both-and-cache**: first poll tries `/api/jobs/{id}` then `/history/{id}`, remembers whichever answered, reuses it for the batch. 2s interval. `timeout_s` from config (default 900). Normalize the two response shapes (`/history/{id}` nests under the prompt_id; `/api/jobs/{id}` does not). |
| 7 | Errors | Retry transient **5xx / connection** failures on submit+poll with exponential backoff (`_MAX_ATTEMPTS=4`, `1/2/4s`). **Fail fast** on 4xx, on a job reaching `failed` status (surface ComfyUI's `node_errors`), on timeout, and on a completed job with no images. Raise `ComfyUIError`. |
| 8 | Layout | New `src/spf/assets/comfyui.py` holds the client + `ComfyUIService`. `src/spf/assets/image.py` slims to wiring (build the service from config, register the Kind). **Delete `PollinationsService`, `_build_url`, `_fetch`.** API key read **lazily at generate time** from the env var *named* by `api_key_env`. |
| 9 | Tests | Monkeypatch a single low-level `_request` seam; no real sockets, stdlib only. Committed fixture graph for patch tests. CLI integration test via the existing `image_env` pattern. Test-first, commit-per-cycle. |
| 10 | Model | **Qwen-Image (Apache-2.0) for both environments.** `cloud.json` content == `local.example.json` content (the friend's Qwen export). No SDXL. If a filename doesn't exactly match Cloud, reconcile by searching Cloud's inventory (plan-B, §4). |

## 3. Files to change

```
configs/spf.toml                         # add comfyui env blocks + env selector
src/spf/schemas/config.py                # ImageAssetConfig + ComfyUI schema; paths.workflows
src/spf/assets/comfyui.py                # NEW: client + ComfyUIService + ComfyUIError
src/spf/assets/image.py                  # slim to wiring; delete Pollinations
src/spf/frontends/cli/assets.py          # broaden one except clause
workflows/cloud.json                     # NEW committed: Qwen export (Cloud-reconciled)
workflows/local.example.json             # NEW committed: same Qwen export, as a reference
.gitignore                               # ignore workflows/local.json
tests/assets/test_comfyui.py             # NEW: client + service unit/flow tests
tests/assets/test_image.py               # rewrite for ComfyUI (drop Pollinations tests)
tests/assets/fixtures/mini_workflow.json # NEW: minimal single-sampler API-format graph
docs/adr/0009-comfyui-image-service.md   # add an amendment (§8)
CONTEXT.md                               # add Environment + Workflow glossary terms (§8)
```

## 4. Pre-implementation step — reconcile the Cloud workflow

The friend's Qwen export names four model files via split loaders:

- `UNETLoader.unet_name` = `qwen_image_2512_fp8_e4m3fn.safetensors`
- `CLIPLoader.clip_name` = `qwen_2.5_vl_7b_fp8_scaled.safetensors`
- `VAELoader.vae_name`   = `qwen_image_vae.safetensors`
- `LoraLoaderModelOnly.lora_name` = `Qwen-Image-2512-Lightning-4steps-V1.0-fp32.safetensors`

The user has confirmed all four exist on Comfy Cloud. Before committing
`cloud.json`, verify the **exact** filenames against Cloud (a `GET
/api/object_info` with the Cloud key, reading each loader input's option list):

- **All four match exactly** → commit the Qwen export unchanged as both
  `workflows/cloud.json` and `workflows/local.example.json`.
- **A filename differs** (Cloud hosts it under a slightly different name) →
  **search Cloud's option list** for that loader input by base-name similarity
  (e.g. a name containing `qwen_image_2512` / `qwen_2.5_vl` / `qwen_image_vae` /
  `Lightning-4steps`), and edit *that one input* in `cloud.json` to Cloud's actual
  filename. This is a **one-time authoring edit** to the committed file — the
  runtime Service never patches model names (Decision 4 holds).

`local.example.json` keeps the original filenames (a local Qwen box uses those).
If the Cloud names diverged, `cloud.json` and `local.example.json` differ only in
those loader inputs; otherwise they are byte-identical.

## 5. Config

### `configs/spf.toml`

```toml
[assets.image]
count = 3

[assets.image.comfyui]
env = "local"          # the ONLY selector; edit to "cloud" to switch
timeout_s = 900        # generous: local cold-start measured ~626s

[assets.image.comfyui.local]
base_url = "http://127.0.0.1:8188"
workflow = "local.json"        # resolved under paths.workflows; gitignored per-machine
api_key_env = ""               # empty ⇒ no auth header

[assets.image.comfyui.cloud]
base_url = "https://cloud.comfy.org"
workflow = "cloud.json"        # resolved under paths.workflows; committed
api_key_env = "SPF_COMFYUI_API_KEY"
```

Add to `[paths]`:

```toml
workflows = "{project_path}/workflows"
```

### `src/spf/schemas/config.py`

- Add `workflows: Path` to `PathsConfig`.
- Add a ComfyUI schema and an image-specific asset config:

```python
class ComfyUIEnvConfig(StrictModel):
    base_url: str
    workflow: str
    api_key_env: str = ""

class ComfyUIConfig(StrictModel):
    env: str = "local"
    timeout_s: int = 900
    local: ComfyUIEnvConfig
    cloud: ComfyUIEnvConfig

class ImageAssetConfig(StrictModel):
    """Image asset settings: count plus the ComfyUI provider config."""
    count: int
    comfyui: ComfyUIConfig
```

- In `AssetsConfig`, change `image` from `AssetKindConfig` to `ImageAssetConfig`.
  `lore` and `model` keep plain `AssetKindConfig` (unchanged).
- Validate `env` ∈ {`local`, `cloud`} — either a Pydantic validator, or let
  `ComfyUIConfig` expose a helper `selected() -> ComfyUIEnvConfig` that raises a
  clear error listing the two names when `env` is neither (mirrors `get_kind`).

## 6. `src/spf/assets/comfyui.py` (new)

Stdlib only (`urllib`, `json`, `random`, `time`, `os`, `uuid`, `pathlib`,
`collections.abc`). No dependency — the probe proved stdlib is sufficient; reaching
for one is itself a signal worth questioning.

### Constants

```python
SAMPLER_CLASSES = ("KSampler", "KSamplerAdvanced")
_MAX_ATTEMPTS = 4         # 1 try + 3 retries (from PollinationsService)
_BACKOFF_BASE = 1.0       # 1s, 2s, 4s
_SERVER_ERROR = 500
_POLL_INTERVAL = 2.0
_SEED_BOUND = 2**31
_POLL_ROUTES = ("/api/jobs/{id}", "/history/{id}")  # try-both order
```

### `ComfyUIError(Exception)`

Raised for anything we want surfaced as a clean CLI message rather than a
traceback: execution `failed` status (carry ComfyUI's `node_errors` text),
timeout, completed-with-no-images, and unpatchable workflows (0/>1 samplers,
non-text positive input). Transient network failures are `urllib` errors
(subclass `OSError`) and are handled by retry, not this.

### `_request(base, path, *, api_key=None, body=None, raw=False, timeout=120)`

The single HTTP seam — **all** network I/O goes through it, so tests monkeypatch
exactly this one function.

- Builds `urllib.request.Request`; JSON-encodes `body` and sets
  `Content-Type: application/json` when present; adds `X-API-Key` when `api_key`.
- On `HTTPError`: **5xx** → retry with backoff up to `_MAX_ATTEMPTS`; **4xx** →
  raise immediately (bad key / bad request are not transient). Surface the response
  body text in the raised error.
- On `URLError` (connection): retry with backoff up to `_MAX_ATTEMPTS`.
- Returns parsed JSON, or raw bytes when `raw=True` (for `/api/view`).

> Retry lives *inside* `_request` so both submit and poll get it for free, exactly
> mirroring how `PollinationsService._fetch` wrapped retries around its GET.

### Graph helpers (ported from the probe, title-independent)

- `_load_workflow(path) -> dict` — read + parse; assert it is API-format (a dict of
  nodes each having `class_type`); else raise `ComfyUIError` telling the user to
  "Save (API Format)", not plain Save.
- `_nodes_of_class(graph, *classes)`, `_sole_node_of_class(graph, classes, what)` —
  the latter raises `ComfyUIError` unless exactly one match.
- `_set_scalar_or_upstream(graph, node_id, key, value) -> bool` — set
  `inputs[key]`; if it is a link `["<id>", slot]`, follow it and set the upstream
  primitive's value (`value`/`key`/`seed`/`int`/`number`). Returns whether it set.
- `_patch_prompt_and_seed(graph, *, prompt, seed)`:
  1. `sid = _sole_node_of_class(graph, SAMPLER_CLASSES, "sampler")`.
  2. seed key = `"seed"` if present else `"noise_seed"`; patch via
     `_set_scalar_or_upstream`; raise if neither.
  3. Follow the sampler's `positive` link to the text node; raise `ComfyUIError`
     if `positive` is not a link or the target has no `text` input; set
     `text = prompt`.
  4. **Do not touch** steps, cfg, model, negative, or anything else.

### Submit / poll / fetch

- `_submit(base, api_key, graph) -> prompt_id` — POST `/api/prompt` with
  `{"prompt": graph, "client_id": uuid4()}`; raise `ComfyUIError` if the response
  has no `prompt_id`.
- `_poll(base, api_key, prompt_id, *, timeout_s, cached_route) -> (record, route)`:
  - Loop until `timeout_s`. On each pass try `cached_route` if known, else each of
    `_POLL_ROUTES` in order. First route that returns 200 becomes the cached route.
  - Normalize: `record = data.get(prompt_id, data)`.
  - If `record`'s status is `failed`/`error` → raise `ComfyUIError` with the
    `node_errors`/record text.
  - If `record` has `outputs` or status `completed` → return `(record, route)`.
  - Sleep `_POLL_INTERVAL`. On timeout → raise `ComfyUIError("timed out …")`.
- `_fetch_images(base, api_key, record) -> list[bytes]` — collect non-`temp`
  images from `record["outputs"]`, GET each via
  `/api/view?filename=…&subfolder=…&type=…` with `raw=True`. Raise `ComfyUIError`
  if the completed job produced no images.

### `ComfyUIService`

```python
class ComfyUIService:
    def __init__(self, *, base_url, workflow_path, api_key_env, timeout_s):
        # store config; do NOT read the secret yet
    def generate(self, source, count, *, seed=None) -> Sequence[bytes]:
        graph = _load_workflow(self._workflow_path)          # once
        api_key = os.environ.get(self._api_key_env) or None  # lazy, at call time
        rng = random.Random(seed)                            # verbatim from Pollinations
        sub_seeds = [rng.randrange(_SEED_BOUND) for _ in range(count)]
        cached_route = None
        blobs = []
        for s in sub_seeds:
            g = json.loads(json.dumps(graph))                # per-job copy
            _patch_prompt_and_seed(g, prompt=source, seed=s)
            prompt_id = _submit(self._base_url, api_key, g)
            record, cached_route = _poll(
                self._base_url, api_key, prompt_id,
                timeout_s=self._timeout_s, cached_route=cached_route,
            )
            blobs.extend(_fetch_images(self._base_url, api_key, record))
        return blobs
```

Notes: sequential (Decision 5); the poll route is discovered once and cached for
the rest of the batch (Decision 6); the key is resolved per `generate` call so it
can be exported after import (Decision 8). One `SaveImage` per job → one blob per
sub-seed; if a workflow's `SaveImage` emits several, they all flow back in order —
harmless.

## 7. `image.py`, CLI, and workflow files

### `src/spf/assets/image.py` (slimmed)

- Delete `PollinationsService`, `_build_url`, `_fetch`, and all Pollinations
  constants/docstring.
- Build the service from config and register the Kind:

```python
from spf.assets.comfyui import ComfyUIService
from spf.config import config

def _build_service() -> ComfyUIService:
    cu = config.assets.image.comfyui
    env = cu.selected()          # ComfyUIEnvConfig for cu.env; raises on bad env
    return ComfyUIService(
        base_url=env.base_url,
        workflow_path=config.paths.workflows / env.workflow,
        api_key_env=env.api_key_env,
        timeout_s=cu.timeout_s,
    )

IMAGE = register_kind(Kind(
    name="image", service=_build_service(),
    subdir="images", extension="png",
))
```

Keep the module import-safe: constructing the service must not touch the network
or read the workflow file (both happen in `generate`). A missing/invalid `env`
should raise at import with a clear message — acceptable, since it's a config typo.

### `src/spf/frontends/cli/assets.py`

One-line change: broaden the image command's failure catch (currently `except
OSError` around the `generate(...)` call, ~line 127) to:

```python
except (OSError, ComfyUIError) as err:
    stderr.print(f"[red]Error:[/] image generation failed: {err}")
    raise SystemExit(1) from None
```

Import `ComfyUIError` from `spf.assets.comfyui`. Nothing else in the CLI changes —
prompt composition, seed resolution/printing, and the promote hint all stand.

### `workflows/` + `.gitignore`

- Commit `workflows/cloud.json` (Cloud-reconciled Qwen export, §4).
- Commit `workflows/local.example.json` (original Qwen export). Add a one-line
  header comment path or a sibling `workflows/README.md` telling local
  contributors: "copy `local.example.json` to `local.json` if you run this exact
  Qwen setup, or drop your own ComfyUI 'Save (API Format)' export at
  `local.json`."
- Add to `.gitignore`: `workflows/local.json`.

## 8. Docs

- **ADR-0009 amendment** (append a dated `## Amendment` section): record the
  concrete choices this plan locks in — TOML-only `env` selector (default
  `local`), named env blocks, the `workflows/` layout (committed cloud + example,
  gitignored per-machine local), and **Qwen-Image (Apache-2.0) for both
  environments** with filename reconciliation for Cloud. Note this supersedes the
  ADR's earlier "prefer FLUX.1 schnell / SDXL" framing for the *shipped* choice
  while staying consistent with its licensing guidance (Qwen is Apache-2.0).
- **CONTEXT.md glossary** — add two terms:
  - **Environment** — a configured ComfyUI target (`local` or `cloud`) the Image
    Service submits to, selected by `assets.image.comfyui.env`. Not to be confused
    with a shell environment.
  - **Workflow** — a ComfyUI API-format graph (JSON) naming the nodes and models a
    generation runs; per-Environment, committed for cloud and per-machine for
    local. _Avoid_: pipeline, graph (in user-facing text).

## 9. Test plan (test-first, commit-per-cycle)

New `tests/assets/test_comfyui.py`, driving everything through a monkeypatched
`comfyui._request`. Suggested cycles:

1. **Sub-seed derivation** — `generate(count=3, seed=42)` twice is identical and
   yields 3 distinct sub-seeds (port the surviving Pollinations test).
2. **Graph-follow patching** — with `fixtures/mini_workflow.json`, assert the
   prompt lands on the positive text node and the seed on the sampler; assert a
   linked-seed primitive is followed; assert `ComfyUIError` on 0 samplers, on 2
   samplers, and on a non-text positive input.
3. **Happy path flow** — scripted `_request` returns a `prompt_id` on
   `/api/prompt`, a completed record on the first poll route, and PNG bytes on
   `/api/view`; assert N blobs returned in order and `batch_size`/seed patched per
   job.
4. **Poll try-both-and-cache** — first route 404s, second returns completed;
   assert the second is used and *reused* on the next job without re-trying the
   first.
5. **Retry vs fail-fast** — a 500-then-200 sequence succeeds (retry); a 400 raises
   immediately; a `failed` status raises `ComfyUIError` carrying `node_errors`; a
   completed-but-empty `outputs` raises; a never-completing poll hits `timeout_s`
   (inject a tiny timeout) and raises.
6. **Lazy key** — `api_key_env` set/unset controls whether `X-API-Key` is sent;
   key read at `generate` time, not construction.

Rewrite `tests/assets/test_image.py`: drop Pollinations URL/fetch tests; keep a
Kind-registration test and add an env-selection test (`env=cloud` builds a service
pointed at the cloud block; a bad `env` raises). Extend the CLI test
(`tests/assets/test_cli.py` or the `image_env` fixture) to point config at a
ComfyUI env with a monkeypatched `_request`, assert candidates are written, and
assert a `failed` job surfaces as a red exit-1.

Keep `just check` green throughout (ruff ALL, pyright, typos, pytest). Note that
the `prototypes/**` ruff/typos ignores were removed with the prototype — this is
production code held to the full ruleset, so: real docstrings, type annotations,
no bare prints, `noqa: S311` on the seed RNG (as Pollinations had).

## 10. Sequencing

1. Pre-implementation Cloud reconciliation (§4) → produce `cloud.json`.
2. Config schema + `configs/spf.toml` + `paths.workflows` (+ a schema test).
3. `comfyui.py` built test-first (cycles 1–6), one commit per green cycle.
4. Slim `image.py` + wire the Kind; rewrite `test_image.py`.
5. CLI one-line broaden + CLI test.
6. Commit `workflows/` files + `.gitignore`.
7. Docs: ADR amendment + CONTEXT.md.
8. Final `just check`; open the PR.

Work in a dedicated worktree per the repo workflow
([`docs/agents/workflow.md`](../agents/workflow.md)); squash-merge later.

## 11. Out of scope / explicitly not now

- **Concurrency** for higher Cloud tiers (Decision 5 — YAGNI).
- **Title-marker patching** escape hatch (Decision 4 — only if a multi-sampler
  graph ever needs it).
- **Preflight / findings / PNG-metadata reading** — probe diagnostics, not needed
  in production. ComfyUI validates on submit and returns `node_errors`.
- **A shared `ServiceError` base** in `kinds.py` — deferred until Lore/Model
  services need it (Decision 7).
- **Rendering embedding the Image**, and anything past a committed Asset — out of
  scope since ADR 0006.

## 12. Acceptance criteria

- `spf assets image <race>` with `env = "local"` and a local ComfyUI running
  writes `count` candidate PNG files, patching only prompt + seed into
  `local.json`.
- Flipping `env = "cloud"` (TOML edit) + exporting `SPF_COMFYUI_API_KEY` generates
  the same way against Comfy Cloud via `cloud.json`, no other change.
- A ComfyUI execution failure prints a clear `[red]Error:[/] …` with ComfyUI's
  message and exits 1; a transient 5xx is retried and can still succeed.
- `PollinationsService` and its helpers/tests are gone; no `SPF_POLLINATIONS_*`
  references remain.
- `just check` is green.
