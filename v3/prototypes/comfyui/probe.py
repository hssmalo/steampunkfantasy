#!/usr/bin/env python3
"""PROTOTYPE — THROWAWAY. Delete once it has answered its question.

Question it answers
-------------------
Can ONE stdlib-only client drive both a local ComfyUI and Comfy Cloud, with
nothing changing but the base URL and an auth header? And is calling a local
ComfyUI "from outside" genuinely free -- no account, no API key, no credits?

Deliberately independent of `spf`: stdlib only, no imports from the project, so
a contributor can run it with a bare `python3` and no checkout of anything else.

Run it
------
    # Local (your friends with GPUs). ComfyUI running on 127.0.0.1:8188.
    python3 prototypes/comfyui/probe.py local

    # Cloud (this machine). Needs a paid tier + key from platform.comfy.org.
    export COMFY_CLOUD_API_KEY=...
    python3 prototypes/comfyui/probe.py cloud

It prints a verdict, drops the PNG files next to itself, and writes
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
# Workflow patching -- by _meta.title, never by numeric node id. The whole
# point: survive someone renumbering the graph in the UI.
# --------------------------------------------------------------------------


def find_node(graph, title):
    hits = [k for k, v in graph.items() if v.get("_meta", {}).get("title") == title]
    if len(hits) != 1:
        raise ProbeError(f"expected exactly 1 node titled {title!r}, found {len(hits)}")
    return hits[0]


def patch(graph, title, **inputs):
    graph[find_node(graph, title)]["inputs"].update(inputs)


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


def phase_inventory(base, api_key, findings, wanted):
    """THE decisive question for cloud: what checkpoints can we actually name?"""
    print("[2] checkpoint inventory  (/api/object_info/CheckpointLoaderSimple)")
    info = request(base, "/api/object_info/CheckpointLoaderSimple", api_key)
    try:
        names = info["CheckpointLoaderSimple"]["input"]["required"]["ckpt_name"][0]
    except (KeyError, IndexError, TypeError) as err:
        raise ProbeError(f"unexpected object_info shape: {err}") from None
    findings["checkpoints"] = names
    print(f"    -> {len(names)} checkpoint(s) available")
    for n in names[:25]:
        print(f"       {n}")
    if len(names) > 25:
        print(f"       ... and {len(names) - 25} more")

    if wanted and wanted not in names:
        raise ProbeError(f"--checkpoint {wanted!r} not on this server")
    chosen = wanted or (names[0] if names else None)
    if not chosen:
        raise ProbeError("server has NO checkpoints installed")
    findings["checkpoint_used"] = chosen
    print(f"    -> using: {chosen}")
    return chosen


def phase_generate(base, api_key, findings, *, checkpoint, prompt, seed, steps):
    graph = json.loads((HERE / "workflow_api.json").read_text())
    patch(graph, "PROTO_CHECKPOINT", ckpt_name=checkpoint)
    patch(graph, "PROTO_POSITIVE", text=prompt)
    patch(graph, "PROTO_SAMPLER", seed=seed, steps=steps)

    print(f"[3] submit  (seed={seed}, steps={steps})")
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
        blob = request(base, f"/api/view?{q}", api_key, raw=True)
        out.append(blob)
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


def main():
    ap = argparse.ArgumentParser(description="Throwaway ComfyUI probe.")
    ap.add_argument("backend", choices=["local", "cloud"])
    ap.add_argument("--base-url", help="override the default base URL")
    ap.add_argument("--api-key", default=os.environ.get("COMFY_CLOUD_API_KEY"))
    ap.add_argument(
        "--checkpoint", help="exact ckpt filename; default = first available"
    )
    ap.add_argument("--prompt", default=DEFAULT_PROMPT)
    ap.add_argument("--seed", type=int, default=12345)
    ap.add_argument("--steps", type=int, default=25)
    ap.add_argument(
        "--twice", action="store_true", help="rerun same seed; is it reproducible?"
    )
    args = ap.parse_args()

    base = args.base_url or (CLOUD_URL if args.backend == "cloud" else LOCAL_URL)
    key = args.api_key if args.backend == "cloud" else None

    findings = {
        "backend": args.backend,
        "base_url": base,
        "when": time.strftime("%Y-%m-%d %H:%M"),
    }
    print(f"=== ComfyUI probe: {args.backend} ===\n")

    try:
        phase_reachable(base, key, findings)
        ckpt = phase_inventory(base, key, findings, args.checkpoint)
        blobs = phase_generate(
            base,
            key,
            findings,
            checkpoint=ckpt,
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
                checkpoint=ckpt,
                prompt=args.prompt,
                seed=args.seed,
                steps=args.steps,
            )
            second = hashlib.sha256(again[0]).hexdigest()[:16]
            same = second == digests[0]
            findings["reproducible_same_seed"] = same
            print(
                f"    -> {digests[0]} vs {second}: {'IDENTICAL' if same else 'DIFFERENT'}"
            )

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
