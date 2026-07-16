#!/usr/bin/env python3
"""PROTOTYPE — THROWAWAY. Delete once it has answered its question.

Question it answers
-------------------
Can ONE stdlib-only client drive both a local ComfyUI and Comfy Cloud, with
nothing changing but the base URL and an auth header? And is calling a local
ComfyUI "from outside" genuinely free -- no account, no API key, no credits?

Deliberately independent of `spf`: stdlib only, no imports from the project, so
a contributor can run it with a bare `python3` and no checkout of anything else.

Two workflows
-------------
* Built-in (default): a portable SDXL graph using only core nodes -- the fair
  test of "does the SAME workflow run on both local and cloud?"
* `--workflow PATH`: drive ANY exported API-format workflow (ComfyUI ->
  "Save (API Format)"). Use this to run a contributor's real, known-good setup
  -- e.g. a Qwen-Image graph, which is a UNET-split model (UNETLoader +
  CLIPLoader + VAELoader) and has NO checkpoint at all.

Either way, a "preflight" phase asks the server, for every node in the workflow:
do you have this node class, and every model file it names? That is the direct
test of the two risks the research flagged -- "two model inventories" and
"custom nodes aren't portable" -- and it works for split-loader models too.

Run it
------
    # Local, portable SDXL graph (needs a checkpoint installed).
    python3 prototypes/comfyui/probe.py local

    # Local, a contributor's own exported workflow (no download needed).
    python3 prototypes/comfyui/probe.py local --workflow my_qwen_api.json

    # Cloud (this machine). Needs a paid tier + key from platform.comfy.org.
    export COMFY_CLOUD_API_KEY=...
    python3 prototypes/comfyui/probe.py cloud

It prints a verdict, drops the image files next to itself, and writes
`findings-<backend>.json` -- send that file back and it tells us everything we
need without anyone having to narrate what happened.
"""

import argparse
import hashlib
import json
import os
import pathlib
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import uuid

HERE = pathlib.Path(__file__).parent
LOCAL_URL = "http://127.0.0.1:8188"
CLOUD_URL = "https://cloud.comfy.org"

DEFAULT_PROMPT = (
    "steampunk fantasy concept art, a brass-armoured rat soldier with goggles, "
    "gritty painterly illustration, dramatic lighting, muted palette"
)

# A combo input whose value ends in one of these is a model file: if the server
# doesn't have it, the job WILL 400. Combo mismatches on anything else (a
# sampler, a scheduler) are reported but not treated as fatal.
MODEL_EXTS = (".safetensors", ".ckpt", ".pt", ".pth", ".bin", ".gguf", ".sft")

# Samplers we know how to patch a seed into. Enough for the built-in graph and
# the common exported ones; anything else fails loudly rather than silently.
SAMPLER_CLASSES = ("KSampler", "KSamplerAdvanced")

# The built-in graph is SDXL, so prefer a real SDXL base checkpoint. Cloud's
# object_info lists ~80 names including ControlNet encoders and refiners that are
# advertised but NOT loadable via CheckpointLoaderSimple (they 400 at execution
# with value_not_in_list) -- so never just take names[0]. These are ordinary base
# checkpoints, tried in order; falls back to the first advertised name.
PREFERRED_BUILTIN_CKPTS = (
    "sd_xl_base_1.0.safetensors",
    "sd_xl_turbo_1.0_fp16.safetensors",
    "dreamshaper_8.safetensors",
    "v1-5-pruned-emaonly-fp16.safetensors",
)


class ProbeError(Exception):
    """Something we want reported as a finding, not a traceback."""


# --------------------------------------------------------------------------
# HTTP -- stdlib only, on purpose. If this needs a dependency, we've learned
# something important about the real implementation.
# --------------------------------------------------------------------------


def request(base, path, api_key=None, body=None, raw=False, timeout=120):
    url = f"{base}{path}"
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(url, data=data)  # noqa: S310
    if body is not None:
        req.add_header("Content-Type", "application/json")
    if api_key:
        req.add_header("X-API-Key", api_key)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:  # noqa: S310
            payload = resp.read()
            return payload if raw else json.loads(payload)
    except urllib.error.HTTPError as err:
        detail = err.read().decode("utf-8", "replace")[:2000]
        raise ProbeError(f"HTTP {err.code} on {path}\n{detail}") from None
    except urllib.error.URLError as err:
        raise ProbeError(f"cannot reach {url}: {err.reason}") from None


# --------------------------------------------------------------------------
# Graph helpers -- address nodes by class and by FOLLOWING LINKS, never by
# numeric id or fragile title. A link is ["<node_id>", <slot>]; a literal is
# anything else. This is what lets one patcher serve both the built-in SDXL
# graph and an arbitrary exported one.
# --------------------------------------------------------------------------


def nodes_of_class(graph, *classes):
    return [nid for nid, n in graph.items() if n.get("class_type") in classes]


def sole_node_of_class(graph, classes, what):
    hits = nodes_of_class(graph, *classes)
    if len(hits) != 1:
        raise ProbeError(f"expected exactly 1 {what} node, found {len(hits)}: {hits}")
    return hits[0]


def set_scalar_or_upstream(graph, node_id, key, value):
    """Set inputs[key] to value; if it's a link, patch the upstream primitive.

    Returns True if a value was set, False if the input is absent.
    """
    inputs = graph[node_id]["inputs"]
    if key not in inputs:
        return False
    current = inputs[key]
    if isinstance(current, list):  # a link to another node -> patch its value
        up = graph[current[0]]["inputs"]
        for k in ("value", key, "seed", "int", "number"):
            if k in up:
                up[k] = value
                return True
        return False
    inputs[key] = value
    return True


def png_text_keys(data):
    """Which tEXt/iTXt keys does this PNG carry? (Does it embed its own recipe?)"""
    keys, pos = [], 8
    while pos < len(data) - 8:
        length = int.from_bytes(data[pos : pos + 4], "big")
        ctype = data[pos + 4 : pos + 8]
        if ctype in (b"tEXt", b"iTXt", b"zTXt"):
            body = data[pos + 8 : pos + 8 + length]
            keys.append(body.split(b"\x00")[0].decode("latin-1", "replace"))
        if ctype == b"IEND":
            break
        pos += 12 + length
    return keys


# --------------------------------------------------------------------------
# Phases
# --------------------------------------------------------------------------


def phase_reachable(base, api_key, findings):
    print(f"[1] reachable + auth?  {base}")
    # Deliberately called with NO key first: on local this proves the server is
    # open (the "is it free?" question); on cloud it should fail with 401/403.
    try:
        request(base, "/api/system_stats", api_key=None, timeout=20)
        findings["works_without_api_key"] = True
        print("    -> 200 with NO api key. Open server, no auth.")
    except ProbeError as err:
        findings["works_without_api_key"] = False
        findings["unauthenticated_error"] = str(err).split("\n")[0]
        print(f"    -> rejected without a key: {str(err).splitlines()[0]}")
        if not api_key:
            raise ProbeError("needs an API key; set COMFY_CLOUD_API_KEY") from None
        request(base, "/api/system_stats", api_key=api_key, timeout=20)
        print("    -> 200 WITH api key.")


def resolve_builtin_checkpoint(base, api_key, graph, wanted):
    """Pick a checkpoint for the built-in SDXL graph and patch it in.

    The built-in workflow ships a placeholder ckpt_name; a real one has to come
    from whatever the server actually has installed.
    """
    node = sole_node_of_class(graph, ("CheckpointLoaderSimple",), "checkpoint loader")
    # Bulk /api/object_info, not the per-class /api/object_info/{class}: Comfy
    # Cloud 404s the per-class route ("Use /api/object_info instead") while local
    # supports both, so the bulk call keeps this a single-client probe.
    info = request(base, "/api/object_info", api_key)
    spec = info.get("CheckpointLoaderSimple")
    if spec is None:
        raise ProbeError("server has no CheckpointLoaderSimple node")
    names = spec["input"]["required"]["ckpt_name"][0]
    if not names:
        raise ProbeError(
            "server has NO checkpoints installed. Either drop a .safetensors into "
            "models/checkpoints/ and restart, or run with --workflow <your own "
            "exported graph> (e.g. a Qwen/UNET setup, which uses no checkpoint)."
        )
    if wanted and wanted not in names:
        raise ProbeError(f"--checkpoint {wanted!r} not on this server; have: {names}")
    chosen = wanted or next(
        (n for n in PREFERRED_BUILTIN_CKPTS if n in names), names[0]
    )
    graph[node]["inputs"]["ckpt_name"] = chosen
    print(f"    -> built-in graph checkpoint: {chosen}")
    return chosen


def phase_preflight(base, api_key, findings, graph):
    """Ask the server: do you know every node class, and have every model file?

    This is the generalised replacement for the old checkpoint-only check. It's
    the direct measurement of the two portability risks -- and it works for
    split-loader models (UNETLoader/CLIPLoader/VAELoader), not just checkpoints.
    """
    print("[2] preflight  (node classes + model files this server has)")
    info = request(base, "/api/object_info", api_key)

    unknown, models, soft = [], [], []
    for nid, node in graph.items():
        ct = node.get("class_type")
        spec = info.get(ct)
        if spec is None:  # server doesn't have this node class at all
            unknown.append(ct)
            continue
        req = spec.get("input", {}).get("required", {})
        opt = spec.get("input", {}).get("optional", {})
        for iname, ispec in {**req, **opt}.items():
            # A combo input's spec is [[option, option, ...], {props}].
            if not (isinstance(ispec, list) and ispec and isinstance(ispec[0], list)):
                continue
            val = node.get("inputs", {}).get(iname)
            if not isinstance(val, str):  # a link, or a numeric widget
                continue
            entry = {"node": nid, "class": ct, "input": iname, "value": val}
            entry["available"] = val in ispec[0]
            if val.lower().endswith(MODEL_EXTS):
                entry["options_count"] = len(ispec[0])
                models.append(entry)
            elif not entry["available"]:
                entry["options"] = ispec[0][:20]
                soft.append(entry)

    findings["unknown_node_classes"] = sorted(set(unknown))
    findings["required_models"] = models
    findings["combo_mismatches"] = soft
    # The comparison payload: the full available list for every loader input the
    # workflow touches. Diff local-vs-cloud on this to settle hypothesis 4.
    inventory = {}
    for e in models:
        key = f"{e['class']}.{e['input']}"
        if key not in inventory:
            sect = info[e["class"]]["input"]
            opts = sect.get("required", {}).get(e["input"]) or sect.get(
                "optional", {}
            ).get(e["input"])
            inventory[key] = opts[0] if opts else []
    findings["model_inventory"] = inventory

    for e in models:
        mark = "OK " if e["available"] else "MISSING"
        print(f"    [{mark}] {e['class']}.{e['input']} = {e['value']}")
    for ct in findings["unknown_node_classes"]:
        print(f"    [UNKNOWN NODE] {ct}  <- not installed here; not portable")
    for e in soft:
        print(f"    [warn] {e['class']}.{e['input']} = {e['value']} not in options")

    missing = [e for e in models if not e["available"]]
    if unknown or missing:
        raise ProbeError(
            f"workflow not runnable on this server: "
            f"{len(unknown)} unknown node class(es) {sorted(set(unknown))}, "
            f"{len(missing)} missing model file(s) "
            f"{[e['value'] for e in missing]}"
        )
    print("    -> every node class and model file is present.")


def patch_prompt_and_seed(graph, findings, *, prompt, seed, steps):
    """Patch the positive prompt and seed by following links from the sampler.

    Title- and id-independent, so it works on the built-in graph and on an
    arbitrary exported one alike.
    """
    sid = sole_node_of_class(graph, SAMPLER_CLASSES, "sampler")
    inputs = graph[sid]["inputs"]

    seed_key = "seed" if "seed" in inputs else "noise_seed"
    if not set_scalar_or_upstream(graph, sid, seed_key, seed):
        raise ProbeError(f"could not find a seed input on sampler {sid}")

    # steps often comes from a Primitive/switch in real graphs -- only override
    # it when it's an inline literal, otherwise leave the author's wiring alone.
    findings["patched_steps"] = isinstance(
        inputs.get("steps"), int
    ) and set_scalar_or_upstream(graph, sid, "steps", steps)

    pos = inputs.get("positive")
    if not isinstance(pos, list):
        raise ProbeError("sampler's 'positive' input is not a link to a text node")
    text_node = graph[pos[0]]["inputs"]
    if "text" not in text_node:
        raise ProbeError(
            f"positive node {graph[pos[0]]['class_type']} has no 'text' to patch"
        )
    text_node["text"] = prompt
    findings["patched_seed_into"] = sid


def phase_generate(base, api_key, findings, graph, *, prompt, seed, steps):
    graph = json.loads(json.dumps(graph))  # don't mutate the caller's copy
    patch_prompt_and_seed(graph, findings, prompt=prompt, seed=seed, steps=steps)

    print(f"[3] submit  (seed={seed})")
    submitted = time.monotonic()
    resp = request(
        base,
        "/api/prompt",
        api_key,
        body={"prompt": graph, "client_id": str(uuid.uuid4())},
    )
    prompt_id = resp.get("prompt_id")
    if not prompt_id:
        raise ProbeError(f"no prompt_id in response: {resp}")
    print(f"    -> queued, prompt_id={prompt_id}")

    print("[4] poll for completion")
    record, route = poll(base, api_key, prompt_id)
    elapsed = time.monotonic() - submitted
    findings["poll_route_that_worked"] = route
    findings["seconds_to_first_image"] = round(elapsed, 1)
    print(f"    -> done in {elapsed:.1f}s via {route}")

    images = [
        img
        for node in record.get("outputs", {}).values()
        for img in node.get("images", [])
        if img.get("type") != "temp"
    ]
    if not images:
        raise ProbeError(
            f"job finished but produced no images: {record.get('outputs')}"
        )

    print(f"[5] fetch {len(images)} image(s)  (/api/view)")
    out = []
    for img in images:
        q = urllib.parse.urlencode(
            {
                "filename": img["filename"],
                "subfolder": img.get("subfolder", ""),
                "type": img.get("type", "output"),
            }
        )
        out.append(request(base, f"/api/view?{q}", api_key, raw=True))
    return out


def poll(base, api_key, prompt_id, timeout=900):
    """Try the endpoints in the order the research suggested, record what worked.

    Research flagged genuine uncertainty here: /api/jobs/{id} is verified on
    local, /api/job/{id}/status is documented for cloud, /history is the classic.
    Rather than pick one and hope, try each and REPORT which one answered.
    """
    routes = [
        f"/api/jobs/{prompt_id}",
        f"/api/history/{prompt_id}",
        f"/history/{prompt_id}",
    ]
    deadline = time.monotonic() + timeout
    working = None
    while time.monotonic() < deadline:
        for route in routes if working is None else [working]:
            try:
                data = request(base, route, api_key, timeout=30)
            except ProbeError:
                continue
            working = route
            # /history/{id} nests under the prompt_id; /api/jobs/{id} does not.
            record = data.get(prompt_id, data) if isinstance(data, dict) else data
            status = record.get("status")
            state = status.get("status_str") if isinstance(status, dict) else status
            if state in ("failed", "error"):
                raise ProbeError(f"job FAILED: {json.dumps(record)[:1500]}")
            if record.get("outputs") or state == "completed":
                return record, route
        time.sleep(2)
    raise ProbeError(f"timed out after {timeout}s waiting for {prompt_id}")


# --------------------------------------------------------------------------


def load_workflow(path):
    graph = json.loads(pathlib.Path(path).read_text())
    if not isinstance(graph, dict) or not all(
        isinstance(v, dict) and "class_type" in v for v in graph.values()
    ):
        raise ProbeError(
            f"{path} is not an API-format workflow. In ComfyUI use "
            "'Save (API Format)', not the plain 'Save' (that's the UI format)."
        )
    return graph


def main():
    ap = argparse.ArgumentParser(description="Throwaway ComfyUI probe.")
    ap.add_argument("backend", choices=["local", "cloud"])
    ap.add_argument("--base-url", help="override the default base URL")
    ap.add_argument("--api-key", default=os.environ.get("COMFY_CLOUD_API_KEY"))
    ap.add_argument("--workflow", help="an exported API-format workflow to drive")
    ap.add_argument("--checkpoint", help="built-in graph only: exact ckpt filename")
    ap.add_argument("--prompt", default=DEFAULT_PROMPT)
    ap.add_argument("--seed", type=int, default=12345)
    ap.add_argument("--steps", type=int, default=25)
    ap.add_argument(
        "--twice", action="store_true", help="rerun same seed; reproducible?"
    )
    args = ap.parse_args()

    base = args.base_url or (CLOUD_URL if args.backend == "cloud" else LOCAL_URL)
    key = args.api_key if args.backend == "cloud" else None

    findings = {
        "backend": args.backend,
        "base_url": base,
        "when": time.strftime("%Y-%m-%d %H:%M"),
        "workflow": args.workflow or "built-in SDXL",
    }
    print(f"=== ComfyUI probe: {args.backend}  ({findings['workflow']}) ===\n")

    try:
        phase_reachable(base, key, findings)

        if args.workflow:
            graph = load_workflow(args.workflow)
        else:
            graph = json.loads((HERE / "workflow_api.json").read_text())
            resolve_builtin_checkpoint(base, key, graph, args.checkpoint)

        phase_preflight(base, key, findings, graph)

        blobs = phase_generate(
            base,
            key,
            findings,
            graph,
            prompt=args.prompt,
            seed=args.seed,
            steps=args.steps,
        )

        digests = []
        for i, blob in enumerate(blobs, 1):
            path = HERE / f"out-{args.backend}-{i}.png"
            path.write_bytes(blob)
            digests.append(hashlib.sha256(blob).hexdigest()[:16])
            print(f"    -> wrote {path.name}  ({len(blob) // 1024} KB)")

        keys = png_text_keys(blobs[0])
        findings["png_text_keys"] = keys
        findings["png_embeds_workflow"] = bool({"prompt", "workflow"} & set(keys))
        print(f"[6] PNG metadata keys: {keys or '(none)'}")
        print(f"    -> embeds its own recipe: {findings['png_embeds_workflow']}")

        if args.twice:
            print("\n[7] determinism: same seed, second run")
            again = phase_generate(
                base,
                key,
                {},
                graph,
                prompt=args.prompt,
                seed=args.seed,
                steps=args.steps,
            )
            second = hashlib.sha256(again[0]).hexdigest()[:16]
            findings["reproducible_same_seed"] = second == digests[0]
            verdict = "IDENTICAL" if second == digests[0] else "DIFFERENT"
            print(f"    -> {digests[0]} vs {second}: {verdict}")

        findings["verdict"] = "OK"
        print("\n=== VERDICT: this backend works with the shared stdlib client. ===")

    except ProbeError as err:
        findings["verdict"] = "FAILED"
        findings["error"] = str(err)
        print(f"\n!!! FAILED: {err}", file=sys.stderr)
    finally:
        report = HERE / f"findings-{args.backend}.json"
        report.write_text(json.dumps(findings, indent=2))
        print(f"\nWrote {report.name} -- send this back.")

    return 0 if findings.get("verdict") == "OK" else 1


if __name__ == "__main__":
    sys.exit(main())
